"""
Document type detection service.
Uses keyword matching to auto-detect document types from extracted text.
"""
import logging
from translation.models import DocumentType

logger = logging.getLogger(__name__)


# Default keywords for each document type
DEFAULT_DOCUMENT_TYPES = {
    'Character Certificate': [
        'character certificate', 'certificate of character', 'character',
        'this is to certify', 'school leaving certificate', 'conduct certificate',
        'certificate', 'national examinations board',
    ],
    'Academic Certificate': [
        'academic certificate', 'certificate of completion', 'degree certificate',
        'diploma', 'bachelor', 'master', 'graduation certificate',
    ],
    'Transcript': [
        'transcript', 'grade sheet', 'marks sheet', 'academic record',
        'marks obtained', 'grade point', 'gpa', 'semester', 'credit',
    ],
    'Bank Balance Certificate': [
        'bank balance certificate', 'balance certificate', 'bank balance',
        'certificate of balance', 'account balance certificate', 'balance confirmation',
    ],
    'Bank Statement': [
        'bank statement', 'account statement', 'transaction history',
        'statement of account', 'transaction details', 'debit', 'credit',
    ],
    'SOP': [
        'statement of purpose', 'sop', 'personal statement',
        'purpose of study', 'motivation letter', 'study abroad',
    ],
    'Sponsor Letter': [
        'sponsor letter', 'sponsorship letter', 'financial sponsor',
        'letter of sponsorship', 'financial support letter', 'undertake',
    ],
    'Way of Payment': [
        'way of payment', 'payment method', 'payment plan',
        'mode of payment', 'financial plan', 'fund transfer',
    ],
    'Early Admission Request': [
        'early admission', 'admission letter', 'letter of admission',
        'acceptance letter', 'offer of admission', 'early entry',
    ],
    'Early Japanese Language Certificate': [
        'japanese language', 'nihongo', 'jlpt', 'japanese proficiency',
        'language certificate', 'japanese certificate', 'japanese course',
    ],
    'Late Issue of NEB Certificate': [
        'late issue', 'delay in issuance', 'late certificate',
        'delayed certificate', 'late issuance', 'duplicate certificate',
        're-issue', 'replacement certificate',
    ],
    'VDC/Ward Recommendation': [
        'vdc', 'ward', 'recommendation letter', 'municipality',
        'ward recommendation', 'local recommendation', 'gaupalika',
    ],
    'Others': [
        'other', 'miscellaneous', 'document',
    ],
}


def detect_document_type(text):
    """
    Detect document type from extracted text using keyword matching.

    Args:
        text: Extracted text from the document

    Returns:
        DocumentType instance or None
    """
    if not text:
        return None

    text_lower = text.lower()

    # Get all document types from database
    doc_types = DocumentType.objects.all()

    best_match = None
    best_score = 0

    for doc_type in doc_types:
        keywords = doc_type.get_keywords_list()
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                # Longer keywords get higher scores
                score += len(keyword)

        if score > best_score:
            best_score = score
            best_match = doc_type

    if best_match and best_score > 0:
        logger.info(f"Auto-detected document type: {best_match.name} (score: {best_score})")
        return best_match

    logger.info("Could not auto-detect document type")
    return None


def seed_document_types():
    """
    Create default document types if they don't exist.
    Called during initial setup or migration.
    """
    created_count = 0
    for name, keywords in DEFAULT_DOCUMENT_TYPES.items():
        obj, created = DocumentType.objects.get_or_create(
            name=name,
            defaults={
                'keywords': ', '.join(keywords),
                'description': f'Auto-generated document type for {name}',
            }
        )
        if created:
            created_count += 1
            logger.info(f"Created document type: {name}")

    return created_count
