import os
import unittest
from ratio.core.document_loader import DocumentLoader
from ratio.core.ocr_engine import OCREngine
from ratio.core.parser_router import ParserRouter
from ratio.core.validation_engine import ValidationEngine
from ratio.core.excel_generator import ExcelGenerator
from ratio.core.tally_exporter import TallyExporter

class TestEndToEndPipeline(unittest.TestCase):

    def test_complete_statement_processing(self):
        pdf_path = "/home/aditya/Heart/test_data/sample_sbi_complete.pdf"
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

        pages = DocumentLoader.load_document(file_bytes, "sample_sbi_complete.pdf")
        self.assertEqual(len(pages), 3)

        all_lines = []
        for p in pages:
            lines = OCREngine.extract_lines(p)
            all_lines.extend(lines)

        router = ParserRouter()
        metadata, trxs = router.parse_document("sample_sbi_complete.pdf", pages, all_lines)
        self.assertEqual(metadata.institution, "State Bank of India")

        validated_trxs, summary = ValidationEngine.validate_statement(trxs)
        self.assertFalse(summary.has_gaps)
        self.assertGreaterEqual(summary.valid_rows, 1)

        # Verify Excel generation
        excel_bytes = ExcelGenerator.generate_workbook(metadata, validated_trxs, summary)
        self.assertGreater(len(excel_bytes), 1000)

        # Verify Tally XML generation
        xml_str = TallyExporter.generate_xml(metadata, validated_trxs)
        self.assertIn("ENVELOPE", xml_str)

    def test_missing_page_detection_e2e(self):
        pdf_path = "/home/aditya/Heart/test_data/sample_sbi_missing_page.pdf"
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

        pages = DocumentLoader.load_document(file_bytes, "sample_sbi_missing_page.pdf")
        all_lines = []
        for p in pages:
            all_lines.extend(OCREngine.extract_lines(p))

        router = ParserRouter()
        metadata, trxs = router.parse_document("sample_sbi_missing_page.pdf", pages, all_lines)

        validated_trxs, summary = ValidationEngine.validate_statement(trxs)
        
        # Must detect missing page gap!
        self.assertTrue(summary.has_gaps)
        self.assertGreater(len(summary.gaps), 0)
        self.assertIn("Missing transactions detected", summary.gaps[0].message)

        # Verify Excel includes missing page gap callout
        excel_bytes = ExcelGenerator.generate_workbook(metadata, validated_trxs, summary)
        self.assertGreater(len(excel_bytes), 1000)

if __name__ == '__main__':
    unittest.main()
