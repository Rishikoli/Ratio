import re
import io
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple, Optional
from ratio.core.document_loader import DocumentPage
from ratio.core.preprocessor import ImagePreprocessor

class TextLine:
    def __init__(self, text: str, page_number: int, confidence: float = 1.0, bbox: Optional[Tuple[float, float, float, float]] = None):
        self.text = OCREngine.normalize_banking_text(text.strip())
        self.page_number = page_number
        self.confidence = confidence
        self.bbox = bbox

class OCREngine:
    """
    OCR & Text Extraction engine powered by PyMuPDF and RapidOCR.
    Uses native PDF text layer when reliable, and RapidOCR neural engine for scanned images & passbook photos.
    """
    
    _rapid_ocr = None

    @staticmethod
    def normalize_banking_text(text: str) -> str:
        if not text:
            return text
            
        replacements = [
            (r'\bN\s+E\s+F\s+T\b', 'NEFT'),
            (r'\bR\s+T\s+G\s+S\b', 'RTGS'),
            (r'\bU\s+P\s+I\b', 'UPI'),
            (r'\bI\s+M\s+P\s+S\b', 'IMPS'),
            (r'\bA\s+T\s+M\b', 'ATM'),
            (r'\bC\s+H\s+Q\b', 'CHQ'),
            (r'\bP\s+O\s+S\b', 'POS'),
            (r'\bRT6S\b', 'RTGS'),
            (r'\b[l1]MPS\b', 'IMPS'),
            (r'\bNIFT\b', 'NEFT'),
            (r'\bUP1\b', 'UPI'),
            (r'\bC/R\b', 'CR'),
            (r'\bD/R\b', 'DR'),
            (r'\bCr\.\b', 'CR'),
            (r'\bDr\.\b', 'DR')
        ]
        
        normalized = text
        for pattern, repl in replacements:
            normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)
            
        return normalized

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
                    total_height = 0
                    for item in result:
                        box, txt, conf = item[0], item[1], float(item[2])
                        x_top = float(box[0][0])
                        y_top = float(box[0][1])
                        # Calculate box height (bottom-left y - top-left y)
                        height = abs(float(box[3][1]) - float(box[0][1]))
                        total_height += height
                        line_items.append((y_top, x_top, txt, conf))
                        
                    avg_height = total_height / len(result) if result else 30
                    y_threshold = max(5, 0.5 * avg_height)
                        
                    # Sort vertically by Y top coordinate
                    line_items.sort(key=lambda item: item[0])
                    
                    current_line = []
                    current_y = None
                    
                    for y_top, x_top, txt, conf in line_items:
                        if current_y is None or abs(y_top - current_y) < y_threshold:
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

    @classmethod
    def extract_lines_batch(cls, pages: List[DocumentPage]) -> List[TextLine]:
        """Extracts text lines from multiple pages in parallel using a ThreadPoolExecutor."""
        if not pages:
            return []
            
        if len(pages) == 1:
            return cls.extract_lines(pages[0])
            
        import concurrent.futures
        
        all_lines: List[TextLine] = []
        max_workers = min(4, len(pages))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(cls.extract_lines, page): page.page_number for page in pages}
            results = {}
            for future in concurrent.futures.as_completed(futures):
                page_num = futures[future]
                try:
                    results[page_num] = future.result()
                except Exception as e:
                    print(f"Error extracting lines on page {page_num}: {e}")
                    results[page_num] = []
                    
        # Flatten lines ordered by page number
        for page_num in sorted(results.keys()):
            all_lines.extend(results[page_num])
            
        return all_lines
