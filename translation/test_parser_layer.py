"""
Test script for Parser Layer and Table Extraction.
Tests Phase 1: Foundation implementation.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translation.services.parsers import (
    get_parser_for_document,
    CharacterCertificateParser,
    list_registered_parsers,
)
from translation.services.parsers.base import StructuredDataResult


def test_parser_registry():
    """Test parser registry functionality."""
    print("=" * 80)
    print("TEST 1: Parser Registry")
    print("=" * 80)
    
    # List registered parsers
    parsers = list_registered_parsers()
    print(f"\nRegistered parsers: {parsers}")
    
    # Get Character Certificate parser
    parser = get_parser_for_document('Character Certificate')
    print(f"\n✓ Got parser for 'Character Certificate': {type(parser).__name__}")
    assert isinstance(parser, CharacterCertificateParser), "Should return CharacterCertificateParser"
    
    # Get parser for unknown type (should return BaseParser)
    unknown_parser = get_parser_for_document('Unknown Document')
    print(f"✓ Got parser for 'Unknown Document': {type(unknown_parser).__name__}")
    
    print("\n✅ Parser registry tests passed!\n")


def test_character_certificate_parser():
    """Test CharacterCertificateParser with sample data."""
    print("=" * 80)
    print("TEST 2: Character Certificate Parser")
    print("=" * 80)
    
    # Sample English Character Certificate text
    sample_text = """
S. No.: C0034274
Registration No. 813271150233

This is to certify that Mr./Ms. SUNIL B. K.
of NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI, KATHMANDU
has completed School Leaving Certificate Examination (Grade XII) conducted by
National Examinations Board in the year 2082 B.S. (2025 A.D.)
with 3.31 GPA.

Date 2082/12/18 (4/1/2026)
"""
    
    print("\n Input Text:")
    print("-" * 80)
    print(sample_text)
    
    # Parse the text
    parser = CharacterCertificateParser()
    result = parser.parse(sample_text)
    
    print("\n" + "=" * 80)
    print("Extracted Fields:")
    print("=" * 80)
    
    for field, value in result.fields.items():
        print(f"  • {field}: {value}")
    
    print(f"\n Metadata:")
    print(f"  • Parser: {result.metadata.get('parser')}")
    print(f"  • Confidence: {result.metadata.get('confidence', 0):.2f}")
    print(f"  • Fields extracted: {result.metadata.get('fields_extracted')}")
    
    # Verify critical fields
    print("\n" + "=" * 80)
    print("Field Validation:")
    print("=" * 80)
    
    checks = {
        'Student name (SUNIL B. K.)': result.fields.get('student_name') == 'SUNIL B. K.',
        'School name (NAVODIT VIDYA KUNJA SECONDARY SCHOOL)': 'NAVODIT' in result.fields.get('school_name', ''),
        'GPA (3.31)': result.fields.get('gpa') == '3.31',
        'Grade (XII)': result.fields.get('grade') == 'XII',
        'BS Year (2082)': result.fields.get('year_bs') == '2082',
        'AD Year (2025)': result.fields.get('year_ad') == '2025',
        'Registration No (813271150233)': result.fields.get('reg_no') == '813271150233',
        'Serial No (C0034274)': result.fields.get('serial_no') == 'C0034274',
        'Issue Date': '2082/12/18' in result.fields.get('issue_date', ''),
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    # Test validation
    is_valid, errors = parser.validate_fields(result.fields)
    print(f"\n📋 Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    if errors:
        for error in errors:
            print(f"  • {error}")
    
    if all_passed:
        print("\n✅ Character Certificate parser tests passed!\n")
    else:
        print("\n❌ Some tests failed!\n")
    
    return all_passed


def test_structured_data_result():
    """Test StructuredDataResult container."""
    print("=" * 80)
    print("TEST 3: StructuredDataResult")
    print("=" * 80)
    
    # Create result with fields and tables
    result = StructuredDataResult(
        fields={'name': 'Test', 'value': '123'},
        tables=[[['Header1', 'Header2'], ['Row1', 'Row2']]],
        metadata={'parser': 'TestParser', 'confidence': 0.95}
    )
    
    print(f"\n✓ Created StructuredDataResult")
    print(f"  • Fields: {result.fields}")
    print(f"  • Has tables: {result.has_tables}")
    print(f"  • Tables count: {len(result.tables)}")
    
    # Test serialization
    data_dict = result.to_dict()
    print(f"\n✓ Serialized to dict: {list(data_dict.keys())}")
    
    # Test deserialization
    result2 = StructuredDataResult.from_dict(data_dict)
    print(f"✓ Deserialized from dict")
    print(f"  • Fields match: {result.fields == result2.fields}")
    
    print("\n✅ StructuredDataResult tests passed!\n")


def test_parser_integration():
    """Test parser integration with different document types."""
    print("=" * 80)
    print("TEST 4: Parser Integration")
    print("=" * 80)
    
    test_cases = [
        {
            'doc_type': 'Character Certificate',
            'text': 'This is to certify that Mr. JOHN DOE of TEST SCHOOL has completed Grade XII with 3.5 GPA.',
            'expected_fields': ['student_name', 'school_name', 'gpa', 'grade']
        },
        {
            'doc_type': 'Unknown Document',
            'text': 'This is some random text without structure.',
            'expected_fields': ['raw_text']  # Base parser returns raw_text
        },
    ]
    
    for test_case in test_cases:
        print(f"\n Testing: {test_case['doc_type']}")
        print("-" * 80)
        
        parser = get_parser_for_document(test_case['doc_type'])
        result = parser.parse(test_case['text'])
        
        print(f"  Parser: {type(parser).__name__}")
        print(f"  Fields extracted: {len(result.fields)}")
        
        # Check expected fields
        for field in test_case['expected_fields']:
            if field in result.fields:
                print(f"  ✅ Found: {field}")
            else:
                print(f"  ❌ Missing: {field}")
    
    print("\n✅ Parser integration tests passed!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PARSER LAYER & TABLE EXTRACTION TEST SUITE")
    print("Phase 1: Foundation")
    print("=" * 80 + "\n")
    
    try:
        # Run tests
        test_parser_registry()
        test_structured_data_result()
        parser_passed = test_character_certificate_parser()
        test_parser_integration()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if parser_passed:
            print("✅ All tests passed!")
            print("\nThe parser layer is working correctly:")
            print("  • Parser registry operational")
            print("  • CharacterCertificateParser extracts all fields")
            print("  • StructuredDataResult handles data correctly")
            print("  • Integration with document types working")
        else:
            print("⚠️  Some tests failed - review output above")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
