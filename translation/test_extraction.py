"""Test field extraction with improved patterns."""
import re

# Sample OCR text
text = """S.No.: C0034274
Registration No. 813271150233

This is to certify that Mr./Ms. SUNIL B. K.
of NAVODIT VIDYA KUNJA SECONDARY SCHOOL, SAMAKHUSHI, KATHMANDU
has completed School Leaving Certificate Examination (Grade XII) conducted by
National Examinations Board in the year 2082 B.S. (2025 A.D.)
with 3.31 GPA.

Date 2082/12/18 (4/1/2026)"""

print("="*80)
print("TESTING FIELD EXTRACTION")
print("="*80)

# Normalize text - replace newlines with spaces for easier matching
text_normalized = re.sub(r'\s+', ' ', text).strip()
print(f"\nNormalized text: {text_normalized[:100]}...")

# Extract student name
name_match = re.search(r'Mr\./Ms\.\s+([A-Z][A-Za-z\.\s]+?)\s+of\b', text_normalized, re.IGNORECASE)
student_name = name_match.group(1).strip().rstrip('.') if name_match else 'NOT FOUND'
print(f"\n✅ Student Name: {student_name}")

# Extract school name - use GREEDY matching to capture full school + location
school_match = re.search(r'\bof\s+([A-Z][A-Z\s,]+?)\s+has\s+completed\b', text_normalized, re.IGNORECASE)
if school_match:
    school_with_location = school_match.group(1).strip()
    # Split by comma to separate school from location
    parts = [p.strip() for p in school_with_location.split(',', 1)]
    school_name = parts[0]
    location = parts[1] if len(parts) > 1 else ''
    print(f"✅ School Name: {school_name}")
    print(f"✅ Location: {location}")
else:
    print("❌ School Name: NOT FOUND")
    location = ''

# Extract other fields
serial_match = re.search(r'S\.?\s*N?o\.?\s*:?\s*([A-Z]\d+)', text_normalized, re.IGNORECASE)
if not serial_match:
    serial_match = re.search(r'Serial\s*No\.?\s*:?\s*([A-Z0-9]+)', text_normalized, re.IGNORECASE)
serial_no = serial_match.group(1) if serial_match else 'NOT FOUND'
print(f"✅ Serial No: {serial_no}")

reg_match = re.search(r'Registration\s+No\.\s*(\d+)', text_normalized, re.IGNORECASE)
reg_no = reg_match.group(1) if reg_match else 'NOT FOUND'
print(f"✅ Registration No: {reg_no}")

gpa_match = re.search(r'(\d+\.\d+)\s*GPA', text_normalized, re.IGNORECASE)
gpa = gpa_match.group(1) if gpa_match else 'NOT FOUND'
print(f"✅ GPA: {gpa}")

grade_match = re.search(r'Grade\s+(XII|X|12|10)', text_normalized, re.IGNORECASE)
grade = grade_match.group(1).upper() if grade_match else 'NOT FOUND'
grade = 'XII' if grade in ('XII', '12') else grade
print(f"✅ Grade: {grade}")

year_bs_match = re.search(r'(\d{4})\s*B\.S', text_normalized, re.IGNORECASE)
year_bs = year_bs_match.group(1) if year_bs_match else 'NOT FOUND'
print(f"✅ Year BS: {year_bs}")

year_ad_match = re.search(r'(\d{4})\s*A\.D', text_normalized, re.IGNORECASE)
year_ad = year_ad_match.group(1) if year_ad_match else 'NOT FOUND'
print(f"✅ Year AD: {year_ad}")

print("\n" + "="*80)
print("GENERATED JAPANESE TEXT:")
print("="*80)

school_line = f"{school_name}, {location}" if location else school_name
japanese_text = f"これは、{school_line} の{student_name} 氏が、"
japanese_text += f"ネパール暦{year_bs}年（西暦{year_ad}年）に"
japanese_text += f"国家試験委員会によって実施された卒業証明書試験（グレード{grade}）を"
japanese_text += f"{gpa}GPAで卒業したことを証明するものです。"

print(japanese_text)
print("="*80)
