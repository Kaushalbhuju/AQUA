"""
Debug command: parse the exact OCR text from the spec and print structured extraction.
Usage:
  python manage.py debug_character_certificate
  python manage.py debug_character_certificate --text "raw ocr here"
"""
import json
from django.core.management.base import BaseCommand


DEFAULT_OCR = (
    "Registration No. 785275160009 AUT Uta TTS GOVERNMENT OF NEPAL "
    "NATIONAL EXAMINATIONS BOARD CERTIFICATE q ROHAN GURUNG This is to certify that Mr./Ms, "
    "at HEART SECONDARY BOARDING SCHOOL, GOLDHUNGA, KATHMANDU has completed "
    "School Leaving Certificate Examination (Grade XII) conducted by 2079 B.S. (2022 A.D.) "
    "National Examinations Board in the year _ sks for Controller of Examinations "
    "Chairperson Date 2082/12/18 (4/1/2026)"
)


class Command(BaseCommand):
    help = "Debug Character Certificate field extraction (RAW OCR -> structured)."

    def add_arguments(self, parser):
        parser.add_argument('--text', type=str, default=None, help='Raw OCR text (defaults to spec example)')

    def handle(self, *args, **options):
        raw = options['text'] or DEFAULT_OCR
        from translation.services.parsers.character_certificate import parse_character_certificate

        result = parse_character_certificate(raw)
        flat = result.get('flat', {})
        fields = result.get('fields', {})
        meta = result.get('metadata', {})

        self.stdout.write(self.style.SUCCESS("=== RAW OCR (truncated) ==="))
        self.stdout.write(raw[:500] + ("..." if len(raw) > 500 else ""))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Structured flat (spec keys) ==="))
        self.stdout.write(json.dumps(flat, indent=2, ensure_ascii=False))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Per-field confidence/method ==="))
        self.stdout.write(json.dumps(fields, indent=2, ensure_ascii=False))
        self.stdout.write("")
        self.stdout.write(f"Overall confidence: {meta.get('overall_confidence')}")
        if meta.get('validation_errors'):
            self.stdout.write(self.style.WARNING(f"Validation errors: {meta['validation_errors']}"))

        # Expected assertion for default OCR
        if options['text'] is None:
            expected = {
                'registration_number': '785275160009',
                'student_name': 'ROHAN GURUNG',
                'school_name': 'HEART SECONDARY BOARDING SCHOOL',
                'school_location': 'GOLDHUNGA, KATHMANDU',
                'grade': 'XII',
                'examination_year_bs': '2079',
                'examination_year_ad': '2022',
                'certificate_date_bs': '2082/12/18',
                'certificate_date_ad': '2026/04/01',
                'gpa': None,
                'serial_number': None,
            }
            ok = True
            for k, v in expected.items():
                if flat.get(k) != v:
                    self.stdout.write(self.style.ERROR(f"FAIL {k}: expected {v!r}, got {flat.get(k)!r}"))
                    ok = False
            if ok:
                self.stdout.write(self.style.SUCCESS("All expected fields PASSED"))
            else:
                self.stdout.write(self.style.ERROR("Some fields FAILED — see above"))
