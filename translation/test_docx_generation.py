"""
Test script for Japanese Character Certificate DOCX generation.
Tests the template-based DOCX generation with proper layout.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from translation.services.docx_generator import generate_translated_docx
from translation.models import Document, DocumentType

# Mock document object for testing
class MockDocument:
    def __init__(self):
        self.title = "NEB Character Certificate - SUNIL B.K."
        self.document_type = type('obj', (object,), {'name': 'Character Certificate'})()
        self.extracted_text = """S. No.: C0034274
Registration No. 813271150233

This is to certify that Mr./Ms. SUNIL B. K.
of NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI, KATHMANDU
has completed School Leaving Certificate Examination (Grade XII) conducted by
National Examinations Board in the year 2082 B.S. (2025 A.D.)
with 3.31 GPA.

Date 2082/12/18 (4/1/2026)"""
        self.translated_text = """これは、【学校名】, SAMAKHUSHI, KATHMANDUの【氏名】氏が、国家試験委員会によって実施された卒業証明書試験（グレードXI）を3.31GPAで卒業したことを証明するものです。

S.N.: C0034274
登録番号: 813271150233

在学中、【氏名】氏の性格は誠実かつ真面目で、規律正しい態度を示していました。

発行日：ネパール暦2082年12月18日(西暦2026年04月01日)"""
        self.updated_at = type('obj', (object,), {'strftime': lambda self, fmt: '2026-01-04 10:00'})()

def test_docx_generation():
    """Test DOCX generation with Japanese certificate template."""
    
    print("=" * 80)
    print("Japanese Character Certificate DOCX Generation Test")
    print("=" * 80)
    print()
    
    # Create mock document
    doc = MockDocument()
    
    print("Step 1: Generating DOCX with Japanese certificate template...")
    print("-" * 80)
    
    # Generate DOCX
    content_file = generate_translated_docx(doc)
    
    if content_file:
        print("✓ DOCX generation successful!")
        print(f"✓ Filename: {content_file.name}")
        print(f"✓ File size: {len(content_file.read())} bytes")
        
        # Save to test output
        output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, content_file.name)
        
        with open(output_path, 'wb') as f:
            f.write(content_file.read())
        
        print(f"✓ Saved to: {output_path}")
        print()
        print("Expected Layout:")
        print("-" * 80)
        print("シリアル番号：C0034274                                    登録番号：813271150233")
        print()
        print("                        ネパール政府")
        print()
        print("  シール    国家試験委員会")
        print("  (印)")
        print()
        print("                         証明書")
        print()
        print("これは、NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI,")
        print("KATHMANDUのSUNIL B. K.氏が、ネパール暦2082年（西暦2025年）に")
        print("国家試験委員会によって実施された卒業証明書試験（グレードXII）")
        print("を3.31GPAで卒業したことを証明するものです。")
        print()
        print("在学中、SUNIL B. K.氏の性格は誠実かつ真面目で、規律正しい態度を")
        print("示していました。")
        print()
        print("                                                 署名")
        print("                                                 委員長")
        print()
        print("発行日：ネパール暦2082年12月18日(西暦2026年04月01日)")
        print("=" * 80)
    else:
        print("✗ DOCX generation failed!")
    
    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == '__main__':
    test_docx_generation()
