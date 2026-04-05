from django.core.management.base import BaseCommand
from books.models import Book
from books.utils import generate_qr

class Command(BaseCommand):
    help = 'Generates/Regenerates QR codes for all books pointing to the public scan URL'

    def handle(self, *args, **options):
        books = Book.objects.all()
        count = 0
        for book in books:
            generate_qr(book)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully regenerated QR codes for {count} books.'))
