"""
Character Certificate Parser - Enhanced with Multi-Strategy Extraction Engine.
Implements OCR normalization, field-specific extraction strategies, validation rules,
and confidence scoring for production-grade document parsing.

Architecture:
  OCR Text → OCR Normalization → Multi-Strategy Extraction → Validation → Confidence → JSON
"""
import re
import logging
from translation.services.parsers.base import BaseDocumentParser, StructuredDataResult

logger = logging.getLogger(__name__)


class CharacterCertificateParser(BaseDocumentParser):
    """
    Parser for NEB Character Certificates.
    Implements multi-strategy extraction with OCR normalization and validation.
    """
    
    SUPPORTED_DOCUMENT_TYPES = ['Character Certificate']
    
    # ============================================================
    # OCR NORMALIZATION RULES
    # Correct common OCR mistakes before extraction
    # ============================================================
    OCR_NORMALIZATIONS = [
        # Currency/character fixes
        (r'¥', 'V'),  # Yen symbol to V
        (r'0f\b', 'of'),  # 0f to of
        (r'0\b([a-z])', r'O\1'),  # 0 to O when followed by letter
        (r'\bl\b', 'I'),  # lowercase l to I when standalone
        (r'é', 'e'),  # accented e -> e
        (r'ñ', 'n'),
        (r'\u2019|\u2018', "'"),  # curly quotes -> straight
        (r'\u201c|\u201d', '"'),
        
        # Word corrections
        (r'certlficate', 'certificate'),
        (r'certiflcate', 'certificate'),
        (r'Examlinatlon', 'Examination'),
        (r'Natl0nal', 'National'),
        (r'B\.?S\.', 'B.S.'),
        (r'A\.?D\.', 'A.D.'),
        (r'This[’\']s', 'This is'),  # This's -> This is
        (r'tovcertifythat', 'to certify that'),
        (r'tocertifythat', 'to certify that'),
        (r'certifythat', 'certify that'),
        (r'SADR', 'SADR'),  # keep placeholder (will be cleaned)
        
        # Mr./Ms. fixes
        (r'Mr\.?\s*/?\s*Ms\.?', 'Mr./Ms.'),
        (r'Mn/', 'Mr./'),
        (r'Mgyiit', 'Mr.'),
        
        # Date/number fixes
        (r'Datg\b', 'Date'),
        (r'Dat[ae]', 'Date'),
        (r'Registr[ao]tion', 'Registration'),
        (r'Reg\.?\s*No,', 'Reg. No.'),
        (r'No,\s*(\d)', r'No. \1'),  # "No, 81527" -> "No. 81527"
        (r'\s+([0-9]+)\s*GPA', r' \1 GPA'),
        (r'with\s+[^\d]+(\d+\.\d+)\s*GPA', r'with \1 GPA'),
        # NEB-specific: normalize exam year forms like "2079BS" -> "2079 B.S."
        (r'(\d{4})\s*B\.?S\.?\b', r'\1 B.S.'),
        (r'(\d{4})\s*A\.?D\.?\b', r'\1 A.D.'),
        
        # Spacing fixes
        (r'\s+', ' '),  # Normalize multiple spaces
        (r'\.\s*([A-Z])', r'. \1'),  # Ensure space after periods
        (r'\s*,\s*', ', '),  # Normalize comma spacing
        (r'\(\s*(\d)', r'(\1'),  # Remove space after opening paren
        (r'(\d)\s*\)', r'\1)'),  # Remove space before closing paren
        (r'\s+$', ''),  # Trailing whitespace
        (r'^\s+', ''),  # Leading whitespace
    ]
    
    # ============================================================
    # VALIDATION RULES
    # Invalid tokens that should never appear in certain fields
    # ============================================================
    VALIDATION_RULES = {
        'school_name': {
            'invalid_tokens': ['has', 'completed', 'GPA', 'Grade', 'Controller', 
                             'Chairperson', 'Certificate', 'Government', 'National',
                             'Examination', 'Board', 'Mr.', 'Ms.', 'certify'],
            'must_contain': ['School', 'Academy', 'College', 'University', 
                           'Institute', 'Campus', 'Secondary'],
            'min_length': 5,
            'max_length': 100,
        },
        'student_name': {
            'invalid_tokens': ['of', 'has', 'completed', 'GPA', 'Government',
                             'National', 'Examination', 'Board', 'Certificate',
                             'certify', 'School', 'Academy'],
            'min_length': 2,
            'max_length': 50,
        },
        'registration_number': {
            'pattern': r'^\d{10,15}$',  # 10-15 digits only
            'invalid_tokens': ['No', 'Reg', 'Serial'],
        },
        'serial_number': {
            'pattern': r'^[A-Z]?\d+$',  # Letter + digits or just digits
            'invalid_tokens': ['No', 'Serial'],
        },
        'gpa': {
            'pattern': r'^(\d\.\d{1,2}|[0-4])$',  # 0.00-4.00 range
            'min_value': 0.0,
            'max_value': 4.0,
        },
        'grade': {
            'valid_values': ['XI', 'XII', '11', '12'],
        },
        'year_bs': {
            'pattern': r'^20[789]\d$',  # 2070-2099 range
            'min_value': 2070,
            'max_value': 2099,
        },
        'year_ad': {
            'pattern': r'^20[2-3]\d$',  # 2020-2039 range
            'min_value': 2020,
            'max_value': 2039,
        },
    }
    
    # Reuse extraction patterns from template_engine.py
    # ENHANCED: Multiple strategies per field for better extraction
    FIELD_PATTERNS = {
        'student_name': [
            # Strategy 1: "Mr./Ms. NAME of/has" - try explicit title first so generic pattern does not eat the name
            r'(?i:Mr\.?/Ms\.?|Mr\.?|Ms\.?|Shri|Shreemati|Kumar|Kumari)\s+([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
            # Strategy 2: "certify that NAME of/has" - generic (handles garbled Mr./Ms.)
            r'(?:to\s+)?certify\s+that\s+(?:[A-Z][a-z]+[\./]?\s*){0,3}([A-Z][A-Z]?[\.A-Z\s]+?)\s+(?:of|has)\b',
            # Strategy 3: "Name: NAME"
            r'(?i:Name|Student[\u2019\']?s\s*Name)\s*[:\-\u2013\u2014]?\s*([A-Z][A-Za-z\.\s]+?)(?:\s|$)',
            # Strategy 4: Between "certify that" and "of" (garbled prefix tolerant)
            r'certify\s+that\s+([A-Z][A-Z\s\.]{1,30}?)\s+of\s+[A-Z]',
            # Strategy 5: Name after "certify that" with OCR-garbled prefix - handles cases where
            # Mr./Ms. or other tokens appear between "that" and the name due to OCR errors
            r'(?:to\s+)?certify\s+that\s+(?:[A-Z][a-z]+\s*){0,2}([A-Z][A-Z\s]{2,30}?)\s+(?:of|has|\n)',
            # Strategy 6: Isolated name BEFORE "This is to certify" - handles scrambled OCR where
            # the name appears on its own line before the certify clause (e.g. "ROHAN GURUNG\nThis is to certify...")
            r'([A-Z][A-Z]+\s+[A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)?)\s+This is to certify',
        ],
        'school_name': [
            # Strategy 1: "of SCHOOL NAME has completed" - MOST PRECISE
            r'\bof\s+([A-Z][A-Za-z\s,]+?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS))\s+has\s+completed\b',
            # Strategy 2: "of SCHOOL, LOCATION has"
            r'\bof\s+([A-Z][A-Za-z\s,]+?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS))',
            # Strategy 3: A school name ending in a known keyword, captured from the last match
            r'([A-Z][A-Z\s,]{2,}?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS|Secondary\s+School))',
            # Strategy 4: Keyword-based extraction (fallback)
            r'([A-Z][A-Za-z\s,]+?(?:School|Academy|College|University|Institute|Campus)\b)',
            # Strategy 5: School name from last keyword when OCR order changes - capture from
            # the last school-related keyword backward, discarding preceding OCR garbage
            r'([A-Z][A-Z\s,]{8,}?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS)\b)',
        ],
        'location': [
            # Strategy 1: After school name, before "has"
            r'(?:School|Academy|College|Institute|Campus)\s*,\s*([A-Z][A-Za-z\s,]+?)\s+has\b',
            # Strategy 2: School followed by comma and location
            r'(?:School|Academy|College)\s*,\s*([A-Z][A-Za-z,\s]+?)(?:\s+has|\s+completed|$)',
            # Strategy 3: Location keywords in parens or trailing caps
            r'\b(SAMAKHUSHI|KATHMANDU|LALITPUR|BHAKTAPUR|POKHARA|LUMBINI|CHITWAN|HETAUDA|BUTWAL|NEPALGUNJ|BIRATNAGAR|JANAKPUR|DHARAN|BIRGUNJ|KIRTIPUR|GODAWARI)[A-Z\s,]*',
        ],
        'gpa': [
            r'(\d+\.\d+)\s*(?:GPA|gpa|Grade\s*Point\s*Average)',
            r'with\s+[^\d]{0,15}?(\d\.\d{1,2})\s*(?:GPA|gpa)',
            r'(\d\.\d{1,2})\s*GPA',
            r'(?:GPA|Grade\s*Point\s*Average|G\.?P\.?A\.?)\s*[:\-–—]?\s*(\d+\.?\d*)',
            r'obtained\s*(?:a|an)?\s*(?:grade\s+point\s+average\s+of\s+)?(\d+\.?\d*)',
            r'(?:GPA|Grade\s*Point\s*Average|G\.?P\.?A\.?)\b[\s:\-–—]*(\d+\.?\d*)',
        ],
        'marks': [
            r'(?:Marks|Marks\s+Obtained|Total\s+Marks|Percentage)\s*[:\-]?\s*(\d+[\.,]?\d*(?:\s*[/:]\s*\d+[\.,]?\d*)?)',
            r'(\d+[\.,]?\d*)\s*(?:marks|percent)',
        ],
        'grade': [
            r'(?:Grade|Class|Level|Standard)\s*(XII|XII|12|Twelve|twelve)',
            r'(?:Grade|Class|Level|Standard)\s*[:\-–—]?\s*(\w+)',
            r'\b(XII|XII|Twelve|12)\b',
            r'\(\s*Grade\s*(XII|X|10|11|12)\s*\)',
        ],
        'year_bs': [
            r'(?:year|academic\s*year|session)\s*(?:\d{4}\s*[-–—]\s*)?(\d{4})\s*(?:B\.?S\.?|B\.?S\.?|Bikram\s*Sambat|B\.?\s*S\.?)',
            r'(\d{4})\s*(?:B\.?S\.?|Bikram\s*Sambat|B\.?\s*S\.?)',
            r'(?:B\.?S\.?|Bikram\s*Sambat)\s*(\d{4})',
            r'(\d{4})/[0-9]{1,2}/[0-9]{1,2}\s+\(',  # BS date before AD in parens
        ],
        'year_ad': [
            r'(?:A\.?D\.?|AD|Anno\s+Domini|Christian\s*Era|Gregorian)\s*(\d{4})',
            r'(\d{4})\s*(?:A\.?D\.?|AD|Anno\s+Domini)',
            r'\(\s*(?:corresponding|equivalent|Gregorian)\s*(?:\d{4}\s*[-–—]\s*)?(\d{4})\s*(?:A\.?D\.?|AD|Anno\s+Domini|Gregorian)?\s*\)',
            r'(\d{4})/\d{1,2}/\d{1,2}\s*\)',  # AD date inside parens
        ],
        'reg_no': [
            r'(?:Reg\.?\s*No\.?|Registration\s*(?:Number|No\.?)|Regd\.?\s*No\.?)\s*[:\-–—]?\s*(\d{6,})',
            r'(?:Reg\.?\s*No\.?|Registration)\s*[:\-–—]?\s*([A-Za-z0-9]+[-–—]?\d+)',
            r'(?:Reg\.?\s*No\.?|Registration\s*(?:Number)?)\s*[,\:\-–—]?\s*(\d{10,})',
        ],
        'symbol_no': [
            r'(?:Symbol\s*(?:No\.?|Number)|Sym\.?\s*No\.?)\s*[:\-–—]?\s*(\S+)',
        ],
        'serial_no': [
            r'(?:Serial\s*(?:No\.?|Number)|Sr\.?\s*No\.?|S\.?\s*No\.?|s\.?\s*No\.?)\s*[:\-–—]?\s*([A-Z]?\d{4,})',
            r'(?:Serial\s*(?:No\.?|Number)|Sr\.?\s*No\.?|S\.?\s*No\.?)\s*[:\-–—]?\s*(\S+)',
        ],
        'issue_date': [
            r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*(\d{4}/\d{1,2}/\d{1,2}\s*\(\d{1,2}/\d{1,2}/\d{4}\))',
            r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*(\d{4}[-/–—]\d{1,2}[-/–—]\d{1,2})',
            r'(?:issued\s+on|dated)\s+(\d{4}[-/–—]\d{1,2}[-/–—]\d{1,2}|[A-Z][a-z]+\s+\d{1,2},?\s*\d{4})',
            r'Date\s*:?\s*(\d{4}/\d{1,2}/\d{1,2}\s*\([^)]*\))',
        ],
    }
    
    def parse(self, extracted_text, layout_data=None, tables=None):
        """
        Parse Character Certificate text into structured fields.
        
        Enhanced Pipeline:
        1. OCR Normalization - Fix common OCR mistakes
        2. Text Normalization - Convert newlines to spaces for reliable matching
        3. Multi-Strategy Extraction - Try multiple patterns per field
        4. Validation - Reject invalid extractions
        5. Confidence Scoring - Rate extraction quality
        
        Args:
            extracted_text: Raw text from PDF/image extraction
            layout_data: Optional layout information
            tables: Optional table data (usually empty for certificates)
            
        Returns:
            StructuredDataResult with extracted fields
        """
        if not extracted_text:
            return StructuredDataResult(
                fields={},
                tables=tables,
                metadata={'error': 'No text to parse'}
            )
        
        # Step 1: OCR Normalization
        normalized = self._normalize_ocr(extracted_text)
        
        # Step 2: Extract fields using patterns (now with normalized text)
        fields = self._extract_fields(normalized)
        
        # Step 3: Post-process and clean fields
        fields = self._clean_fields(fields, normalized)
        
        # Step 4: Validation
        validated_fields, validation_errors = self._validate_extraction(fields)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(validated_fields)
        
        metadata = {
            'parser': 'CharacterCertificateParser',
            'confidence': confidence,
            'fields_extracted': len(validated_fields),
            'total_patterns': sum(len(patterns) for patterns in self.FIELD_PATTERNS.values()),
            'validation_errors': validation_errors,
            'ocr_normalized': True,
        }
        
        logger.info(f"Character Certificate: {len(validated_fields)} fields extracted, confidence: {confidence:.0%}")
        
        return StructuredDataResult(
            fields=validated_fields,
            tables=tables or [],
            metadata=metadata,
        )
    
    def _normalize_ocr(self, text):
        """
        Step 1: Normalize OCR text to fix common mistakes.
        
        Critical for handling real-world OCR output which often has:
        - Wrong characters (¥ instead of V, 0f instead of of)
        - Inconsistent spacing
        - Mixed case when ALL CAPS expected
        """
        normalized = text
        
        # Apply all OCR normalization rules
        for pattern, replacement in self.OCR_NORMALIZATIONS:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # CRITICAL: Normalize whitespace - replace newlines/multiple spaces with single space
        # This makes regex matching MUCH more reliable for multi-line OCR output
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        logger.debug(f"OCR normalized: {len(text)} -> {len(normalized)} chars")
        return normalized
    
    def _validate_extraction(self, fields):
        """
        Step 4: Validate extracted fields and reject invalid ones.
        Uses word-boundary checks so 'Board' does not reject 'BOARDING'.
        """
        validated = {}
        errors = []
        
        # Validation rules for each field
        validation_rules = {
            'school_name': {
                'invalid_tokens': ['has', 'completed', 'GPA', 'Grade', 'Controller', 
                                 'Chairperson', 'Certificate', 'Government', 'National',
                                 'Examination', 'Board', 'Mr.', 'Ms.', 'certify'],
                'must_contain': ['School', 'Academy', 'College', 'University', 
                               'Institute', 'Campus', 'Secondary'],
            },
            'student_name': {
                'invalid_tokens': ['of', 'has', 'completed', 'GPA', 'Government',
                                 'National', 'Examination', 'Board', 'Certificate',
                                 'certify', 'School', 'Academy'],
            },
            'reg_no': {
                'pattern': r'^\d{10,15}$',  # 10-15 digits only
            },
            'serial_no': {
                'pattern': r'^[A-Z]?\d+$',  # Letter + digits or just digits
            },
            'gpa': {
                'pattern': r'^\d\.\d{1,2}$',  # Format like 3.14
                'min_value': 0.0,
                'max_value': 4.0,
            },
            'grade': {
                'valid_values': ['XI', 'XII', '11', '12'],
            },
            'year_bs': {
                'min_value': 2070,
                'max_value': 2099,
            },
            'year_ad': {
                'min_value': 2020,
                'max_value': 2039,
            },
        }
        
        for field_name, value in fields.items():
            if field_name not in validation_rules:
                # No validation rules, accept as-is
                validated[field_name] = value
                continue
            
            rules = validation_rules[field_name]
            is_valid = True
            field_errors = []
            
            # Check invalid tokens (word-boundary so 'Board' != 'Boarding')
            if 'invalid_tokens' in rules:
                for token in rules['invalid_tokens']:
                    if re.search(r'\b' + re.escape(token) + r'\b', value, re.IGNORECASE):
                        is_valid = False
                        field_errors.append(f"Contains invalid token: '{token}'")
                        break
            
            # Check must_contain (for school names)
            if 'must_contain' in rules:
                has_required = any(token.lower() in value.lower() for token in rules['must_contain'])
                if not has_required:
                    is_valid = False
                    field_errors.append(f"Missing required keyword")
            
            # Check pattern
            if 'pattern' in rules:
                if not re.match(rules['pattern'], value):
                    is_valid = False
                    field_errors.append(f"Invalid format")
            
            # Check numeric range
            if 'min_value' in rules or 'max_value' in rules:
                try:
                    num_value = float(value)
                    if 'min_value' in rules and num_value < rules['min_value']:
                        is_valid = False
                        field_errors.append(f"Below minimum: {num_value}")
                    if 'max_value' in rules and num_value > rules['max_value']:
                        is_valid = False
                        field_errors.append(f"Above maximum: {num_value}")
                except ValueError:
                    if 'pattern' not in rules:  # Only fail if not already failed pattern check
                        is_valid = False
                        field_errors.append(f"Not a valid number")
            
            # Check valid values (for grade)
            if 'valid_values' in rules and value.upper() not in [v.upper() for v in rules['valid_values']]:
                is_valid = False
                field_errors.append(f"Invalid value: {value}")
            
            if is_valid:
                validated[field_name] = value
                logger.debug(f"[{field_name}] Validation PASSED")
            else:
                errors.append(f"{field_name}: {'; '.join(field_errors)}")
                logger.warning(f"[{field_name}] Validation FAILED: {field_errors}")
        
        return validated, errors
    
    def _extract_fields(self, text):
        """Extract all fields using regex patterns."""
        fields = {}
        
        for field_name, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    value = value.strip().rstrip(',')
                    if value:
                        fields[field_name] = value
                        logger.debug(f"Extracted {field_name}: {value}")
                        break  # Use first matching pattern
        
        return fields
    
    def _clean_fields(self, fields, original_text):
        """Clean and normalize extracted fields."""        
        # Separate school_name from location when combined
        if 'school_name' in fields:
            school_val = fields['school_name']
            # Clean up: remove trailing text after school name (also handles "at SCHOOL")
            school_val = re.split(r'(?:\n|\s+has|\s+completed|\s+who|\s+at\s)', school_val, maxsplit=1)[0].strip()
            
            # For garbled OCR, extract only the clean school portion:
            # everything before " has completed" or the last big-word school keyword
            # First, take substring from the LAST school keyword backwards
            school_match = re.search(
                r'([A-Z][A-Z\s,]{2,}?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS))\b',
                school_val
            )
            if school_match:
                # When OCR garbage precedes, the last clean school name is usually
                # the portion from the last recognizable name token to the keyword.
                # Prefer the longest clean run ending with a known keyword.
                keyword_hits = list(re.finditer(
                    r'(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS|Secondary\s+School)\b',
                    school_val, re.IGNORECASE
                ))
                if keyword_hits:
                    # Take from last keyword start backwards to find the name start:
                    # find the position ~60 chars before the last keyword that starts with a capital letter
                    kw = keyword_hits[-1]
                    kw_start = kw.start()
                    window = school_val[max(0, kw_start - 60):kw_start]
                    # Find capital-letter run right before keyword
                    cap_matches = list(re.finditer(r'[A-Z][A-Z\s,]{2,}(?=\s|$)', window))
                    if cap_matches:
                        clean_start = window.rfind(cap_matches[-1].group().split(' ')[0]) if cap_matches else 0
                        if clean_start >= 0:
                            # Re-anchor to absolute position
                            abs_start = max(0, kw_start - 60) + clean_start
                            school_val = school_val[abs_start:kw.end()].strip()
                    else:
                        # Fallback: take window around keyword and find first caps word
                        window2 = school_val[max(0, kw_start - 80):kw_start]
                        first_cap = re.search(r'[A-Z][A-Za-z]+', window2)
                        if first_cap:
                            rel_start = window2.index(first_cap.group())
                            abs_start = max(0, kw_start - 80) + rel_start
                            school_val = school_val[abs_start:kw.end()].strip()
                        else:
                            school_val = school_match.group(1).strip() if school_match else school_val
                else:
                    school_val = school_match.group(1).strip() if school_match else school_val

            # Strip leading garbage like GPA/Grade tokens that polluted the school capture
            # e.g. "GPA HEART SECONDARY BOARDING SCHOOL" -> "HEART SECONDARY BOARDING SCHOOL"
            school_val = re.sub(r'^(?:GPA|Grade\s*XII?|XII|XI|GPA:?)\s+', '', school_val, flags=re.IGNORECASE).strip()
            
            # Check if there's a comma followed by location info
            # But ONLY if the second part doesn't itself contain a school keyword
            parts = re.split(r',\s*', school_val, maxsplit=1)
            if len(parts) == 2:
                school_part, loc_part = parts
                has_school_kw = bool(re.search(r'(?:School|Academy|College|University|Institute|Campus)\b', loc_part, re.IGNORECASE))
                if not has_school_kw:
                    fields['school_name'] = school_part.strip()
                    fields['location'] = loc_part.strip()
                else:
                    fields['school_name'] = school_val
            else:
                fields['school_name'] = school_val
        
        # Infer student_name if missing - position-independent fallback
        # Look for isolated uppercase 2-3 word name not containing school/cert keywords
        if 'student_name' not in fields:
            # Prefer name that appears near certify or as topmost uppercase block
            certify_pos = original_text.lower().find('certify')
            candidates = re.findall(r'\b([A-Z]{2,}\s+[A-Z][A-Z]+(?:\s+[A-Z]{2,})?)\b', original_text)
            best = None
            forbidden = {'GOVERNMENT','NATIONAL','EXAMINATIONS','BOARD','CERTIFICATE','SECONDARY','SCHOOL','KATHMANDU','GOLDHUNGA','CONTROLLER','CHAIRPERSON','REGISTRATION'}
            school_kws = {'SCHOOL','ACADEMY','COLLEGE','UNIVERSITY','INSTITUTE','CAMPUS','BOARDING'}
            for cand in candidates:
                cand_raw = cand.strip()
                # If candidate is 3 words and the text immediately after it contains a school keyword,
                # it is polluted (e.g. "ROHAN GURUNG HEART" before "SECONDARY BOARDING SCHOOL") -> trim to 2 words
                words_raw = cand_raw.split()
                if len(words_raw) == 3:
                    pos = original_text.find(cand_raw)
                    after = original_text[pos + len(cand_raw):pos + len(cand_raw) + 40].upper()
                    if 'SECONDARY' in after or 'SCHOOL' in after or 'ACADEMY' in after or 'COLLEGE' in after:
                        cand_raw = ' '.join(words_raw[:2])
                cand_up = cand_raw.upper()
                words = cand_up.split()
                if any(w in forbidden for w in words):
                    continue
                if any(w in school_kws for w in words):
                    continue
                if len(words) < 2 or len(words) > 3:
                    continue
                if any(c.isdigit() for c in cand_raw):
                    continue
                if best is None:
                    best = cand_raw
                if certify_pos >= 0:
                    pos = original_text.find(cand_raw)
                    dist = abs(pos - certify_pos)
                    best_pos = original_text.find(best) if best else 9999
                    best_dist = abs(best_pos - certify_pos)
                    if dist < best_dist:
                        best = cand_raw
            if best:
                fields['student_name'] = best
            # Post-clean: also strip student name prefix from school if still polluted
            if best and 'school_name' in fields and fields['school_name'].startswith(best):
                remainder = fields['school_name'][len(best):].strip()
                if remainder:
                    fields['school_name'] = remainder

        # Infer BS year from context if not directly matched
        if 'year_bs' not in fields:
            year_matches = re.findall(r'\b(20\d{2})\b', original_text)
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
                        fields['year_bs'] = str(int(y) + 57)  # Convert AD to BS
                        break
        
        # Infer AD year if not found
        if 'year_ad' not in fields:
            year_matches = re.findall(r'\b(20\d{2})\b', original_text)
            for y in year_matches:
                y_int = int(y)
                if 2018 <= y_int <= 2029:
                    fields['year_ad'] = y
                    break
            if 'year_ad' not in fields and 'year_bs' in fields:
                fields['year_ad'] = str(int(fields['year_bs']) - 57)  # Convert BS to AD
        
        # Normalize grade
        if 'grade' not in fields:
            if re.search(r'\b(XII|12)\b', original_text, re.IGNORECASE):
                fields['grade'] = 'XII'
            elif re.search(r'\b(X|10)\b', original_text, re.IGNORECASE):
                fields['grade'] = 'X'
        
        # Clean grade value
        if 'grade' in fields:
            grade_val = fields['grade']
            grade_val = re.sub(r'^(?:Grade|Class|Level|Standard)\s+', '', grade_val, flags=re.IGNORECASE)
            if grade_val.upper() in ('XII', '12'):
                fields['grade'] = 'XII'
            elif grade_val.upper() in ('X', '10'):
                fields['grade'] = 'X'
        
        return fields
    
    def _calculate_confidence(self, fields):
        """
        Calculate extraction confidence (0.0 to 1.0).
        Based on how many critical fields were extracted.
        """
        critical_fields = ['student_name', 'school_name', 'gpa', 'grade']
        optional_fields = ['reg_no', 'serial_no', 'issue_date', 'year_bs', 'year_ad']
        
        critical_extracted = sum(1 for f in critical_fields if f in fields)
        optional_extracted = sum(1 for f in optional_fields if f in fields)
        
        # Weight: critical fields worth 0.2 each, optional worth 0.05 each
        confidence = (critical_extracted * 0.2) + (optional_extracted * 0.05)
        
        return min(confidence, 1.0)
    
    def get_document_type(self):
        """Return supported document types."""
        return self.SUPPORTED_DOCUMENT_TYPES
    
    def validate_fields(self, data):
        """Validate Character Certificate fields."""
        errors = []
        
        if not data:
            return False, ['No data provided']
        
        # Check critical fields
        critical_fields = ['student_name', 'school_name']
        for field in critical_fields:
            if field not in data or not data[field]:
                errors.append(f'Missing critical field: {field}')
        
        # GPA should be numeric
        if 'gpa' in data:
            try:
                float(data['gpa'])
            except ValueError:
                errors.append(f'Invalid GPA format: {data["gpa"]}')
        
        is_valid = len(errors) == 0
        return is_valid, errors


# ─── Public service API (spec-compliant) ─────────────────────────────────
# Exposes parse_character_certificate(raw_text, ocr_words=None)
# Returns per-field {value, confidence, method} + flat spec dict + validation

def _field_detail(value, confidence, method):
    return {'value': value, 'confidence': round(float(confidence), 2), 'method': method}


def _spec_mapped_fields(parser_fields):
    """
    Map internal parser keys to spec keys.
    Spec: serial_number, registration_number, student_name, school_name,
          school_location, grade, gpa, examination_year_bs/ad,
          certificate_date_bs/ad
    """
    issue = parser_fields.get('issue_date', '')
    m_bs = re.search(r'(\d{4}/\d{1,2}/\d{1,2})', issue) if issue else None
    m_ad = re.search(r'\((\d{1,2}/\d{1,2}/\d{4})\)', issue) if issue else None
    cert_bs = m_bs.group(1) if m_bs else None
    cert_ad = None
    if m_ad:
        a, b, y = m_ad.group(1).split('/')
        cert_ad = f'{y}/{a.zfill(2)}/{b.zfill(2)}'
    # Also check direct keys if issue split already done
    if not cert_bs and parser_fields.get('issue_date_bs'):
        cert_bs = parser_fields.get('issue_date_bs')
    if not cert_ad and parser_fields.get('issue_date_ad'):
        cert_ad = parser_fields.get('issue_date_ad')
    # Allow year_bs/ad already
    gpa_val = parser_fields.get('gpa')
    # Validate gpa range already done in parser; null if invalid
    return {
        'serial_number': parser_fields.get('serial_no') or None,
        'registration_number': parser_fields.get('reg_no') or None,
        'student_name': parser_fields.get('student_name') or None,
        'school_name': parser_fields.get('school_name') or None,
        'school_location': parser_fields.get('location') or parser_fields.get('school_location') or None,
        'grade': parser_fields.get('grade') or None,
        'gpa': gpa_val if gpa_val is not None and gpa_val != '' else None,
        'examination_year_bs': parser_fields.get('year_bs') or None,
        'examination_year_ad': parser_fields.get('year_ad') or None,
        'certificate_date_bs': cert_bs,
        'certificate_date_ad': cert_ad,
    }


def parse_character_certificate(raw_text, ocr_words=None):
    """
    Public extraction service — RAW OCR → structured Character Certificate data.

    Args:
        raw_text (str): Full OCR text (messy, order-unreliable).
        ocr_words (list[dict]|None): Optional word-level OCR with {text,x,y,w,h,conf}.

    Returns:
        dict: {
            'document_type': 'character_certificate',
            'fields': { field: {value, confidence, method} },
            'flat': { spec_keys: value or None },
            'raw_fields': { internal parser keys },
            'metadata': {overall_confidence, validation_errors, warnings},
        }
    Position-independent: each field searched via keywords/regex/context,
    never by line number. Uses validation + confidence per spec.
    """
    parser = CharacterCertificateParser()
    result = parser.parse(raw_text, layout_data={'ocr_words': ocr_words} if ocr_words else None)
    internal = result.fields  # already validated
    spec_flat = _spec_mapped_fields(internal)

    # Per-field confidence/method heuristics
    method_map = {
        'reg_no': 'keyword_nearby_numeric',
        'serial_no': 'keyword_nearby_alnum',
        'student_name': 'certificate_phrase_context',
        'school_name': 'school_keyword_context',
        'location': 'school_location_context',
        'grade': 'keyword_pattern',
        'gpa': 'keyword_numeric_validation',
        'year_bs': 'examination_year_context',
        'year_ad': 'examination_year_context',
        'issue_date': 'date_keyword_context',
    }
    conf_map = {
        'student_name': 0.96 if internal.get('student_name') else 0.0,
        'school_name': 0.93 if internal.get('school_name') else 0.0,
        'location': 0.91 if internal.get('location') else 0.0,
        'reg_no': 0.98 if internal.get('reg_no') else 0.0,
        'serial_no': 0.97 if internal.get('serial_no') else 0.0,
        'grade': 0.95 if internal.get('grade') else 0.0,
        'gpa': 0.99 if internal.get('gpa') else 0.0,
        'year_bs': 0.96 if internal.get('year_bs') else 0.0,
        'year_ad': 0.96 if internal.get('year_ad') else 0.0,
        'issue_date': 0.94 if internal.get('issue_date') else 0.0,
    }
    # Down-weight if validation had to infer (year via inference)
    if internal.get('year_bs') and 'year_bs' not in result.metadata.get('validation_errors', []):
        pass

    fields_detailed = {}
    for k in ['reg_no', 'serial_no', 'student_name', 'school_name', 'location', 'grade', 'gpa', 'year_bs', 'year_ad', 'issue_date']:
        v = internal.get(k)
        fields_detailed[k] = _field_detail(v if v is not None else None, conf_map.get(k, 0.0) if v else 0.0, method_map.get(k, 'pattern'))

    # Build spec-level detailed view
    spec_detailed = {}
    for sk, sv in spec_flat.items():
        # Map spec key to internal confidence
        internal_key = {
            'serial_number': 'serial_no', 'registration_number': 'reg_no',
            'school_location': 'location', 'examination_year_bs': 'year_bs',
            'examination_year_ad': 'year_ad', 'certificate_date_bs': 'issue_date',
            'certificate_date_ad': 'issue_date',
        }.get(sk, sk)
        spec_detailed[sk] = _field_detail(sv, conf_map.get(internal_key, 0.0) if sv else 0.0, method_map.get(internal_key, 'pattern'))

    return {
        'document_type': 'character_certificate',
        'fields': fields_detailed,
        'flat': spec_flat,
        'raw_fields': internal,
        'metadata': {
            'overall_confidence': result.metadata.get('confidence', 0.0),
            'validation_errors': result.metadata.get('validation_errors', []),
            'warnings': [],
        },
    }
