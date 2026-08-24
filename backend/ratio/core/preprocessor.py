import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple

_rapid_layout_engine = None

def _get_layout_engine():
    global _rapid_layout_engine
    if _rapid_layout_engine is None:
        try:
            from rapid_layout import RapidLayout
            _rapid_layout_engine = RapidLayout(conf_threshold=0.4)
        except Exception as e:
            print("RapidLayout init warning:", e)
    return _rapid_layout_engine

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
        
        # 1. Upscale low-resolution images
        h, w = img.shape[:2]
        max_dim = max(h, w)
        if max_dim < 1500:
            scale = 1500 / max_dim
            # Limit scale to at most 3x to avoid huge memory usage
            scale = min(scale, 3.0)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            metadata["upscaled"] = True
            metadata["scale_factor"] = scale
        
        # 2. 3D Perspective Unwarping for angled passbook photos
        unwarped_img, quad_found = cls.unwarp_perspective_quad(img)
        if quad_found:
            img = unwarped_img
            metadata["perspective_unwarped"] = True

        # 2.2 RapidLayout Table Region Cropping
        layout_engine = _get_layout_engine()
        if layout_engine is not None:
            try:
                boxes, _, _ = layout_engine(img) if callable(layout_engine) else ([], None, None)
                if boxes:
                    table_boxes = [b for b in boxes if 'table' in str(b).lower() or (isinstance(b, (list, tuple, np.ndarray)) and len(b) >= 4)]
                    if table_boxes:
                        best_table = max(table_boxes, key=lambda b: (float(b[2])-float(b[0]))*(float(b[3])-float(b[1])))
                        x1, y1, x2, y2 = int(best_table[0]), int(best_table[1]), int(best_table[2]), int(best_table[3])
                        cur_h, cur_w = img.shape[:2]
                        if (x2 - x1) * (y2 - y1) > 0.35 * (cur_h * cur_w):
                            img = img[max(0, y1-10):min(cur_h, y2+10), max(0, x1-10):min(cur_w, x2+10)]
                            metadata["layout_cropped"] = True
            except Exception as ex:
                pass
            
        # 3. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2.5 Illumination / Shadow Removal
        # Create a heavily blurred version of the image to act as the background/illumination map
        bg_blur = cv2.GaussianBlur(gray, (101, 101), 0)
        # Divide original grayscale by background to flatten lighting
        flat_gray = cv2.divide(gray, bg_blur, scale=255)
        
        # 3. Contrast adjustment (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(flat_gray)
        
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
        
        # 6. Table Grid Detection & Erasing (Turn lines into pure white space)
        # Inverted binary image for morphological operations (text/lines are white, background black)
        inverted = cv2.bitwise_not(binary)
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        detect_horizontal = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        detect_vertical = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Combine detected lines and erase them from the binary image (turn them white)
        table_lines = cv2.add(detect_horizontal, detect_vertical)
        
        # Dilate slightly to ensure the entire line thickness is covered
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        table_lines = cv2.dilate(table_lines, dilate_kernel, iterations=1)
        
        binary[table_lines > 0] = 255
        
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

    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]      # top-left
        rect[2] = pts[np.argmax(s)]      # bottom-right
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]   # top-right
        rect[3] = pts[np.argmax(diff)]   # bottom-left
        return rect

    @classmethod
    def unwarp_perspective_quad(cls, img: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Detects 4-corner document boundaries and applies perspective transform."""
        h, w = img.shape[:2]
        if h < 200 or w < 200:
            return img, False
            
        # Downscale copy for fast contour detection
        ratio = h / 500.0
        small_h = 500
        small_w = int(w / ratio)
        if small_w < 10 or small_h < 10:
            return img, False
            
        small = cv2.resize(img, (small_w, small_h))
        
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if len(small.shape) == 3 else small
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)
        
        cnts, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        
        doc_cnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(c) > (0.35 * (small_h * small_w)):
                doc_cnt = approx
                break
                
        if doc_cnt is None:
            return img, False
            
        pts = doc_cnt.reshape(4, 2) * ratio
        rect = cls.order_points(pts)
        tl, tr, br, bl = rect
        
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))
        
        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))
        
        if max_width < 100 or max_height < 100:
            return img, False
            
        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (max_width, max_height))
        return warped, True
