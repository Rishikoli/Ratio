import re
import io
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple, Optional
from ratio.core.document_loader import DocumentPage
from ratio.core.preprocessor import ImagePreprocessor

class TextLine:
    def __init__(self, text: str, page_number: int, confidence: float = 1.0, bbox: Optional[Tuple[float, float, float, float]] = None):
        self.text = text.strip()
        self.page_number = page_number
        self.confidence = confidence
        self.bbox = bbox

class OCREngine:
    """
    OCR & Text Extraction engine powered by PyMuPDF and RapidOCR.
    Uses native PDF text layer when reliable, and RapidOCR neural engine for scanned images & passbook photos.
    """
    
    _rapid_ocr = None

    @classmethod
    def _get_ocr(cls):
        if cls._rapid_ocr is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                cls._rapid_ocr = RapidOCR()
            except Exception as e:
                print("RapidOCR init warning:", e)
        return cls._rapid_ocr

    @classmethod
    def extract_lines(cls, page: DocumentPage) -> List[TextLine]:
        lines: List[TextLine] = []
        
        # 1. Native Digital Text Extraction
        if not page.is_scanned and page.text and len(page.text.strip()) > 50:
            raw_lines = page.text.split('\n')
            for line in raw_lines:
                cleaned = line.strip()
                if cleaned:
                    lines.append(TextLine(text=cleaned, page_number=page.page_number, confidence=1.0))
            return lines
            
        # 2. Neural OCR Engine (RapidOCR) for Scanned Pages / Passbook Photos
        try:
            engine = cls._get_ocr()
            if engine is not None and page.image_bytes:
                # Preprocess image for high contrast OCR
                proc_bytes, _ = ImagePreprocessor.preprocess_image(page.image_bytes)
                
                img = Image.open(io.BytesIO(proc_bytes)).convert("RGB")
                img_np = np.array(img)
                
                result, _ = engine(img_np)
                if result:
                    line_items = []
                    for item in result:
                        box, txt, conf = item[0], item[1], float(item[2])
                        x_top = float(box[0][0])
                        y_top = float(box[0][1])
                        line_items.append((y_top, x_top, txt, conf))
                        
                    # Sort vertically by Y top coordinate
                    line_items.sort(key=lambda item: item[0])
                    
                    current_line = []
                    current_y = None
                    
                    for y_top, x_top, txt, conf in line_items:
                        if current_y is None or abs(y_top - current_y) < 15:
                            current_line.append((x_top, txt, conf))
                            if current_y is None:
                                current_y = y_top
                        else:
                            current_line.sort(key=lambda x: x[0])
                            line_str = "  ".join(x[1] for x in current_line)
                            avg_conf = sum(x[2] for x in current_line) / len(current_line)
                            lines.append(TextLine(text=line_str, page_number=page.page_number, confidence=avg_conf))
                            
                            current_line = [(x_top, txt, conf)]
                            current_y = y_top
                            
                    if current_line:
                        current_line.sort(key=lambda x: x[0])
                        line_str = "  ".join(x[1] for x in current_line)
                        avg_conf = sum(x[2] for x in current_line) / len(current_line)
                        lines.append(TextLine(text=line_str, page_number=page.page_number, confidence=avg_conf))
        except Exception as ex:
            print("RapidOCR processing exception:", ex)
            
        # 3. Fallback to native text layer if present
        if not lines and page.text:
            for line in page.text.split('\n'):
                cleaned = line.strip()
                if cleaned:
                    lines.append(TextLine(text=cleaned, page_number=page.page_number, confidence=0.85))
                        
        return lines
