from typing import List, Optional
from .base import BaseExtractor, ExtractedContent
from PIL import Image
import pytesseract
import cv2
import numpy as np
from ..exceptions.extraction_exceptions import ExtractionError
import logging

logger = logging.getLogger(__name__)

class ImageExtractor(BaseExtractor):
    @property
    def supported_mimes(self) -> List[str]:
        return [
            'image/jpeg',
            'image/png',
            'image/tiff',
            'image/bmp'
        ]

    def extract_content(self, file_path: str) -> ExtractedContent:
        try:
            # Read image using OpenCV
            image = cv2.imread(file_path)
            if image is None:
                raise ExtractionError("Failed to read image file")

            # Preprocess image
            preprocessed = self._preprocess_image(image)
            
            # Perform OCR
            text = pytesseract.image_to_string(preprocessed)
            
            # Get additional data
            data = pytesseract.image_to_data(preprocessed, output_type=pytesseract.Output.DICT)
            
            # Detect tables
            tables = self._detect_tables(preprocessed)
            
            # Get confidence scores
            confidence_scores = [float(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Get image metadata
            with Image.open(file_path) as img:
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'dpi': img.info.get('dpi'),
                    'has_tables': bool(tables),
                    'ocr_confidence': avg_confidence
                }

            return ExtractedContent(
                text=self._clean_text(text),
                metadata=metadata,
                tables=tables,
                images=[open(file_path, 'rb').read()],
                language=self._detect_language(text),
                confidence=avg_confidence / 100
            )

        except Exception as e:
            logger.error(f"Image extraction error: {str(e)}", exc_info=True)
            raise ExtractionError(f"Failed to extract image content: {str(e)}")

    def validate_file(self, file_path: str) -> bool:
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Remove noise
            denoised = cv2.medianBlur(thresh, 3)
            
            # Deskew
            angle = self._get_skew_angle(denoised)
            if abs(angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h),
                                        flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)
            
            return denoised

        except Exception as e:
            logger.warning(f"Image preprocessing error: {str(e)}")
            return image

    def _get_skew_angle(self, image: np.ndarray) -> float:
        """Detect skew angle of text in image."""
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
            
            if lines is not None:
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = np.degrees(theta)
                    if angle < 45:
                        angles.append(angle)
                    elif angle > 135:
                        angles.append(angle - 180)
                
                if angles:
                    return np.median(angles)
            
            return 0.0

        except Exception as e:
            logger.warning(f"Skew detection error: {str(e)}")
            return 0.0

    def _detect_tables(self, image: np.ndarray) -> List[List[str]]:
        """Detect and extract tables from image."""
        try:
            # Use pytesseract to detect tables
            tables_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Group text by lines and blocks
            tables = []
            current_table = []
            current_row = []
            last_block_num = -1
            
            for i in range(len(tables_data['text'])):
                if tables_data['text'][i].strip():
                    if tables_data['block_num'][i] != last_block_num:
                        if current_row:
                            current_table.append(current_row)
                            current_row = []
                        if current_table:
                            if len(current_table) > 1:  # Minimum table size
                                tables.append(current_table)
                            current_table = []
                    
                    current_row.append(tables_data['text'][i])
                    last_block_num = tables_data['block_num'][i]
            
            # Add last row and table if they exist
            if current_row:
                current_table.append(current_row)
            if current_table and len(current_table) > 1:
                tables.append(current_table)
            
            return tables

        except Exception as e:
            logger.warning(f"Table detection error: {str(e)}")
            return []
