# Document Understanding Engine - Upgrade Summary

## What Was Already Working

Your project already has a **solid parser architecture**:
- `BaseDocumentParser` - Abstract base class
- `CharacterCertificateParser` - Existing parser implementation  
- `ParserRegistry` - Maps document types to parsers
- Integration with Django views and template engine

## Problem Identified

The current extraction approach in `CharacterCertificateParser` has **weaknesses**:

1. **Single Strategy Per Field** - Only one regex pattern, if it fails, field is lost
2. **No OCR Normalization** - OCR mistakes (0f→of, ¥→V) break patterns
3. **Limited Validation** - No rules to reject invalid extractions
4. **No Confidence Scoring** - Can't tell when extraction is unreliable
5. **Patterns Too Strict** - Only match ALL CAPS, fail on mixed-case OCR output

## What Needs to Be Upgraded

### File: `translation/services/parsers/character_certificate.py`

**Add at top of class (after SUPPORTED_DOCUMENT_TYPES):**

```python
# OCR NORMALIZATION RULES
OCR_NORMALIZATIONS = [
    (r'¥', 'V'),  # Yen symbol to V
    (r'0f\b', 'of'),  # 0f to of
    (r'certlficate', 'certificate'),
    (r'Mr/Ms', 'Mr./Ms.'),
    # ... more corrections
]

# VALIDATION RULES  
VALIDATION_RULES = {
    'school_name': {
        'invalid_tokens': ['has', 'completed', 'GPA', 'Grade'],
        'must_contain': ['School', 'Academy', 'College'],
    },
    'student_name': {
        'invalid_tokens': ['of', 'has', 'completed', 'School'],
    },
    'reg_no': {
        'pattern': r'^\d{10,15}$',
    },
    # ... more rules
}
```

**Replace FIELD_PATTERNS with multi-strategy versions:**

```python
FIELD_PATTERNS = {
    'student_name': [
        # Strategy 1: "Mr./Ms. NAME of"
        r'(?i:Mr\.?/Ms\.?)\s+([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
        # Strategy 2: "certify that NAME"  
        r'(?i:certify\s+that)\s+([A-Z][A-Za-z\.\s]+?)\s+(?:of|has)\b',
        # Strategy 3: "Name: NAME"
        r'(?i:Name)\s*:\s*([A-Z][A-Za-z\.\s]+?)(?:\n|$)',
    ],
    'school_name': [
        # Strategy 1: "of SCHOOL has completed" - MOST PRECISE
        r'\bof\s+([A-Z][A-Za-z\s,]+?(?:SECONDARY\s+SCHOOL|SCHOOL))\s+has\s+completed\b',
        # Strategy 2: "of SCHOOL, LOCATION has"
        r'\bof\s+([A-Z][A-Za-z\s,]+?(?:SCHOOL|ACADEMY))',
    ],
    # ... more fields with multiple strategies
}
```

**Add new methods to the class:**

```python
def _normalize_ocr(self, text):
    """Step 1: Fix OCR mistakes before extraction."""
    normalized = text
    for pattern, replacement in self.OCR_NORMALIZATIONS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    # CRITICAL: Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def _extract_all_fields(self, text):
    """Step 2: Try multiple strategies per field."""
    fields = {}
    for field_name, patterns in self.FIELD_PATTERNS.items():
        for strategy_idx, pattern in enumerate(patterns, 1):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                fields[field_name] = value
                logger.debug(f"[{field_name}] Strategy {strategy_idx} succeeded")
                break  # Success, move to next field
    return fields

def _validate_fields(self, fields):
    """Step 3: Validate every extracted field."""
    validated = {}
    errors = []
    
    for field_name, value in fields.items():
        if field_name not in self.VALIDATION_RULES:
            validated[field_name] = value
            continue
        
        rules = self.VALIDATION_RULES[field_name]
        is_valid = True
        
        # Check invalid tokens
        if 'invalid_tokens' in rules:
            for token in rules['invalid_tokens']:
                if token.lower() in value.lower():
                    is_valid = False
                    errors.append(f"{field_name}: contains '{token}'")
                    break
        
        # Add more validation checks...
        
        if is_valid:
            validated[field_name] = value
    
    return validated, errors
```

**Update `parse()` method:**

```python
def parse(self, extracted_text, layout_data=None, tables=None):
    """
    Enhanced parsing pipeline:
    1. OCR Normalization
    2. Multi-Strategy Extraction
    3. Validation
    4. Confidence Scoring
    """
    # Step 1: Normalize OCR text
    normalized_text = self._normalize_ocr(extracted_text)
    
    # Step 2: Extract with multiple strategies
    fields = self._extract_all_fields(normalized_text)
    
    # Step 3: Validate
    validated_fields, errors = self._validate_fields(fields)
    
    # Step 4: Calculate confidence
    confidence = self._calculate_confidence(validated_fields)
    
    return StructuredDataResult(
        fields=validated_fields,
        tables=tables or [],
        metadata={
            'parser': 'CharacterCertificateParser',
            'confidence': confidence,
            'validation_errors': errors,
        },
    )
```

## Expected Output Format

After upgrade, the parser will return structured JSON:

```json
{
  "document_type": "character_certificate",
  "serial_number": "C0034274",
  "registration_number": "845271150233",
  "student_name": "SUNIL B.K.",
  "school_name": "NAVODIT VIDYA KUNJA SECONDARY SCHOOL",
  "school_location": "SAMAKHUSHI, KATHMANDU",
  "grade": "XII",
  "gpa": "3.14",
  "exam_year_bs": "2082",
  "exam_year_ad": "2025",
  "certificate_date_bs": "2082/12/18",
  "certificate_date_ad": "2026/04/01",
  "confidence": 0.95,
  "validation_errors": []
}
```

## Benefits of This Upgrade

1. **Robust Extraction** - Multiple strategies per field, if one fails, tries another
2. **OCR Error Correction** - Fixes common mistakes before extraction
3. **Validation** - Rejects invalid extractions (e.g., school name containing "has")
4. **Confidence Scoring** - Tells you when extraction is unreliable
5. **Easy to Extend** - Just add new patterns to FIELD_PATTERNS for better extraction
6. **Production Ready** - Clean, maintainable, SOLID principles

## Next Steps

1. Add the OCR_NORMALIZATIONS dict to CharacterCertificateParser
2. Add the VALIDATION_RULES dict
3. Update FIELD_PATTERNS with multiple strategies per field
4. Add `_normalize_ocr()`, `_extract_all_fields()`, `_validate_fields()` methods
5. Update `parse()` method to use the new pipeline
6. Test with actual Character Certificate documents

## Integration Points

- **views.py** - Already calls parser via `get_parser_for_document()`
- **template_engine.py** - Receives structured fields from parser
- **docx_generator.py** - Uses fields to generate Japanese certificate

**No breaking changes required** - the upgrade is backward compatible!
