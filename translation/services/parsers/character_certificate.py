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
        (r'0\b([a-z])', 'O\1'),  # 0 to O when followed by letter
        (r'\bl\b', 'I'),  # lowercase l to I when standalone
        
        # Word corrections
        (r'certlficate', 'certificate'),
        (r'certiflcate', 'certificate'),
        (r'Examlinatlon', 'Examination'),
        (r'Natl0nal', 'National'),
        (r'Natl0nal', 'National'),
        (r'B\.?S\.', 'B.S.'),
        (r'A\.?D\.', 'A.D.'),
        
        # Mr./Ms. fixes
        (r'Mr\./Ms', 'Mr./Ms.'),
        (r'Mr/Ms', 'Mr./Ms.'),
        (r'Mr\.?', 'Mr.'),
        (r'Ms\.?', 'Ms.'),
        
        # Spacing fixes
        (r'\s+', ' '),  # Normalize multiple spaces
        (r'\.\s*([A-Z])', '. \1'),  # Ensure space after periods
        (r'\s*,\s*', ', '),  # Normalize comma spacing
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
            # Strategy 1: "Mr./Ms. NAME of" or "Mr./Ms. NAME has"
            r'(?i:Mr\.?/Ms\.?|Mr\.?|Ms\.?|Shri|Shreemati|Kumar|Kumari)\s+([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
            # Strategy 2: "certify that NAME of/has"
            r'(?i:certify\s+that)\s+(?i:Mr\.?/Ms\.?|Mr\.?|Ms\.?)?\s*([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
            # Strategy 3: "Name: NAME"
            r'(?i:Name|Student[\u2019\']?s\s*Name)\s*[:\-\u2013\u2014]?\s*([A-Z][A-Za-z\.\s]+?)(?:\s|$)',
        ],
        'school_name': [
            # Strategy 1: "of SCHOOL NAME has completed" - MOST PRECISE
            r'\bof\s+([A-Z][A-Za-z\s,]+?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS))\s+has\s+completed\b',
            # Strategy 2: "of SCHOOL, LOCATION has"
            r'\bof\s+([A-Z][A-Za-z\s,]+?(?:SECONDARY\s+SCHOOL|SCHOOL|ACADEMY|COLLEGE|UNIVERSITY|INSTITUTE|CAMPUS))',
            # Strategy 3: Keyword-based extraction
            r'([A-Z][A-Za-z\s,]+?(?:School|Academy|College|University|Institute|Campus|Secondary\s+School)\b)',
        ],
        'location': [
            # Strategy 1: After school name, before "has"
            r'(?:School|Academy|College|Institute|Campus)\s*,\s*([A-Z][A-Za-z\s,]+?)\s+has\b',
            # Strategy 2: School followed by comma and location
            r'(?:School|Academy|College)\s*,\s*([A-Z][A-Za-z,\s]+?)(?:\s+has|\s+completed|$)',
        ],
        'gpa': [
            r'(?:GPA|Grade\s*Point\s*Average|g\.?p\.?a\.?|G\.?P\.?A\.?)\s*[:\-–—]?\s*(\d+\.?\d*)',
            r'(\d+\.\d+)\s*(?:GPA|gpa|Grade\s*Point\s*Average)',
            r'obtained\s*(?:a|an)?\s*(?:grade\s+point\s+average\s+of\s+)?(\d+\.?\d*)',
        ],
        'marks': [
            r'(?:Marks|Marks\s+Obtained|Total\s+Marks|Percentage)\s*[:\-]?\s*(\d+[\.,]?\d*(?:\s*[/:]\s*\d+[\.,]?\d*)?)',
            r'(\d+[\.,]?\d*)\s*(?:marks|percent)',
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
        ],
        'serial_no': [
            r'(?:Serial\s*(?:No\.?|Number)|Sr\.?\s*No\.?|S\.?\s*No\.?)\s*[:\-–—]?\s*(\S+)',
        ],
        'issue_date': [
            r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*(\d{4}/\d{1,2}/\d{1,2}\s*\(\d{1,2}/\d{1,2}/\d{4}\))',
            r'(?:Issue\s*Date|Date\s*of\s*Issue|Issued\s*Date|Date)\s*[:\-–—]?\s*(\d{4}[-/–—]\d{1,2}[-/–—]\d{1,2})',
            r'(?:issued\s+on|dated)\s+(\d{4}[-/–—]\d{1,2}[-/–—]\d{1,2}|[A-Z][a-z]+\s+\d{1,2},?\s*\d{4})',
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
        
        # Fix common OCR character mistakes
        ocr_fixes = [
            (r'¥', 'V'),  # Yen symbol to V
            (r'0f\b', 'of'),  # 0f to of  
            (r'certlficate', 'certificate'),
            (r'certiflcate', 'certificate'),
            (r'Examlinatlon', 'Examination'),
            (r'Mr/Ms', 'Mr./Ms.'),
        ]
        
        for pattern, replacement in ocr_fixes:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # CRITICAL: Normalize whitespace - replace newlines/multiple spaces with single space
        # This makes regex matching MUCH more reliable for multi-line OCR output
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        logger.debug(f"OCR normalized: {len(text)} -> {len(normalized)} chars")
        return normalized
    
    def _validate_extraction(self, fields):
        """
        Step 4: Validate extracted fields and reject invalid ones.
        
        Returns:
            tuple: (validated_fields, list_of_errors)
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
            
            # Check invalid tokens
            if 'invalid_tokens' in rules:
                for token in rules['invalid_tokens']:
                    if token.lower() in value.lower():
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
            # Clean up: remove trailing text after school name
            school_val = re.split(r'(?:\n|\s+has|\s+completed|\s+who)', school_val, maxsplit=1)[0].strip()
            
            # Check if there's a comma followed by location info
            parts = re.split(r',\s*', school_val, maxsplit=1)
            if len(parts) == 2:
                school_part, loc_part = parts
                # Verify the second part looks like a location (not "School" etc.)
                if not re.search(r'(?:School|Academy|College|Institute|Campus)', loc_part, re.IGNORECASE):
                    fields['school_name'] = school_part.strip()
                    fields['location'] = loc_part.strip()
                else:
                    fields['school_name'] = school_val
            else:
                fields['school_name'] = school_val
        
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
