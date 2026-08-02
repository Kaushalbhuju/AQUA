# Document Translation with Japanese Templates - User Guide

## Overview

Your Django translation app **already has a sophisticated template-based translation system** that:

1. ✅ Extracts text from uploaded documents (PDFs, images, scanned docs)
2. ✅ Automatically detects document type (NEB Character Certificate, Bank Statement, etc.)
3. ✅ Applies Japanese templates with proper field mapping
4. ✅ Preserves specific fields untranslated (S.N., Reg. No., GPA, School Name, etc.)
5. ✅ Generates professional Japanese translations

## Supported Document Types

The system currently supports templates for:

1. **Character Certificate** (NEB) - ✅ Fully implemented
2. **Transcript** - Template ready
3. **Academic Certificate** - Template ready
4. **Bank Statement** - Template ready
5. **Bank Balance Certificate** - Template ready
6. **SOP (Statement of Purpose)** - Template ready
7. **Sponsor Letter** - Template ready
8. **Way of Payment** - Template ready
9. **VDC/Ward Recommendation Letter** - Template ready
10. **Early Admission Request** - Template ready
11. **Early Japanese Language Certificate** - Template ready
12. **Late Issue of NEB Certificate** - Template ready

## How to Use the System

### Step 1: Upload the ORIGINAL English Document

**Important:** Upload the **English version** of your document, NOT the Japanese translation.

For example, for a NEB Character Certificate, upload a document containing:
```
This is to certify that Mr. B K SUNIL of ABC School has completed
the School Leaving Certificate Examination conducted by National 
Examinations Board in 2075 BS (2018 AD) with GPA 3.45.

Registration No: 123456
Symbol No: 789012

During his study, his character was honest and sincere.

Issue Date: 2019-05-15
```

### Step 2: System Auto-Processes

The system automatically:

1. **Extracts text** using enhanced OCR (with preprocessing, confidence scoring)
2. **Detects document type** as "Character Certificate"
3. **Applies Japanese template** from `template_engine.py`
4. **Preserves fields** like Reg. No., Symbol No., GPA, School Name
5. **Generates Japanese translation**

### Step 3: Review the Output

The system generates professional Japanese output:

```
これは、ABC SchoolのB K SUNIL氏が、ネパール暦2075年（西暦2018年）に
国家試験委員会により実施された卒業証明書試験（グレード12）を3.45GPAで
修了したことを証明するものです。

登録番号: 123456
記号番号: 789012

在学中、B K SUNIL氏の性格は誠実かつ真面目で、規律正しい態度を示していました。

発行日: 2019-05-15
```

## Field Preservation Rules

The system automatically **preserves these fields in English**:

### Character Certificate
- ✅ S.N. (Serial Number)
- ✅ Registration Number / Reg. No.
- ✅ Symbol Number / Symbol No.
- ✅ School Name
- ✅ Student Name (Mr./Ms. format)
- ✅ GPA
- ✅ Marks

### Bank Documents
- ✅ Account Numbers
- ✅ Transaction IDs
- ✅ Currency amounts (NPR, USD, JPY)
- ✅ Dates
- ✅ Bank/Branch names

### Academic Documents
- ✅ Subject codes
- ✅ Grade/Marks
- ✅ Registration numbers
- ✅ Institution names

## NEB Character Certificate Template Details

### Template Structure (from `template_engine.py`)

```python
CHARACTER_CERTIFICATE_TEMPLATES = [
    {
        'id': 'certify_clause',
        'template': 'これは、{school_name}の{student_name}氏が、',
    },
    {
        'id': 'examination_clause',
        'template': 'ネパール暦{year_bs}年（西暦{year_ad}年）に国家試験委員会により実施された、',
    },
    {
        'id': 'exam_name',
        'template': '卒業証明書試験（グレード{grade}）を',
    },
    {
        'id': 'gpa_clause',
        'template': '{gpa}GPAで修了したことを証明するものです。',
    },
    {
        'id': 'registration_info',
        'template': '\n登録番号: {reg_no}\n記号番号: {symbol_no}',
    },
    {
        'id': 'character_clause',
        'template': '\n在学中、{student_name}氏の性格は誠実かつ真面目で、規律正しい態度を示していました。',
    },
    {
        'id': 'issue_clause',
        'template': '\n発行日: {issue_date}',
    },
]
```

### Field Extraction Patterns

The system uses regex to extract:
- **School Name**: `[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:School|Academy|College|University)`
- **Student Name**: `(?:Mr\.?|Ms\.?|Shri|Shreemati)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2}`
- **Registration No**: `Reg\.?\s*No\.?\s*[:\-–—]?\s*([A-Za-z0-9]+[-–—]?\d+)`
- **Symbol No**: `Symbol\s*(?:No\.?|Number)\s*[:\-–—]?\s*(\S+)`
- **GPA**: `\d+\.?\d*\s*(?:GPA|gpa)`
- **Year**: `(\d{4})\s*(?:BS|AD|B\.S\.|A\.D\.)`
- **Issue Date**: `(?:Issue\s*Date|Date\s*of\s*Issue)\s*[:\-–—]?\s*(\d{4}[-–—]\d{1,2}[-–—]\d{1,2})`

## Using the System via Django Admin

### 1. Upload Document
1. Go to Translation Dashboard
2. Click "Upload Document"
3. Select your English PDF/image
4. Set file type:
   - **PDF** (for digital PDFs with selectable text)
   - **Image** (for JPG/PNG photos)
   - **Scanned PDF** (for scanned documents)
5. Document Type: Select "Auto-detect" or choose manually
6. Click Upload

### 2. Extract Text
1. System will show extraction progress
2. Click "Extract Text"
3. Enhanced OCR processes with:
   - Image preprocessing (denoising, deskewing, contrast)
   - Confidence scoring
   - Quality metrics
4. View extracted English text

### 3. Translate
1. Click "Translate"
2. System applies template-based translation
3. Japanese output appears with:
   - Proper template structure
   - Preserved fields (Reg. No., GPA, etc.)
   - Professional formatting

### 4. Review & Edit
1. Use side-by-side review screen
2. Edit Japanese translation if needed
3. Option to update Translation Memory
4. Mark as completed

### 5. Download
Options:
- **DOCX**: Word document with Japanese translation
- **Bilingual PDF**: Original layout with Japanese text overlaid

## Adding New Document Templates

To add templates for new document types:

### 1. Define Template Structure

Edit `translation/services/template_engine.py`:

```python
NEW_DOCUMENT_TEMPLATES = [
    {
        'id': 'section_name',
        'keywords': ['keyword1', 'keyword2'],  # For detection
        'priority': 1,
        'template': 'Japanese template with {field_name} placeholders',
    },
    # ... more sections
]
```

### 2. Add Field Extraction Patterns

```python
NEW_FIELD_PATTERNS = {
    'field_name': [
        r'regex pattern to extract field',
    ],
}
```

### 3. Register the Engine

```python
REGISTERED_ENGINES = {
    'Character Certificate': TemplateTranslationEngine,
    'New Document Type': NewTemplateEngine,  # Add here
}
```

### 4. Add to Document Rules

Edit `translation/services/translator.py`:

```python
DOCUMENT_RULES = {
    'New Document Type': {
        'keep_patterns': [
            r'patterns to keep in English',
        ],
        'translate_all': True/False,
    },
}
```

## Example Workflow: NEB Character Certificate

### Input (English PDF)
```
This is to certify that Mr. B K SUNIL of Sunrise Secondary School
has successfully completed the School Leaving Certificate Examination
(Grade XII) conducted by National Examinations Board in 2075 BS (2018 AD)
with GPA 3.45.

Registration No: NEB-123456
Symbol No: SYM-789012

During his study period, his character and conduct were satisfactory.
He was found to be honest, sincere, and hardworking.

Issue Date: 2019-06-20
```

### System Processing
1. **Detects**: "Character Certificate" (keywords matched)
2. **Extracts fields**:
   - student_name: "B K SUNIL"
   - school_name: "Sunrise Secondary School"
   - year_bs: "2075"
   - year_ad: "2018"
   - grade: "XII"
   - gpa: "3.45"
   - reg_no: "NEB-123456"
   - symbol_no: "SYM-789012"
   - issue_date: "2019-06-20"
3. **Applies template**: Maps fields to Japanese template
4. **Preserves**: Reg. No., Symbol No., GPA, names

### Output (Japanese)
```
これは、Sunrise Secondary SchoolのB K SUNIL氏が、ネパール暦2075年
（西暦2018年）に国家試験委員会により実施された卒業証明書試験
（グレードXII）を3.45GPAで修了したことを証明するものです。

登録番号: NEB-123456
記号番号: SYM-789012

在学中、B K SUNIL氏の性格は誠実かつ真面目で、規律正しい態度を
示していました。

発行日: 2019-06-20
```

## Troubleshooting

### Poor OCR Quality
- **Problem**: Garbled text extraction
- **Solution**: 
  - Use higher resolution scans (300+ DPI)
  - Ensure good contrast
  - System automatically applies preprocessing

### Wrong Document Type Detected
- **Problem**: System misidentifies document
- **Solution**: Manually select correct type in upload form

### Fields Not Preserved
- **Problem**: Names/numbers translated when they shouldn't be
- **Solution**: Check regex patterns in `translator.py` DOCUMENT_RULES

### Template Not Applied
- **Problem**: Generic translation instead of template
- **Solution**: Ensure document contains keywords matching template

## Key Files

- **Template Engine**: `translation/services/template_engine.py`
- **Translation Logic**: `translation/services/translator.py`
- **Document Detection**: `translation/services/detector.py`
- **Text Extraction**: `translation/services/extractor.py` (enhanced with OCR)
- **Views**: `translation/views.py`
- **Models**: `translation/models.py`

## Benefits of Your System

✅ **Professional Output**: Template-based translations match official consultancy quality
✅ **Field Preservation**: Important data stays in original form
✅ **Automatic Processing**: Minimal manual intervention required
✅ **Quality Metrics**: OCR confidence scoring and text quality assessment
✅ **Multi-format Support**: PDFs, images, scanned documents
✅ **Review System**: Side-by-side editing and approval workflow
✅ **Translation Memory**: Learns from corrections for better future translations

## Next Steps

1. **Test with real English documents** (not Japanese translations)
2. **Review template accuracy** and adjust patterns as needed
3. **Add more templates** for other document types as required
4. **Build Translation Memory** with correct translations
5. **Train staff** on the review and approval workflow

---

**Remember**: Always upload the **ORIGINAL English document**, not a pre-translated Japanese version. The system will handle the translation automatically using the templates!
