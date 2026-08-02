"""
Test script for NEB Character Certificate translation.
Tests the template engine with the example document.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from translation.services.template_engine import TemplateTranslationEngine

# Example English text from the NEB Character Certificate
EXAMPLE_TEXT = """
S. No.: C0034274
Registration No. 813271150233

GOVERNMENT OF NEPAL
NATIONAL EXAMINATIONS BOARD

CERTIFICATE

This is to certify that Mr./Ms. SUNIL B. K.
of NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI, KATHMANDU
has completed School Leaving Certificate Examination (Grade XII) conducted by
National Examinations Board in the year 2082 B.S. (2025 A.D.)
with 3.31 GPA.

Date 2082/12/18 (4/1/2026)
"""

def test_character_certificate_translation():
    """Test the template translation engine with NEB Character Certificate."""
    
    print("=" * 80)
    print("NEB Character Certificate Translation Test")
    print("=" * 80)
    print()
    
    # Initialize engine
    engine = TemplateTranslationEngine()
    
    # Step 1: Detect document type
    print("Step 1: Document Detection")
    print("-" * 80)
    is_detected = engine.detect(EXAMPLE_TEXT, document_type_name='Character Certificate')
    print(f"✓ Detected as Character Certificate: {is_detected}")
    print(f"✓ Confidence: {engine.confidence:.2%}")
    print()
    
    # Step 2: Extract fields
    print("Step 2: Field Extraction")
    print("-" * 80)
    fields = engine.extract_fields(EXAMPLE_TEXT)
    
    for field_name, value in fields.items():
        print(f"✓ {field_name}: {value}")
    print()
    
    # Step 3: Get remaining unmatched text
    print("Step 3: Unmatched Text Analysis")
    print("-" * 80)
    remaining = engine.get_remaining_unmatched_text(EXAMPLE_TEXT)
    if remaining:
        print(f"Remaining text: {remaining[:100]}...")
    else:
        print("✓ All text matched to fields")
    print()
    
    # Step 4: Generate Japanese translation
    print("Step 4: Japanese Translation Generation")
    print("=" * 80)
    result = engine.translate(EXAMPLE_TEXT, document_type_name='Character Certificate')
    
    if result['result']:
        print("✓ Translation successful!")
        print(f"✓ Method: {result['method']}")
        print(f"✓ Confidence: {result['confidence']:.2%}")
        print(f"✓ Fields extracted: {list(result['fields'].keys())}")
        print()
        print("Japanese Output:")
        print("=" * 80)
        print(result['result'])
        print("=" * 80)
    else:
        print("✗ Translation failed")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Method: {result['method']}")
    
    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == '__main__':
    test_character_certificate_translation()
