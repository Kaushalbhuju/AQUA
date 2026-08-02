"""
Parser Registry - Maps document types to their parsers.

Usage:
    from translation.services.parsers.registry import get_parser_for_document
    
    parser = get_parser_for_document('Character Certificate')
    result = parser.parse(extracted_text, layout_data, tables)
"""
import logging
from translation.services.parsers.base import BaseDocumentParser
from translation.services.parsers.character_certificate import CharacterCertificateParser

logger = logging.getLogger(__name__)

# Registry mapping document type names to parser classes
PARSER_REGISTRY = {
    'Character Certificate': CharacterCertificateParser,
    # Future parsers will be added here:
    # 'Transcript': TranscriptParser,
    # 'Bank Statement': BankStatementParser,
    # 'Bank Balance Certificate': BankBalanceParser,
    # 'Academic Certificate': AcademicCertificateParser,
    # etc.
}


def get_parser_for_document(document_type_name):
    """
    Get the appropriate parser for a document type.
    
    Args:
        document_type_name (str): Name of document type (e.g., 'Character Certificate')
        
    Returns:
        BaseDocumentParser: Instance of appropriate parser
                           Falls back to BaseParser if no specific parser exists
    """
    parser_cls = PARSER_REGISTRY.get(document_type_name)
    
    if parser_cls:
        logger.info(f"Using parser: {parser_cls.__name__} for '{document_type_name}'")
        return parser_cls()
    else:
        logger.debug(f"No specific parser for '{document_type_name}', using base parser")
        return BaseParser()


def register_parser(document_type_name, parser_class):
    """
    Register a new parser for a document type.
    
    Args:
        document_type_name (str): Document type name
        parser_class (class): Parser class (must inherit from BaseDocumentParser)
    """
    if not issubclass(parser_class, BaseDocumentParser):
        raise ValueError(f"Parser class must inherit from BaseDocumentParser")
    
    PARSER_REGISTRY[document_type_name] = parser_class
    logger.info(f"Registered parser {parser_class.__name__} for '{document_type_name}'")


def list_registered_parsers():
    """List all registered parsers."""
    return {
        doc_type: parser_class.__name__
        for doc_type, parser_class in PARSER_REGISTRY.items()
    }


class BaseParser(BaseDocumentParser):
    """
    Fallback parser for document types without specific parsers.
    Returns raw text as-is (no structured extraction).
    """
    
    SUPPORTED_DOCUMENT_TYPES = []  # Handles all unspecified types
    
    def parse(self, extracted_text, layout_data=None, tables=None):
        """Return text as-is with minimal processing."""
        from translation.services.parsers.base import StructuredDataResult
        
        return StructuredDataResult(
            fields={
                'raw_text': extracted_text,
                'text_length': len(extracted_text) if extracted_text else 0,
            },
            tables=tables or [],
            metadata={
                'parser': 'BaseParser',
                'note': 'No specific parser for this document type',
            }
        )
    
    def get_document_type(self):
        return ['All unspecified document types']
