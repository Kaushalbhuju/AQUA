from django.core.management.base import BaseCommand
from books.models import BookAssignment
from books.utils import generate_assignment_qr, merge_qr_into_pdf

class Command(BaseCommand):
    help = 'Regenerates QR codes and PDFs for all assignments'

    def handle(self, *args, **options):
        assignments = BookAssignment.objects.all()
        count = 0
        for asgn in assignments:
            generate_assignment_qr(asgn)
            if asgn.template:
                merge_qr_into_pdf(asgn)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully regenerated QR and PDFs for {count} assignments.'))
