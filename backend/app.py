from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io
import json
import os
import re

from ratio.models.schemas import ExtractionResult, StatementMetadata, Transaction, ValidationSummary, RevalidateRequest
from ratio.core.document_loader import DocumentLoader
from ratio.core.ocr_engine import OCREngine
from ratio.core.parser_router import ParserRouter
from ratio.core.validation_engine import ValidationEngine
from ratio.core.excel_generator import ExcelGenerator
from ratio.core.tally_exporter import TallyExporter

app = FastAPI(title="Ratio Financial Extraction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser_router = ParserRouter()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Ratio Financial Intelligence Engine", "version": "1.0.0"}

@app.post("/api/process", response_model=ExtractionResult)
async def process_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    try:
        contents = await file.read()
        pages = DocumentLoader.load_document(contents, file.filename)
        
        all_lines = []
        for page in pages:
            lines = OCREngine.extract_lines(page)
            all_lines.extend(lines)
            
        metadata, transactions = parser_router.parse_document(file.filename, pages, all_lines)
        
        # Process Capital Gains if document is a Capital Gains / Mutual Fund Statement
        capital_gains_data = None
        if metadata.document_type in ["CAPITAL_GAINS", "MUTUAL_FUND"]:
            from ratio.core.capital_gains_parser import CapitalGainsParser
            capital_gains_data = CapitalGainsParser.parse_capital_gains(all_lines)
            metadata.document_type = "CAPITAL_GAINS"
        
        # Run Mathematical Validation & Gap / Missing Page Detector
        validated_transactions, validation_summary = ValidationEngine.validate_statement(transactions, metadata.document_type)
        
        logs = [
            f"Successfully processed {len(pages)} page(s).",
            f"Detected document type: {metadata.institution}.",
            f"Parsed {len(validated_transactions)} transactions.",
            f"Capital Gains STCG: ₹{capital_gains_data.total_stcg if capital_gains_data else 0.0:,.2f}, LTCG: ₹{capital_gains_data.total_ltcg if capital_gains_data else 0.0:,.2f}"
        ]
        
        return ExtractionResult(
            metadata=metadata,
            transactions=validated_transactions,
            capital_gains=capital_gains_data,
            validation=validation_summary,
            logs=logs
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/revalidate", response_model=ExtractionResult)
async def revalidate_transactions(req: RevalidateRequest):
    try:
        validated_transactions, validation_summary = ValidationEngine.validate_statement(
            req.transactions, req.metadata.document_type
        )
        logs = [
            "Re-validated statement after user inline edits.",
            f"Total rows: {validation_summary.total_rows}, Valid: {validation_summary.valid_rows}, Gaps: {len(validation_summary.gaps)}"
        ]
        
        return ExtractionResult(
            metadata=req.metadata,
            transactions=validated_transactions,
            capital_gains=req.capital_gains,
            validation=validation_summary,
            logs=logs
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Revalidation failed: {str(e)}")

@app.post("/api/export/excel")
async def export_excel(data: ExtractionResult):
    try:
        raw_stem = os.path.splitext(data.metadata.source_file)[0] if data.metadata.source_file else data.metadata.institution
        clean_stem = re.sub(r'[^\w\-]', '_', raw_stem)
        clean_stem = re.sub(r'_+', '_', clean_stem).strip('_')
        filename = f"{clean_stem}_Ratio_Audit.xlsx"
        
        if data.capital_gains and data.capital_gains.items:
            excel_bytes = ExcelGenerator.generate_capital_gains_workbook(data.metadata, data.capital_gains)
        else:
            excel_bytes = ExcelGenerator.generate_workbook(data.metadata, data.transactions, data.validation)
        
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@app.post("/api/export/tally")
async def export_tally(data: ExtractionResult):
    try:
        raw_stem = os.path.splitext(data.metadata.source_file)[0] if data.metadata.source_file else data.metadata.institution
        clean_stem = re.sub(r'[^\w\-]', '_', raw_stem)
        clean_stem = re.sub(r'_+', '_', clean_stem).strip('_')
        filename = f"{clean_stem}_Tally_Vouchers.xml"
        
        xml_content = TallyExporter.generate_xml(data.metadata, data.transactions)
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tally XML generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
