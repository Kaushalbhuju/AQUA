"""
Translation service with Translation Memory integration.
Translation Memory is the PRIMARY source. Google Translate is only
used as a fallback when no TM match exists.
For structured documents (Character Certificate), template-based
translation takes priority over everything else.
"""
import logging
import re
import hashlib
from django.db.models import Q
from translation.models import TranslationMemory, TranslationHistory
from translation.services.template_engine import detect_and_translate_with_templates

logger = logging.getLogger(__name__)


# ─── Document-specific rules for what to keep vs translate ──────────────────

DOCUMENT_RULES = {
    'Character Certificate': {
        'keep_patterns': [
            r'\bS\.?\s*No\.?\s*[:\-]?\s*\S+',                               # S.N. (Serial Number)
            r'\bReg\.?\s*No\.?\s*[:\-]?\s*\S+',                               # Registration Number
            r'\bSymbol\s*No\.?\s*[:\-]?\s*\S+',                                # Symbol Number
            r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:School|Academy|College|University|Institute|Campus|Board|Foundation|Education|Higher\s*Secondary)s?',  # School Name
            r'(?:Mr\.?|Ms\.?|Shri|Shreemati|Kumar|Kumari)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2}',  # Student Name
            r'\b\d+\.?\d*\s*(?:GPA|gpa|Grade\s*Point\s*Average)',             # GPA
            r'(?:Marks|Marks\s+Obtained|Total\s+Marks)\s*[:\-]?\s*\d+[\.,]?\d*',  # Marks
            r'\d{4}/\d{1,2}/\d{1,2}\s*\(\d{1,2}/\d{1,2}/\d{4}\)',           # Date format: 2082/12/18 (4/1/2026)
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',                              # Date format: 2082/12/18 or 2082-12-18
        ],
        'translate_all': True,
    },
    'Transcript': {
        'keep_patterns': [
            r'\b\d+\.?\d*\b',                            # GPA / Marks
            r'\bReg\.?\s*No\.?\s*[:\-]?\s*\S+',
            r'\bSymbol\s*No\.?\s*[:\-]?\s*\S+',
            r'\b[A-Z]{2,}\s*\d+',                        # Subject codes
            r'(?:Name|Student)\s*[:\-]?\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*',
            r'(?:College|School|University|Institute)[\s,]*[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*',
        ],
        'translate_all': True,
    },
    'Bank Statement': {
        'keep_patterns': [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',         # Dates
            r'(?:NPR|USD|JPY|Rs\.?)\s*[\d,]+\.?\d*',     # Amounts with currency
            r'\b\d{6,}\b',                                # Account/Transaction IDs
            r'\b[\d,]+\.\d{2}\b',                        # Decimal amounts
            r'(?:Account|A/C)\s*(?:No|Number)#?\s*[:\-]?\s*\d+',
            r'(?:Name|Customer)\s*[:\-]?\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*',
        ],
        'translate_all': False,
    },
    'Bank Balance Certificate': {
        'keep_patterns': [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'(?:NPR|USD|JPY|Rs\.?)\s*[\d,]+\.?\d*',
            r'\b\d{6,}\b',
            r'\b[\d,]+\.\d{2}\b',
            r'(?:Account|A/C)\s*(?:No|Number)#?\s*[:\-]?\s*\d+',
            r'(?:Name|Customer)\s*[:\-]?\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*',
            r'(?:Bank|Branch)\s*[:\-]?\s*[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*',
        ],
        'translate_all': True,
    },
    'Academic Certificate': {
        'keep_patterns': [
            r'\bS\.?\s*No\.?\s*[:\-]?\s*\S+',
            r'\bReg\.?\s*No\.?\s*[:\-]?\s*\S+',
            r'\bSymbol\s*No\.?\s*[:\-]?\s*\S+',
            r'[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:School|Academy|College|University|Institute|Campus)',
            r'(?:Mr\.?|Ms\.?|Shri|Shreemati|Kumar|Kumari)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2}',
            r'\b\d+\.?\d*\s*(?:GPA|gpa|Grade\s*Point\s*Average)',
            r'(?:Marks|Marks\s+Obtained|Percentage)\s*[:\-]?\s*\d+[\.,]?\d*',
        ],
        'translate_all': True,
    },
    'SOP': {
        'keep_patterns': [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',           # Proper names
            r'\b[A-Z]{1,2}\d{7,}\b',                     # Passport numbers
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',         # Dates
            r'(?:University|College|School|Institute)\s*[:\-]?\s*[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*',
        ],
        'translate_all': True,
    },
    'Sponsor Letter': {
        'keep_patterns': [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            r'\b[A-Z]{1,2}\d{7,}\b',
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'(?:Rs\.?|NPR|USD|JPY)\s*[\d,]+\.?\d*',
        ],
        'translate_all': True,
    },
    'Way of Payment': {
        'keep_patterns': [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'(?:NPR|USD|JPY|Rs\.?)\s*[\d,]+\.?\d*',
            r'\b\d{6,}\b',
            r'\b[\d,]+\.\d{2}\b',
            r'(?:Bank|Branch|Account)\s*[:\-]?\s*\S+',
        ],
        'translate_all': True,
    },
    'VDC/Ward Recommendation Letter': {
        'keep_patterns': [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'\bReg\.?\s*No\.?\s*[:\-]?\s*\S+',
            r'\b\d{4}\b',
            r'(?:Mr\.?|Ms\.?|Shri|Shreemati)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2}',
            r'(?:VDC|Ward|Municipality|Gaupalika|Rural\s*Municipality)\s*[:\-]?\s*\d*',
        ],
        'translate_all': True,
    },
    'Early Admission Request': {
        'keep_patterns': [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            r'(?:University|College|School)\s*[:\-]?\s*[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*',
        ],
        'translate_all': True,
    },
    'Early Japanese Language Certificate': {
        'keep_patterns': [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            r'(?:Japanese|N[0-9]|JLPT|NAT|JPT)\s*[:\-]?\s*\S+',
            r'(?:Level|Score|Grade|Class)\s*[:\-]?\s*\S+',
        ],
        'translate_all': True,
    },
    'Late Issue of NEB Certificate': {
        'keep_patterns': [
            r'\bS\.?\s*No\.?\s*[:\-]?\s*\S+',
            r'\bReg\.?\s*No\.?\s*[:\-]?\s*\S+',
            r'\bSymbol\s*No\.?\s*[:\-]?\s*\S+',
            r'(?:Mr\.?|Ms\.?|Shri|Shreemati)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2}',
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:School|College|University)',
        ],
        'translate_all': True,
    },
}


def _normalize_text(text):
    """Normalize text for TM matching: lowercase, collapse whitespace."""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def check_translation_memory(english_text, document_type=None):
    """
    Check Translation Memory for an existing translation.
    This is the PRIMARY translation source.

    Args:
        english_text: The English text to look up
        document_type: Optional DocumentType to filter by

    Returns:
        TranslationMemory instance if found, None otherwise
    """
    normalized = _normalize_text(english_text)
    if not normalized:
        return None

    # First try exact match with same document type
    if document_type:
        tm = TranslationMemory.objects.filter(
            english_text__iexact=normalized,
            document_type=document_type
        ).first()
        if tm:
            tm.increment_usage()
            return tm

    # Then try exact match without document type filter
    tm = TranslationMemory.objects.filter(
        english_text__iexact=normalized
    ).order_by('-usage_count').first()
    if tm:
        tm.increment_usage()
        return tm

    return None


def save_translation_memory(english_text, japanese_text, document_type=None, source='google'):
    """
    Save a new translation to Translation Memory.

    Args:
        english_text: English source text
        japanese_text: Japanese translation
        document_type: Optional DocumentType
        source: Source of translation (google/manual/review)

    Returns:
        TranslationMemory instance
    """
    normalized = _normalize_text(english_text)
    if not normalized or not japanese_text.strip():
        return None

    tm, created = TranslationMemory.objects.update_or_create(
        english_text=normalized,
        document_type=document_type,
        defaults={
            'japanese_text': japanese_text.strip(),
            'source': source,
        }
    )

    if created:
        logger.info(f"New TM entry saved: {normalized[:50]}...")
    else:
        logger.info(f"TM entry updated: {normalized[:50]}...")

    return tm


def translate_with_google(text):
    """
    Translate text using Google Translate (googletrans library).
    Only called when Translation Memory has no match.
    """
    try:
        from googletrans import Translator

        translator = Translator()
        result = translator.translate(text, src='en', dest='ja')
        return result.text
    except Exception as e:
        logger.error(f"Google Translate error: {e}")
        # Try deep_translator as fallback
        try:
            from deep_translator import GoogleTranslator

            # Split long texts (deep_translator has a 5000 char limit)
            if len(text) > 4500:
                parts = []
                sentences = re.split(r'(?<=[.!?])\s+', text)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > 4500:
                        if current_chunk:
                            translated = GoogleTranslator(source='en', target='ja').translate(current_chunk)
                            parts.append(translated)
                        current_chunk = sentence
                    else:
                        current_chunk += (" " if current_chunk else "") + sentence
                if current_chunk:
                    translated = GoogleTranslator(source='en', target='ja').translate(current_chunk)
                    parts.append(translated)
                return ' '.join(parts)
            else:
                return GoogleTranslator(source='en', target='ja').translate(text)
        except Exception as e2:
            logger.error(f"deep_translator error: {e2}")
            return f"[Translation Error: {str(e2)}]"


def apply_document_rules(text, document_type_name=None):
    """
    Apply document-specific rules to preserve certain content
    (numbers, dates, IDs) while marking translatable content.

    Returns list of (text_chunk, should_translate) tuples.
    """
    if not document_type_name or document_type_name not in DOCUMENT_RULES:
        # No rules — translate everything
        return [(text, True)]

    rules = DOCUMENT_RULES[document_type_name]
    keep_patterns = rules.get('keep_patterns', [])

    if not keep_patterns:
        return [(text, True)]

    # Combine all keep patterns
    combined_pattern = '|'.join(f'({p})' for p in keep_patterns)

    # Split text keeping the preserved tokens
    parts = re.split(f'({combined_pattern})', text)

    result = []
    for part in parts:
        if not part or not part.strip():
            continue
        # Check if this part matches any keep pattern
        is_keep = False
        for pattern in keep_patterns:
            if re.fullmatch(pattern, part.strip()):
                is_keep = True
                break
        result.append((part, not is_keep))

    return result if result else [(text, True)]


def translate_paragraph(paragraph, document_type=None, document_type_name=None):
    """
    Translate a single paragraph using TM-first strategy.

    Workflow:
    1. Check Translation Memory
    2. If found: use TM translation (TM HIT)
    3. If not found: translate with Google Translate, save to TM (TM MISS)

    Args:
        paragraph: English text paragraph
        document_type: DocumentType model instance
        document_type_name: String name of document type for rules

    Returns:
        tuple: (japanese_text, source) where source is 'tm' or 'google'
    """
    paragraph = paragraph.strip()
    if not paragraph:
        return ('', 'skip')

    # Step 1: Check Translation Memory (PRIMARY source)
    tm = check_translation_memory(paragraph, document_type)
    if tm:
        logger.info(f"TM HIT: {paragraph[:50]}...")
        return (tm.japanese_text, 'tm')

    # Step 2: Apply document rules and translate
    if document_type_name:
        chunks = apply_document_rules(paragraph, document_type_name)
    else:
        chunks = [(paragraph, True)]

    translated_parts = []
    for chunk_text, should_translate in chunks:
        if should_translate and chunk_text.strip():
            translated = translate_with_google(chunk_text)
            translated_parts.append(translated)
        else:
            translated_parts.append(chunk_text)

    japanese_text = ''.join(translated_parts)

    # Step 3: Save to Translation Memory
    save_translation_memory(paragraph, japanese_text, document_type, source='google')

    logger.info(f"TM MISS (Google used): {paragraph[:50]}...")
    return (japanese_text, 'google')


def translate_text(full_text, document_type=None, document=None):
    """
    Translate complete extracted text paragraph by paragraph.
    Memory-efficient: processes one paragraph at a time.

    For structured documents (Character Certificate), uses template-based
    translation engine first, then falls back to paragraph translation.

    Args:
        full_text: Complete English text
        document_type: DocumentType instance
        document: Document instance (for history logging)

    Returns:
        Complete Japanese translated text
    """
    if not full_text or not full_text.strip():
        return ''

    document_type_name = document_type.name if document_type else None

    # Try template-based translation for structured documents
    template_result = detect_and_translate_with_templates(full_text, document_type_name)
    if template_result and template_result['method'] == 'template':
        logger.info(
            f"Template-based translation used for {document_type_name} "
            f"(confidence: {template_result['confidence']:.2f}, "
            f"fields: {list(template_result['fields'].keys())})"
        )

        # Save extracted fields as notes on document if available
        if document and template_result['fields']:
            field_summary = '; '.join(
                f"{k}: {v}" for k, v in template_result['fields'].items()
            )
            if document.notes:
                document.notes += f'\n[Extracted: {field_summary}]'
            else:
                document.notes = f'[Extracted: {field_summary}]'
            TranslationHistory.objects.create(
                document=document,
                action='translate',
                details=f'Template translation: {len(template_result["fields"])} fields extracted',
            )

        return template_result['result']

    # Fallback: standard paragraph-by-paragraph translation
    paragraphs = full_text.split('\n')

    translated_paragraphs = []
    tm_hits = 0
    tm_misses = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            translated_paragraphs.append('')
            continue

        japanese, source = translate_paragraph(paragraph, document_type, document_type_name)
        translated_paragraphs.append(japanese)

        if source == 'tm':
            tm_hits += 1
        elif source == 'google':
            tm_misses += 1

    # Log translation stats
    if document:
        TranslationHistory.objects.create(
            document=document,
            action='translate',
            details=f'Translation completed. TM hits: {tm_hits}, Google translations: {tm_misses}',
        )

    logger.info(f"Translation complete. TM hits: {tm_hits}, Misses: {tm_misses}")
    return '\n'.join(translated_paragraphs)
