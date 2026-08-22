import fitz  # PyMuPDF
from PIL import Image
import io
from typing import List, Tuple, Dict, Any
import os

class DocumentPage:
    def __init__(self, page_number: int, text: str, image_bytes: bytes, is_scanned: bool):
        self.page_number = page_number
        self.text = text
        self.image_bytes = image_bytes
        self.is_scanned = is_scanned

class DocumentLoader:
    """
    Ingest PDFs (digital or scanned) and Image files (.jpg, .png, .jpeg).
    Extracts native text when present or renders high-DPI page images for OCR.
    """
    
    @classmethod
    def load_document(cls, file_bytes: bytes, filename: str) -> List[DocumentPage]:
        ext = os.path.splitext(filename)[1].lower()
        pages: List[DocumentPage] = []
        
        if ext in ['.pdf']:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for i, page in enumerate(doc):
                native_text = page.get_text("text").strip()
                
                # Determine if page is scanned (less than 50 chars of native text)
                is_scanned = len(native_text) < 50
                
                img_bytes = b""
                if is_scanned:
                    # Render scanned page to image at 200 DPI for fast high-accuracy OCR
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                
                pages.append(DocumentPage(
                    page_number=i + 1,
                    text=native_text,
                    image_bytes=img_bytes,
                    is_scanned=is_scanned
                ))
            doc.close()
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff']:
            # Single image file (e.g. mobile photo of passbook)
            pages.append(DocumentPage(
                page_number=1,
                text="",
                image_bytes=file_bytes,
                is_scanned=True
            ))
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
        return pages
