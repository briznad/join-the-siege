from typing import List, Optional, Dict, Any
from .base import BaseExtractor, ExtractedContent
import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
import io
import re
from ...exceptions.classification import ExtractionError
import logging

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    @property
    def supported_mimes(self) -> List[str]:
        return ['application/pdf']

    def extract_content(self, file_path: str) -> ExtractedContent:
        try:
            with open(file_path, 'rb') as file:
                # Try text extraction with PyPDF2 first
                text, metadata = self._extract_with_pypdf2(file)

                # If text extraction yields poor results, try pdfplumber
                if not text or self._needs_ocr(text):
                    text, tables = self._extract_with_pdfplumber(file_path)

                    # If still poor results, try OCR
                    if self._needs_ocr(text):
                        text = self._extract_with_ocr(file_path)
                else:
                    tables = []

                # Extract headers and footers
                headers, footers = self._extract_headers_footers(file_path)

                # Calculate confidence
                confidence = self._calculate_confidence(text)

                return ExtractedContent(
                    text=self._clean_text(text),
                    metadata=metadata,
                    tables=tables,
                    headers=headers,
                    footers=footers,
                    page_count=metadata.get('page_count'),
                    language=self._detect_language(text),
                    confidence=confidence
                )

        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}", exc_info=True)
            raise ExtractionError(f"Failed to extract PDF content: {str(e)}")

    def validate_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as file:
                PyPDF2.PdfReader(file)
            return True
        except Exception:
            return False

    def _extract_with_pypdf2(self, file) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata using PyPDF2."""
        pdf = PyPDF2.PdfReader(file)

        # Extract text
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

        # Extract metadata
        metadata = {
            'page_count': len(pdf.pages),
            'encrypted': pdf.is_encrypted,
            'author': pdf.metadata.get('/Author', ''),
            'creator': pdf.metadata.get('/Creator', ''),
            'producer': pdf.metadata.get('/Producer', ''),
            'subject': pdf.metadata.get('/Subject', ''),
            'title': pdf.metadata.get('/Title', ''),
            'creation_date': pdf.metadata.get('/CreationDate', ''),
            'modification_date': pdf.metadata.get('/ModDate', '')
        }

        return text, metadata

    def _extract_with_pdfplumber(self, file_path: str) -> tuple[str, List[List[str]]]:
        """Extract text and tables using pdfplumber."""
        with pdfplumber.open(file_path) as pdf:
            text = ""
            tables = []

            for page in pdf.pages:
                text += page.extract_text() or ""
                tables.extend(page.extract_tables())

        return text, tables

    def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Convert page to image
                img = page.to_image()
                # Perform OCR
                text += pytesseract.image_to_string(img.original) + "\n"
        return text

    def _extract_headers_footers(self, file_path: str) -> tuple[List[str], List[str]]:
        """Extract headers and footers from PDF."""
        headers = []
        footers = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Define header and footer regions
                header_bbox = (0, 0, page.width, page.height * 0.1)
                footer_bbox = (0, page.height * 0.9, page.width, page.height)

                # Extract text from regions
                header = page.crop(header_bbox).extract_text() or ""
                footer = page.crop(footer_bbox).extract_text() or ""

                if header: headers.append(header)
                if footer: footers.append(footer)

        return headers, footers

    def _needs_ocr(self, text: str) -> bool:
        """Determine if OCR is needed based on text quality."""
        if not text:
            return True

        # Check if text contains mainly special characters or whitespace
        alphanumeric_ratio = sum(c.isalnum() for c in text) / len(text)
        return alphanumeric_ratio < 0.1
