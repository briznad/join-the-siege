from typing import Optional, Dict, Type, List
from .extractors.registry import ExtractorRegistry
from .strategies.base import BaseIndustryStrategy
from .models.document import Document
from .extractors.base import ExtractedContent
from .extractors.pdf import PDFExtractor
from .extractors.image import ImageExtractor
from .extractors.office import WordExtractor, ExcelExtractor
from ..exceptions.classification import ClassificationError
from ..utils.file_utils import FileManager
import hashlib
import os
import logging
import magic
from prometheus_client import Summary, Counter, Histogram


logger = logging.getLogger(__name__)

# Metrics
CLASSIFICATION_TIME = Summary('document_classification_seconds', 'Time spent classifying documents')
DOCUMENTS_PROCESSED = Counter('documents_processed_total', 'Total number of documents processed', ['industry', 'document_type'])
CLASSIFICATION_CONFIDENCE = Histogram('classification_confidence', 'Classification confidence scores', ['industry', 'document_type'])

class DocumentClassifier:
    def __init__(self):
        self.registry = ExtractorRegistry()

        # Register specific file extractors
        self.registry.register(PDFExtractor)
        self.registry.register(ImageExtractor)
        self.registry.register(WordExtractor)
        self.registry.register(ExcelExtractor)

        self.strategies: Dict[str, BaseIndustryStrategy] = {}
        self._register_strategies()
        self.file_manager = FileManager(
            upload_dir='uploads',
            allowed_extensions={'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'tiff', 'xls', 'xlsx'},
            max_file_size=10 * 1024 * 1024  # 10MB
        )
        self._mime = magic.Magic(mime=True)

    def _register_strategies(self):
        """Register all available industry strategies."""
        from .strategies.financial import FinancialIndustryStrategy
        from .strategies.healthcare import HealthcareIndustryStrategy

        strategies: List[Type[BaseIndustryStrategy]] = [
            FinancialIndustryStrategy,
            HealthcareIndustryStrategy
        ]

        for strategy_class in strategies:
            strategy = strategy_class()
            self.strategies[strategy.industry_name] = strategy
            logger.info(f"Registered {strategy.industry_name} industry strategy")

    @CLASSIFICATION_TIME.time()
    def classify(
        self,
        file_path: str,
        industry: Optional[str] = None,
        return_extracted_text: bool = False
    ) -> Document:
        """
        Classify a document, optionally within a specific industry context.
        If no industry is specified, tries all registered strategies.
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise ClassificationError(f"File not found: {file_path}")

            # Get file metadata
            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_file_hash(file_path)

            # Get mime type from file content
            mime_type = self._mime.from_file(file_path)

            # Get appropriate extractor and extract content
            extractor = self.registry.get_extractor(file_path)
            content = extractor.extract_content(file_path)

            # Enhance classification with format-specific features
            enhancement = self._enhance_classification(content)

            if industry:
                if industry not in self.strategies:
                    raise ClassificationError(f"Unknown industry: {industry}")
                result = self._classify_with_strategy(
                    self.strategies[industry],
                    content,
                    enhancement
                )
            else:
                result = self._classify_generic(content, enhancement)

            # Record metrics
            DOCUMENTS_PROCESSED.labels(
                industry=industry or 'unknown',
                document_type=result['document_type']
            ).inc()

            CLASSIFICATION_CONFIDENCE.labels(
                industry=industry or 'unknown',
                document_type=result['document_type']
            ).observe(result['confidence_score'])

            # Create document instance
            document = Document(
                file_path=file_path,
                document_type=result['document_type'],
                confidence_score=result['confidence_score'],
                mime_type=mime_type,
                file_size=file_size,
                file_hash=file_hash,
                industry=industry,
                extracted_text=content.text if return_extracted_text else None,
                metadata={
                    **content.metadata,
                    **enhancement,
                    'classification_method': result['method']
                },
                tables=content.tables,
                headers=content.headers,
                footers=content.footers
            )

            logger.info(
                "Document classified successfully",
                extra={
                    'document_type': document.document_type,
                    'confidence_score': document.confidence_score,
                    'industry': document.industry,
                    'file_size': document.file_size
                }
            )

            return document

        except Exception as e:
            logger.error(f"Classification error: {str(e)}", exc_info=True)
            raise ClassificationError(f"Error classifying document: {str(e)}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file contents."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _enhance_classification(self, content: ExtractedContent) -> dict:
        """Extract format-specific features to enhance classification."""
        enhancement = {
            'content_length': len(content.text),
            'has_tables': bool(content.tables),
            'has_headers': bool(content.headers),
            'has_footers': bool(content.footers),
        }

        if content.tables:
            enhancement.update({
                'table_count': len(content.tables),
                'table_patterns': self._analyze_table_patterns(content.tables)
            })

        if content.headers or content.footers:
            enhancement.update({
                'header_patterns': self._analyze_headers(content.headers),
                'footer_patterns': self._analyze_footers(content.footers)
            })

        return enhancement

    def _classify_with_strategy(
        self,
        strategy: BaseIndustryStrategy,
        content: ExtractedContent,
        enhancement: dict
    ) -> dict:
        """Classify document using a specific industry strategy."""
        result = strategy.classify(content.text, enhancement)

        if result['document_type'] == 'unknown' and content.tables:
            # Try classification based on table patterns
            table_result = self._classify_from_tables(
                content.tables,
                strategy
            )
            if table_result['confidence_score'] > result['confidence_score']:
                result = table_result

        return result

    def _classify_generic(
        self,
        content: ExtractedContent,
        enhancement: dict
    ) -> dict:
        """Classify document without industry context."""
        best_result = None
        best_score = 0

        # Try all strategies
        for strategy in self.strategies.values():
            result = self._classify_with_strategy(
                strategy,
                content,
                enhancement
            )
            if result['confidence_score'] > best_score:
                best_score = result['confidence_score']
                best_result = result

        return best_result or {
            'document_type': "unknown",
            'confidence_score': 0.0,
            'method': 'none'
        }

    def _analyze_table_patterns(self, tables: List[List[str]]) -> dict:
        """Analyze table structures for common patterns."""
        return {
            'financial_table': self._count_financial_tables(tables),
            'list_table': self._count_list_tables(tables),
            'form_table': self._count_form_tables(tables),
            'header_row_count': self._count_header_rows(tables)
        }

    def _analyze_headers(self, headers: List[str]) -> dict:
        """Analyze headers for common patterns."""
        patterns = {
            'date_pattern': 0,
            'logo_reference': 0,
            'letterhead': 0,
            'page_number': 0
        }

        if not headers:
            return patterns

        header_text = ' '.join(headers).lower()

        if any(word in header_text for word in ['page', 'of']):
            patterns['page_number'] += 1

        if any(word in header_text for word in ['logo', 'brand', 'trademark']):
            patterns['logo_reference'] += 1

        if any(word in header_text for word in ['confidential', 'draft', 'final']):
            patterns['letterhead'] += 1

        if any(word in header_text for word in ['date:', 'dated:', 'as of']):
            patterns['date_pattern'] += 1

        return patterns

    def _analyze_footers(self, footers: List[str]) -> dict:
        """Analyze footers for common patterns."""
        patterns = {
            'page_number': 0,
            'copyright': 0,
            'contact_info': 0,
            'disclaimer': 0
        }

        if not footers:
            return patterns

        footer_text = ' '.join(footers).lower()

        if any(word in footer_text for word in ['page', 'of']):
            patterns['page_number'] += 1

        if any(word in footer_text for word in ['copyright', '©', 'all rights reserved']):
            patterns['copyright'] += 1

        if any(word in footer_text for word in ['tel:', 'phone:', 'email:', 'www.', 'http']):
            patterns['contact_info'] += 1

        if any(word in footer_text for word in ['confidential', 'disclaimer', 'privacy']):
            patterns['disclaimer'] += 1

        return patterns

    def _count_financial_tables(self, tables: List[List[str]]) -> int:
        """Count tables that appear to contain financial data."""
        count = 0
        for table in tables:
            numeric_cols = 0
            financial_keywords = ['amount', 'total', 'balance', 'price']

            for row in table:
                if any(str(cell).replace('.', '').isdigit() for cell in row):
                    numeric_cols += 1
                if any(keyword in str(cell).lower() for cell in row
                      for keyword in financial_keywords):
                    count += 1
                    break
        return count

    def _count_list_tables(self, tables: List[List[str]]) -> int:
        """Count tables that appear to be lists."""
        return sum(1 for table in tables if len(table[0]) == 1)

    def _count_form_tables(self, tables: List[List[str]]) -> int:
        """Count tables that appear to be forms."""
        return sum(
            1 for table in tables
            if len(table[0]) == 2 and all(not str(row[0]).isdigit() for row in table)
        )

    def _count_header_rows(self, tables: List[List[str]]) -> int:
        """Count likely header rows in tables."""
        header_count = 0
        for table in tables:
            if not table:
                continue
            first_row = [str(cell).lower() for cell in table[0]]
            if any(word in cell for cell in first_row
                  for word in ['total', 'sum', 'amount', 'date', 'description']):
                header_count += 1
        return header_count

    def _classify_from_tables(
        self,
        tables: List[List[str]],
        strategy: BaseIndustryStrategy
    ) -> dict:
        """Attempt classification based on table patterns."""
        table_text = ' '.join(
            ' '.join(str(cell) for cell in row)
            for table in tables
            for row in table
        )

        result = strategy.classify(table_text)
        if result['document_type'] != 'unknown':
            result['method'] = 'table_analysis'

        return result
