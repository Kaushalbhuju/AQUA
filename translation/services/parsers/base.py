"""
Document Parser Layer - Document-specific extraction strategies.
Sits between text extraction and translation.

Architecture:
  Document → Extractor → Parser → Structured Data → Template Engine → Japanese Output
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseDocumentParser(ABC):
    """
    Abstract base class for document-specific parsers.
    
    Each document type should have its own parser that:
    1. Extracts structured fields from raw text
    2. Preserves table data if present
    3. Returns clean structured data for template engine
    """
    
    SUPPORTED_DOCUMENT_TYPES = []  # List of document type names this parser handles
    
    @abstractmethod
    def parse(self, extracted_text, layout_data=None, tables=None):
        """
        Parse extracted text into structured data.
        
        Args:
            extracted_text (str): Raw extracted text from OCR/PDF
            layout_data (dict, optional): Layout information with positions
            tables (list, optional): Extracted tables as list of lists
            
        Returns:
            dict: Structured data with fields specific to document type
                  Example: {'student_name': '...', 'school_name': '...', ...}
        """
        pass
    
    @abstractmethod
    def get_document_type(self):
        """Return document type name(s) this parser handles."""
        pass
    
    def can_parse(self, document_type_name):
        """Check if this parser can handle the given document type."""
        return document_type_name in self.SUPPORTED_DOCUMENT_TYPES
    
    def validate_fields(self, data):
        """
        Validate extracted fields.
        Override in subclasses for document-specific validation.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        if not data:
            return False, ['No data provided']
        return True, []


class StructuredDataResult:
    """Container for parsed document data."""
    
    def __init__(self, fields, tables=None, metadata=None):
        """
        Args:
            fields (dict): Extracted structured fields
            tables (list, optional): Table data if document contains tables
            metadata (dict, optional): Additional metadata (confidence, parsing notes, etc.)
        """
        self.fields = fields or {}
        self.tables = tables or []
        self.metadata = metadata or {}
        self.has_tables = len(self.tables) > 0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'fields': self.fields,
            'tables': self.tables,
            'metadata': self.metadata,
            'has_tables': self.has_tables,
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        return cls(
            fields=data.get('fields', {}),
            tables=data.get('tables', []),
            metadata=data.get('metadata', {}),
        )
