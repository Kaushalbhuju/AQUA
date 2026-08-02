"""
Template-based translation engine for structured documents.
Uses predefined Japanese templates instead of direct machine translation.
Produces professional output resembling official Japanese consultancy translations.
"""
import logging
import re

logger = logging.getLogger(__name__)


# ─── Field Extraction Patterns ──────────────────────────────────────────────

CHARACTER_CERTIFICATE_PATTERNS = {
    'student_name': [
        # Match: "Mr./Ms. NAME" - handles both ALL CAPS and Title Case
        r'(?i:Mr\.?/Ms\.?|Mr\.?|Ms\.?|Shri|Shreemati|Kumar|Kumari)\s+([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
        # Match: "Name: NAME"
        r'(?i:Name|Student[\u2019\']?s\s*Name|Candidate[\u2019\']?s\s*Name)\s*[:\-\u2013\u2014]?\s*([A-Z][A-Za-z\.\s]+?)(?:\n|$)',
        # Match: "certify that NAME"
        r'(?i:certify\s+that)\s+(?i:Mr\.?/Ms\.?|Mr\.?|Ms\.?|Shri|Shreemati|Kumar|Kumari)?\s*([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
        # Fallback: Look for person name patterns (2-4 capitalized words)
        r'(?i:that)\s+([A-Z][a-z]+(?:\s[A-Z][a-z\.]+){1,3})\s+(?:of|has|who)\b',
    ],
    'school_name': [
        # Match: "of SCHOOL NAME has completed" - MOST PRECISE
        r'\bof\s+([A-Z][A-Za-z\s,]+?(?:School|Academy|College|University|Institute|Campus|Secondary\s+School))\s+has\s+completed\b',
        # Match: "of SCHOOL NAME, LOCATION" - stop before newline or "has"
        r'\bof\s+([A-Z][A-Za-z\s,]+?(?:School|Academy|College|University|Institute|Campus|Secondary\s+School)[^,\n]*)',
        # Fallback: Look for institution names
        r'([A-Z][A-Za-z\s,]+?(?:School|Academy|College|University|Institute|Campus|Secondary\s+School)\b[^,\n]*)',
    ],
    'location': [
        # Match location after school name (comma-separated)
        r'(?:School|Academy|College|University|Institute|Campus)\s*,\s*([A-Z][A-Za-z\s,]+?)(?:\n|has\b|\s+has\b)',
    ],
    'gpa': [
        r'(?:GPA|Grade\s*Point\s*Average|g\.?p\.?a\.?|G\.?P\.?A\.?)\s*[:\-–—]?\s*(\d+\.?\d*)',
        r'(\d+\.\d+)\s*(?:GPA|gpa|Grade\s*Point\s*Average)',
        r'obtained\s*(?:a|an)?\s*(?:grade\s+point\s+average\s+of\s+)?(\d+\.?\d*)',
    ],
    'marks': [
        r'(?:Marks|Marks\s+Obtained|Total\s+Marks|Percentage)\s*[:\-]?\s*(\d+[\.,]?\d*(?:\s*[/:]\s*\d+[\.,]?\d*)?)',
        r'(\d+[\.,]?\d*)\s*(?:marks|percent)',
        r'obtained\s+(?:a|an)?\s*(?:total\s+)?(\d+[\.,]?\d*(?:\s*out\s+of\s+\d+[\.,]?\d*)?)',
    ],
    'grade': [
        r'(?:Grade|Class|Level|Standard)\s*(XII|XII|12|Twelve|twelve)',
        r'(?:Grade|Class|Level|Standard)\s*[:\-–—]?\s*(\w+)',
        r'\b(XII|XII|Twelve|12)\b',
    ],
    'year_bs': [
        r'(?:year|academic\s*year|session)\s*(?:\d{4}\s*[-–—]\s*)?(\d{4})\s*(?:B\.?S\.?|B\.?S\.?|Bikram\s*Sambat|B\.?\s*S\.?)',
        r'(\d{4})\s*(?:B\.?S\.?|Bikram\s*Sambat|B\.?\s*S\.?)',
        r'(?:B\.?S\.?|Bikram\s*Sambat)\s*(\d{4})',
    ],
    'year_ad': [
        r'(?:A\.?D\.?|AD|Anno\s+Domini|Christian\s*Era|Gregorian)\s*(\d{4})',
        r'(\d{4})\s*(?:A\.?D\.?|AD|Anno\s+Domini)',
        r'\(\s*(?:corresponding|equivalent|Gregorian)\s*(?:\d{4}\s*[-–—]\s*)?(\d{4})\s*(?:A\.?D\.?|AD|Anno\s+Domini|Gregorian)?\s*\)',
    ],
    'reg_no': [
        r'(?:Reg\.?\s*No\.?|Registration\s*(?:Number|No\.?)|Regd\.?\s*No\.?)\s*[:\-–—]?\s*(\S+)',
        r'(?:Reg\.?\s*No\.?|Registration)\s*[:\-–—]?\s*([A-Za-z0-9]+[-–—]?\d+)',
    ],
    'symbol_no': [
        r'(?:Symbol\s*(?:No\.?|Number)|Sym\.?\s*No\.?)\s*[:\-–—]?\s*(\S+)',
        r'(?:Symbol|Sym\.?)\s*[:\-–—]?\s*([A-Za-z0-9]+[-–—]?\d+)',
    ],
    'serial_no': [
        r'(?:Serial\s*(?:No\.?|Number)|Sr\.?\s*No\.?|S\.?\s*No\.?)\s*[:\-–—]?\s*(\S+)',
    ],
    'issue_date': [
        # Match format: 2082/12/18 (4/1/2026)
        r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*(\d{4}/\d{1,2}/\d{1,2}\s*\(\d{1,2}/\d{1,2}/\d{4}\))',
        # Match format: 2082/12/18 or 2082-12-18
        r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*(\d{4}[-/–—]\d{1,2}[-/–—]\d{1,2})',
        # Match format: December 18, 2026 or 18 December 2026
        r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*([A-Z][a-z]+\s+\d{1,2},?\s*\d{4}|\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
        # Fallback: issued on or dated
        r'(?:issued\s+on|dated)\s+(\d{4}[-/–—]\d{1,2}[-/–—]\d{1,2}|[A-Z][a-z]+\s+\d{1,2},?\s*\d{4})',
    ],
}

# ─── Japanese Templates ─────────────────────────────────────────────────────

CHARACTER_CERTIFICATE_TEMPLATES = [
    {
        'id': 'certify_clause',
        'keywords': ['this is to certify', 'certify that', 'hereby certify'],
        'priority': 1,
        'template': 'これは、{school_name}の{student_name}氏が、',
    },
    {
        'id': 'examination_clause',
        'keywords': ['completed', 'passed', 'successfully completed', 'has completed', 'has passed'],
        'priority': 2,
        'template': 'ネパール暦{year_bs}年（西暦{year_ad}年）に国家試験委員会によって実施された卒業証明書試験（グレード{grade}）を',
    },
    {
        'id': 'gpa_clause',
        'keywords': ['gpa', 'grade point average', 'obtained', 'secured', 'achieved'],
        'priority': 3,
        'template': '{gpa}GPAで修了したことを証明するものです。',  # Changed from 卒業 to 修了 per requirements
    },
    {
        'id': 'registration_info',
        'keywords': ['registration no', 'reg no', 'registration number', 'symbol no', 'symbol number'],
        'priority': 4,
        'template': '\n登録番号: {reg_no}\n記号番号: {symbol_no}',
    },
    {
        'id': 'character_clause',
        'keywords': ['character', 'conduct', 'good moral', 'well behaved', 'discipline', 'diligent', 'obedient',
                     'satisfactory', 'hardworking', 'honest', 'truthful', 'sincere'],
        'priority': 5,
        'template': '\n在学中、{student_name}氏の性格は誠実かつ真面目で、規律正しい態度を示していました。',
    },
    {
        'id': 'issue_clause',
        'keywords': ['issue date', 'date of issue', 'issued on'],
        'priority': 6,
        'template': '\n発行日: ネパール暦{issue_date_bs}年{issue_month}月{issue_day}日(西暦{issue_date_ad})',
    },
]

# ─── Standard Japanese Character Certificate Template ──────────────────────

FULL_TEMPLATE_JAPANESE = """\
これは、{school_name}の{student_name}氏が、ネパール暦{year_bs}年（西暦{year_ad}年）に国家試験委員会によって実施された卒業証明書試験（グレード{grade}）を{gpa}GPAで卒業したことを証明するものです。

{registration_info}
{character_info}
{issue_info}"""


class TemplateTranslationEngine:
    """
    Template-based translation for structured documents like Character Certificates.
    Produces professional Japanese output resembling official consultancy translations.
    """

    DETECTION_KEYWORDS = [
        'character certificate', 'certificate of character', 'to whom it may concern',
        'this is to certify', 'school leaving certificate', 'conduct certificate',
    ]

    def __init__(self):
        self.fields = {}
        self.remaining_text = ''
        self.confidence = 0.0

    def detect(self, text, document_type_name=None):
        """
        Detect if this document matches the Character Certificate format.
        Returns confidence score 0.0 - 1.0.
        """
        text_lower = text.lower().strip()
        score = 0.0

        # Check document type name
        if document_type_name and 'character' in document_type_name.lower():
            score += 0.3

        # Check for detection keywords
        for keyword in self.DETECTION_KEYWORDS:
            if keyword in text_lower:
                score += 0.15

        # Check for structured field patterns
        matched_fields = 0
        for field_name, patterns in CHARACTER_CERTIFICATE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched_fields += 1
                    break

        score += matched_fields * 0.08

        self.confidence = min(score, 1.0)
        return self.confidence >= 0.3

    def extract_fields(self, text):
        """
        Extract structured fields from Character Certificate text.
        Returns dict of field_name -> value.

        Non-translatable fields (preserved as-is in Japanese output):
        - serial_no (S.N.)
        - reg_no (Registration Number)
        - school_name (School Name)
        - location (Location)
        - student_name (Student Name)
        - gpa (GPA)
        - marks (Marks)
        """
        fields = {}

        for field_name, patterns in CHARACTER_CERTIFICATE_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    value = value.strip().rstrip(',')
                    if value:
                        fields[field_name] = value
                        break

        # Separate school_name from location when combined
        # e.g. "VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHT, KATHMANDU"
        if 'school_name' in fields:
            school_val = fields['school_name']
            # Clean up: remove trailing text after school name (like "has completed...")
            school_val = re.split(r'(?:\n|\s+has|\s+completed|\s+who)', school_val, maxsplit=1)[0].strip()
            
            # Check if there's a comma followed by location info
            parts = re.split(r',\s*', school_val, maxsplit=1)
            if len(parts) == 2:
                school_part, loc_part = parts
                # Verify the second part looks like a location (all caps, not "School" etc.)
                if not re.search(r'(?:School|Academy|College|Institute|Campus)', loc_part, re.IGNORECASE):
                    fields['school_name'] = school_part.strip()
                    fields['location'] = loc_part.strip()
                else:
                    fields['school_name'] = school_val
            else:
                fields['school_name'] = school_val

        # Infer BS year from context if not directly matched
        if 'year_bs' not in fields:
            year_matches = re.findall(r'\b(20\d{2})\b', text)
            for y in year_matches:
                y_int = int(y)
                # BS years typically range 2070-2085
                if 2070 <= y_int <= 2085:
                    fields['year_bs'] = y
                    break
            if 'year_bs' not in fields:
                for y in year_matches:
                    y_int = int(y)
                    if 2018 <= y_int <= 2029:
                        fields['year_bs'] = str(int(y) + 57)
                        break

        # Infer AD year if not found
        if 'year_ad' not in fields:
            year_matches = re.findall(r'\b(20\d{2})\b', text)
            for y in year_matches:
                y_int = int(y)
                if 2018 <= y_int <= 2029:
                    fields['year_ad'] = y
                    break
            if 'year_ad' not in fields and 'year_bs' in fields:
                fields['year_ad'] = str(int(fields['year_bs']) - 57)

        # Normalize grade
        if 'grade' not in fields:
            if re.search(r'\b(XII|12)\b', text, re.IGNORECASE):
                fields['grade'] = 'XII'
            elif re.search(r'\b(X|10)\b', text, re.IGNORECASE):
                fields['grade'] = 'X'

        # Clean grade value (remove "Grade " prefix if present)
        if 'grade' in fields:
            grade_val = fields['grade']
            grade_val = re.sub(r'^(?:Grade|Class|Level|Standard)\s+', '', grade_val, flags=re.IGNORECASE)
            if grade_val.upper() in ('XII', '12'):
                fields['grade'] = 'XII'
            elif grade_val.upper() in ('X', '10'):
                fields['grade'] = 'X'

        self.fields = fields
        return fields

    def get_remaining_unmatched_text(self, text):
        """
        Return text that wasn't matched by any field extraction.
        Cleans up fragments and returns only substantial content.
        """
        remaining = text
        for field_name, value in self.fields.items():
            for pattern in CHARACTER_CERTIFICATE_PATTERNS[field_name]:
                remaining = re.sub(pattern, ' ', remaining, flags=re.IGNORECASE)

        # Clean up: collapse whitespace, remove punctuation-only fragments
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        remaining = re.sub(r'[^\w\s]', ' ', remaining)
        remaining = re.sub(r'\s+', ' ', remaining).strip()

        # Remove single-letter fragments and very short words
        words = [w for w in remaining.split() if len(w) > 2 and w.lower() not in
                 ('the', 'and', 'for', 'with', 'has', 'had', 'was', 'his', 'her', 'its')]
        remaining = ' '.join(words)

        self.remaining_text = remaining
        return remaining

    def generate_japanese(self, fields=None):
        """
        Generate Japanese translation using templates.
        Non-translatable fields preserved as-is: serial_no, reg_no,
        school_name, location, student_name, gpa, marks.

        Args:
            fields: dict of extracted fields (uses self.fields if not provided)

        Returns:
            Japanese text string
        """
        f = fields if fields else self.fields

        # Build registration info line
        reg_parts = []
        if f.get('serial_no'):
            reg_parts.append(f"S.N.: {f['serial_no']}")
        if f.get('reg_no'):
            reg_parts.append(f"登録番号: {f['reg_no']}")
        if f.get('symbol_no'):
            reg_parts.append(f"記号番号: {f['symbol_no']}")
        registration_info = '\n'.join(reg_parts)

        # Build character info
        character_info = ''
        student = f.get('student_name', '当該学生')
        if any(kw in self.remaining_text.lower() for kw in
               ['character', 'conduct', 'good', 'moral', 'discipline', 'diligent', 'sincere', 'honest']):
            character_info = f"在学中、{student}氏の性格は誠実かつ真面目で、規律正しい態度を示していました。"

        # Build issue info
        issue_info = ''
        if f.get('issue_date'):
            # Try to parse and format the date properly
            issue_date = f['issue_date']
            
            # Check if date is in format: 2082/12/18 (BS) or (4/1/2026) (AD)
            # Extract BS and AD dates if both present
            bs_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', issue_date)
            ad_match = re.search(r'\((\d{1,2})/(\d{1,2})/(\d{4})\)', issue_date)
            
            if bs_match and ad_match:
                # Format: ネパール暦 2082 年 12 月 18 日(西暦 2026 年 04 月 01 日)
                bs_year = bs_match.group(1)
                bs_month = bs_match.group(2).zfill(2)
                bs_day = bs_match.group(3).zfill(2)
                ad_month = ad_match.group(1).zfill(2)
                ad_day = ad_match.group(2).zfill(2)
                ad_year = ad_match.group(3)
                
                issue_info = f"発行日: ネパール暦{bs_year}年{bs_month}月{bs_day}日(西暦{ad_year}年{ad_month}月{ad_day}日)"
            elif bs_match:
                bs_year = bs_match.group(1)
                bs_month = bs_match.group(2).zfill(2)
                bs_day = bs_match.group(3).zfill(2)
                issue_info = f"発行日: ネパール暦{bs_year}年{bs_month}月{bs_day}日"
            else:
                issue_info = f"発行日: {issue_date}"

        # Build result
        result_parts = []

        # NEW: Add English fields at the top for clarity
        english_fields = []
        if f.get('student_name'):
            english_fields.append(f"Student Name: {f['student_name']}")
        if f.get('school_name'):
            school_with_location = f['school_name']
            if f.get('location'):
                school_with_location = f"{f['school_name']}, {f['location']}"
            english_fields.append(f"School: {school_with_location}")
        
        if english_fields:
            result_parts.append('\n'.join(english_fields))
            result_parts.append('')  # Empty line separator

        # School line with location (for Japanese template)
        school_line = f.get('school_name', '【学校名】')
        if f.get('location'):
            school_line = f"{school_line}, {f['location']}"

        # Main certification clause - Professional Japanese format
        main_clause = f"これは、{school_line}の{f.get('student_name', '【氏名】')}氏が、"
        
        if f.get('year_bs') or f.get('year_ad'):
            year_part = ''
            if f.get('year_bs') and f.get('year_ad'):
                year_part = f"ネパール暦{f['year_bs']}年（西暦{f['year_ad']}年）に"
            elif f.get('year_bs'):
                year_part = f"ネパール暦{f['year_bs']}年に"
            elif f.get('year_ad'):
                year_part = f"西暦{f['year_ad']}年に"

            main_clause += f"国家試験委員会によって実施された卒業証明書試験（グレード{f.get('grade', 'XII')}）を{f.get('gpa', '')}GPAで修了したことを証明するものです。"  # 修了 instead of 卒業
        else:
            main_clause += f"卒業証明書試験（グレード{f.get('grade', 'XII')}）を{f.get('gpa', '')}GPAで修了したことを証明するものです。"  # 修了 instead of 卒業
        
        result_parts.append(main_clause)

        # Marks line (if present)
        if f.get('marks'):
            result_parts.append(f"取得点数: {f['marks']}")

        if registration_info:
            result_parts.append(registration_info)

        if character_info:
            result_parts.append(character_info)

        if issue_info:
            result_parts.append(issue_info)

        if self.remaining_text and len(self.remaining_text) > 30:
            result_parts.append(f"\n（備考: {self.remaining_text}）")

        return '\n\n'.join(result_parts)

    def translate(self, text, document_type_name=None):
        """
        Full pipeline: detect, extract, generate.
        Returns dict with result, confidence, fields, method.
        """
        if not self.detect(text, document_type_name):
            return {
                'result': None,
                'confidence': self.confidence,
                'fields': {},
                'method': 'not_detected',
            }

        self.extract_fields(text)
        self.get_remaining_unmatched_text(text)
        japanese = self.generate_japanese()

        return {
            'result': japanese,
            'confidence': self.confidence,
            'fields': self.fields,
            'method': 'template',
        }


# ─── Engine Registry ────────────────────────────────────────────────────────

REGISTERED_ENGINES = {
    'Character Certificate': TemplateTranslationEngine,
    # Additional engines will be added as templates are provided:
    # 'Bank Balance Certificate': ...,
    # 'Bank Statement': ...,
    # 'Transcript': ...,
    # 'Academic Certificate': ...,
    # 'SOP': ...,
    # 'Sponsor Letter': ...,
    # 'Way of Payment': ...,
    # 'VDC/Ward Recommendation': ...,
    # 'Early Admission Request': ...,
    # 'Early Japanese Language Certificate': ...,
    # 'Late Issue of NEB Certificate': ...,
}


def detect_document_type(text):
    """
    Identify document type from text content using keyword matching.
    Returns (document_type_name, confidence) tuple.

    Detection keywords:
      - Character Certificate: character certificate, school leaving certificate, conduct, this is to certify
      - Transcript: transcript, grade report, marks sheet, semester, gpa, grade point
      - Academic Certificate: academic certificate, certificate of completion, has completed the course
      - Bank Statement: bank statement, account statement, transaction, debit, credit, balance
      - Bank Balance Certificate: bank balance, balance certificate, balance confirmation
      - SOP: statement of purpose, sop, study abroad, educational goal
      - Sponsor Letter: sponsor letter, sponsorship, financial support, undertake
      - Way of Payment: payment, fund transfer, remittance, bank transfer, tuition fee
      - VDC/Ward Recommendation: vdc, ward, recommendation, municipality, gaupalika
      - Early Admission Request: early admission, early entry, advance enrollment
      - Early Japanese Language Certificate: japanese language, jlpt, nihongo, japanese proficiency
      - Late Issue of NEB Certificate: late issue, duplicate certificate, re-issue, replacement
    """
    if not text:
        return ('Others', 0.0)

    text_lower = text.lower().strip()

    signatures = [
        ('Character Certificate', [
            'character certificate', 'this is to certify', 'school leaving certificate',
            'certificate of character', 'conduct certificate', 'to whom it may concern',
            'national examinations board',
        ]),
        ('Transcript', [
            'transcript', 'grade report', 'marks sheet', 'grade point',
            'credit hour', 'credit earned', 'semester', 'gpa',
        ]),
        ('Academic Certificate', [
            'academic certificate', 'certificate of completion', 'has completed the course',
            'programme', 'academic session', 'academic year',
        ]),
        ('Bank Statement', [
            'bank statement', 'account statement', 'transaction details',
            'debit', 'credit', 'opening balance', 'closing balance',
        ]),
        ('Bank Balance Certificate', [
            'bank balance', 'balance certificate', 'balance confirmation',
            'current balance', 'account balance',
        ]),
        ('SOP', [
            'statement of purpose', 'my name is', 'i am writing', 'study abroad',
            'educational goal', 'career goal', 'i wish to pursue',
        ]),
        ('Sponsor Letter', [
            'sponsor letter', 'sponsorship', 'letter of sponsorship',
            'financial support', 'i undertake', 'bear all expenses',
        ]),
        ('Way of Payment', [
            'payment', 'fund transfer', 'remittance', 'bank transfer',
            'tuition fee', 'payment method',
        ]),
        ('VDC/Ward Recommendation', [
            'vdc', 'ward', 'recommendation', 'municipality',
            'gaupalika', 'rural municipality', 'ward office',
        ]),
        ('Early Admission Request', [
            'early admission', 'early entry', 'advance enrollment',
            'early enrollment', 'request for early',
        ]),
        ('Early Japanese Language Certificate', [
            'japanese language', 'jlpt', 'nihongo', 'japanese proficiency',
            'japanese certificate', 'japanese course',
        ]),
        ('Late Issue of NEB Certificate', [
            'late issue', 'duplicate certificate', 're-issue',
            'replacement certificate', 'lost certificate',
        ]),
    ]

    best_type = 'Others'
    best_score = 0.0

    for doc_type, keywords in signatures:
        score = 0.0
        for kw in keywords:
            if kw in text_lower:
                score += 0.2
        if score > best_score:
            best_score = score
            best_type = doc_type

    return (best_type, min(best_score, 1.0))


def get_engine_for_document(document_type_name):
    """Get the appropriate template engine for a document type."""
    if not document_type_name:
        return None
    engine_cls = REGISTERED_ENGINES.get(document_type_name)
    if engine_cls:
        return engine_cls()
    return None


def detect_and_translate_with_templates(text, document_type_name=None):
    """
    Try to translate using template engines first.
    Falls back to None if no engine matches, allowing regular MT.
    """
    for doc_type, engine_cls in REGISTERED_ENGINES.items():
        if document_type_name and document_type_name != doc_type:
            continue
        engine = engine_cls()
        result = engine.translate(text, document_type_name)
        if result['method'] == 'template':
            logger.info(f"Template translation used for {doc_type} (confidence: {result['confidence']:.2f})")
            return result
    return None
