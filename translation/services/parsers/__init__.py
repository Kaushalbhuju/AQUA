"""
Translation Document Parsers.

Provides document-specific parsing strategies for structured data extraction.

Architecture:
  Document → Extractor → Parser → StructuredDataResult → Template Engine → Output

Usage:
    from translation.services.parsers import get_parser_for_document
    
    parser = get_parser_for_document('Character Certificate')
    result = parser.parse(extracted_text, tables=tables)
    
    # Access structured data
    student_name = result.fields.get('student_name')
    school_name = result.fields.get('school_name')
"""

from translation.services.parsers.base import BaseDocumentParser, StructuredDataResult
from translation.services.parsers.character_certificate import CharacterCertificateParser
from translation.services.parsers.registry import (
    get_parser_for_document,
    register_parser,
    list_registered_parsers,
    PARSER_REGISTRY,
)

__all__ = [
    'BaseDocumentParser',
    'StructuredDataResult',
    'CharacterCertificateParser',
    'get_parser_for_document',
    'register_parser',
    'list_registered_parsers',
    'PARSER_REGISTRY',
]
