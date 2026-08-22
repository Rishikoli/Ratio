import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple

class ImagePreprocessor:
    """
    OpenCV image preprocessing pipeline for passbook scans and mobile phone photos.
    Includes deskewing, noise reduction, contrast enhancement, and adaptive binarization.
    """
    
    @staticmethod
    def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image bytes with OpenCV")
        return img

    @staticmethod
    def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
        if len(cv2_img.shape) == 2:
            return Image.fromarray(cv2_img)
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_img)

    @classmethod
    def preprocess_image(cls, image_bytes: bytes, deskew: bool = True) -> Tuple[bytes, dict]:
        """
        Runs full pre-processing pipeline on input image bytes.
        Returns processed image bytes (PNG) and metadata about transformations applied.
        """
        img = cls.bytes_to_cv2(image_bytes)
        metadata = {"original_shape": img.shape}
        
        # 1. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Contrast adjustment (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 3. Deskewing
        angle = 0.0
        if deskew:
            angle = cls.calculate_skew_angle(enhanced)
            if abs(angle) > 0.5 and abs(angle) < 45.0:
                enhanced = cls.rotate_image(enhanced, angle)
                metadata["deskew_angle"] = angle
        
        # 4. Denoising
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # 5. Adaptive Binarization for crisp text OCR
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
        )
        
        # Encode back to PNG bytes
        _, buffer = cv2.imencode('.png', binary)
        processed_bytes = buffer.tobytes()
        
        metadata["processed_shape"] = binary.shape
        return processed_bytes, metadata

    @staticmethod
    def calculate_skew_angle(gray_img: np.ndarray) -> float:
        """Calculates text line skew angle using Hough Transform or minimum area rectangle."""
        edges = cv2.Canny(gray_img, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
        
        if lines is None or len(lines) == 0:
            return 0.0
            
        angles = []
        for line in lines:
            coords = line[0] if len(line.shape) > 1 else line
            if len(coords) == 4:
                x1, y1, x2, y2 = coords
                if x2 - x1 == 0:
                    continue
                angle = np.arctan2(y2 - y1, x2 - x1) * (180.0 / np.pi)
                if -45 < angle < 45:
                    angles.append(angle)
                
        if not angles:
            return 0.0
        return float(np.median(angles))

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
