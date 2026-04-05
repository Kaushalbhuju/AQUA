from django.core.management.base import BaseCommand
from books.models import AssignmentTemplate
import os

class Command(BaseCommand):
    help = 'Registers the AQUA smart template'

    def handle(self, *args, **options):
        # Find the most recent image in media/assignment_templates
        from django.conf import settings
        template_dir = os.path.join(settings.MEDIA_ROOT, 'assignment_templates')
        files = [f for f in os.listdir(template_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            self.stdout.write(self.style.ERROR('No image found in assignment_templates/'))
            return

        # Sort by modification time to get the newest one
        files.sort(key=lambda x: os.path.getmtime(os.path.join(template_dir, x)), reverse=True)
        latest_file = files[0]
        
        # Coordinates for AQUA template
        # Assuming we use Image size. 
        # Using percentages of typical 1000x1000 image:
        # Book Name: X=240, Y=765
        # ID: X=240, Y=675
        # QR: X=440, Y=250 (Centered horizontally, lower half)
        
        template, created = AssignmentTemplate.objects.get_or_create(
            name='AQUA Smart Card',
            defaults={
                'pdf_file': f'assignment_templates/{latest_file}',
                'qr_x': 320,
                'qr_y': 170,
                'qr_size': 260,
                'qr_page': 1,
                'name_x': 240,
                'name_y': 695,
                'id_x': 240,
                'id_y': 605,
            }
        )
        
        if not created:
            # Update existing
            template.pdf_file = f'assignment_templates/{latest_file}'
            template.qr_x = 320
            template.qr_y = 170
            template.qr_size = 260
            template.name_x = 240
            template.name_y = 695
            template.id_x = 240
            template.id_y = 605
            template.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully registered/updated template: {template.name} using {latest_file}'))
