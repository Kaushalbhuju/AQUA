from django.core.management.base import BaseCommand
from books.models import Book


SEED_DATA = [
    {
        'id': 'BK-ENG-001',
        'name': 'Computer Networking: A Top-Down Approach',
        'total_stock': 50,
    },
    {
        'id': 'BK-MTH-002',
        'name': 'Mathematics for Engineers',
        'total_stock': 30,
    },
    {
        'id': 'BK-PGM-003',
        'name': 'Introduction to Algorithms',
        'total_stock': 20,
    },
    {
        'id': 'BK-PHY-004',
        'name': 'University Physics',
        'total_stock': 25,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample books for testing.'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for data in SEED_DATA:
            book, was_created = Book.objects.get_or_create(
                id=data['id'],
                defaults={
                    'name': data['name'],
                    'total_stock': data['total_stock'],
                }
            )
            if was_created:
                self.stdout.write(self.style.SUCCESS(f'  Created: {book}'))
                created += 1
            else:
                self.stdout.write(f'  Skipped (already exists): {book}')
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeding complete. Created: {created}, Skipped: {skipped}.'
        ))
