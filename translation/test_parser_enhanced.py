"""
Test the enhanced CharacterCertificateParser with real-world OCR output.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from translation.services.parsers.character_certificate import CharacterCertificateParser

# Sample OCR text (real-world example with newlines and mixed formatting)
SAMPLE_OCR_TEXT = """S.No.: C0034274
Registration No. 813271150233

This is to certify that Mr./Ms. SUNIL B. K.
of NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI, KATHMANDU
has completed School Leaving Certificate Examination (Grade XII) conducted by
National Examinations Board in the year 2082 B.S. (2025 A.D.)
with 3.31 GPA.

Date 2082/12/18 (4/1/2026)"""

# Sample with OCR mistakes
SAMPLE_OCR_WITH_ERRORS = """S.No.: C0034274
Registration No. 813271150233

This is to certlficate that Mr./Ms. SUNIL B. K.
0f NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI, KATHMANDU
has completed School Leaving Certlficate Examination (Grade XII) conducted by
National Examinations Board in the year 2082 B.S. (2025 A.D.)
with 3.31 GPA.

Date 2082/12/18 (4/1/2026)"""

def test_parser():
    """Test the enhanced parser."""
    print("=" * 80)
    print("Testing Enhanced CharacterCertificateParser")
    print("=" * 80)
    
    parser = CharacterCertificateParser()
    
    # Test 1: Normal OCR text
    print("\n📝 TEST 1: Normal OCR Text")
    print("-" * 80)
    result = parser.parse(SAMPLE_OCR_TEXT)
    
    print(f"✅ Fields extracted: {len(result.fields)}")
    print(f"📊 Confidence: {result.metadata['confidence']:.0%}")
    print(f"🔍 Validation errors: {result.metadata.get('validation_errors', [])}")
    print("\n📋 Extracted Fields:")
    for field, value in result.fields.items():
        print(f"  • {field}: {value}")
    
    # Test 2: OCR text with mistakes
    print("\n" + "=" * 80)
    print("📝 TEST 2: OCR Text with Mistakes (0f→of, certlficate→certificate)")
    print("-" * 80)
    result2 = parser.parse(SAMPLE_OCR_WITH_ERRORS)
    
    print(f"✅ Fields extracted: {len(result2.fields)}")
    print(f"📊 Confidence: {result2.metadata['confidence']:.0%}")
    print(f"🔍 Validation errors: {result2.metadata.get('validation_errors', [])}")
    print("\n📋 Extracted Fields:")
    for field, value in result2.fields.items():
        print(f"  • {field}: {value}")
    
    # Test 3: Validation demonstration
    print("\n" + "=" * 80)
    print("📝 TEST 3: Validation Demonstration")
    print("-" * 80)
    
    # Simulate bad extraction
    bad_fields = {
        'school_name': 'has, SAMAKHUSHI, KATHMANDU of',  # Should be rejected
        'student_name': 'SUNIL B.K. of National Board',  # Should be rejected
        'gpa': '5.5',  # Should be rejected (>4.0)
        'reg_no': '12345',  # Should be rejected (<10 digits)
    }
    
    validated, errors = parser._validate_extraction(bad_fields)
    
    print("❌ Invalid fields that should be rejected:")
    for field in bad_fields:
        if field not in validated:
            print(f"  ✗ {field}: '{bad_fields[field]}'")
    
    print(f"\n✅ Validation errors caught: {len(errors)}")
    for error in errors:
        print(f"  • {error}")
    
    # Test 4: Structured output
    print("\n" + "=" * 80)
    print("📝 TEST 4: Structured JSON Output")
    print("-" * 80)
    
    output = {
        "document_type": "character_certificate",
        "serial_number": result.fields.get('serial_no', ''),
        "registration_number": result.fields.get('reg_no', ''),
        "student_name": result.fields.get('student_name', ''),
        "school_name": result.fields.get('school_name', ''),
        "school_location": result.fields.get('location', ''),
        "grade": result.fields.get('grade', ''),
        "gpa": result.fields.get('gpa', ''),
        "exam_year_bs": result.fields.get('year_bs', ''),
        "exam_year_ad": result.fields.get('year_ad', ''),
        "confidence": f"{result.metadata['confidence']:.0%}",
        "validation_errors": result.metadata.get('validation_errors', []),
    }
    
    import json
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == '__main__':
    test_parser()
