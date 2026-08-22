import os
import unittest
from ratio.core.document_loader import DocumentLoader
from ratio.core.ocr_engine import OCREngine
from ratio.core.parser_router import ParserRouter
from ratio.core.validation_engine import ValidationEngine

class TestUserDataPrivacy(unittest.TestCase):

    def test_process_user_files(self):
        test_dir = "/home/aditya/Heart/test_data"
        user_files = [f for f in os.listdir(test_dir) if f.endswith(".pdf") and not f.startswith("sample_sbi")]
        
        router = ParserRouter()
        for filename in user_files:
            file_path = os.path.join(test_dir, filename)
            with open(file_path, "rb") as f:
                file_bytes = f.read()
                
            pages = DocumentLoader.load_document(file_bytes, filename)
            lines = []
            for p in pages:
                lines.extend(OCREngine.extract_lines(p))
                
            meta, trxs = router.parse_document(filename, pages, lines)
            validated, summary = ValidationEngine.validate_statement(trxs)
            
            # Print only non-sensitive summary counts
            print(f"[PRIVACY SAFE TEST] File: {filename} -> Type: {meta.institution}, Pages: {meta.total_pages}, Extracted Trxs: {len(trxs)}, Gaps: {len(summary.gaps)}")
            self.assertGreaterEqual(meta.total_pages, 1)

if __name__ == '__main__':
    unittest.main()
