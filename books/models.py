from django.db import models
import os
import base64
import mimetypes



class Book(models.Model):
    id = models.CharField(max_length=30, primary_key=True, help_text='e.g. BK-ENG-001')
    name = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True, verbose_name='ISBN')
    description = models.TextField(blank=True, null=True)
    total_stock = models.PositiveIntegerField(default=1)
    issued_count = models.PositiveIntegerField(default=0)
    current_holder = models.CharField(max_length=255, blank=True, null=True,
                                      help_text='Name of last assigned student/person')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

    def __str__(self):
        return f'{self.id} – {self.name}'

    @property
    def qr_code_data_uri(self):
        if not self.qr_code:
            return None
        try:
            if self.qr_code.storage.exists(self.qr_code.name):
                with self.qr_code.open('rb') as f:
                    encoded = base64.b64encode(f.read()).decode('ascii')
                mime = mimetypes.guess_type(self.qr_code.name)[0] or 'image/png'
                return f'data:{mime};base64,{encoded}'
        except Exception:
            pass
        return None

    def qr_code_url(self):
        if self.qr_code and self.qr_code.name:
            from django.conf import settings
            if settings.DEBUG:
                return self.qr_code.url
            return f"/media/{self.qr_code.name}"
        return None

    @property
    def remaining_stock(self):
        return max(self.total_stock - self.issued_count, 0)

    @property
    def status(self):
        if self.remaining_stock > 0:
            return 'available'
        return 'out_of_stock'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        # Generate QR code automatically for new books or when QR is missing
        if not self.qr_code:
            from books.utils import generate_qr
            generate_qr(self)


class AssignmentTemplate(models.Model):
    name = models.CharField(max_length=100)
    pdf_file = models.FileField(upload_to='assignment_templates/')
    qr_x = models.FloatField(default=100, help_text="X coordinate for QR placement (points)")
    qr_y = models.FloatField(default=100, help_text="Y coordinate for QR placement (points)")
    qr_size = models.PositiveIntegerField(default=300, help_text="Size of QR code (points)")
    qr_page = models.PositiveIntegerField(default=1, help_text="Page number for QR placement (1-indexed)")
    
    # Text placement for "Book Name" and "ID"
    name_x = models.FloatField(default=0, help_text="X for Book Name")
    name_y = models.FloatField(default=0, help_text="Y for Book Name")
    id_x = models.FloatField(default=0, help_text="X for Book ID")
    id_y = models.FloatField(default=0, help_text="Y for Book ID")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def pdf_file_url(self):
        if self.pdf_file and self.pdf_file.name:
            from django.conf import settings
            if settings.DEBUG:
                return self.pdf_file.url
            return f"/media/{self.pdf_file.name}"
        return None


class BookAssignment(models.Model):
    id = models.CharField(max_length=50, primary_key=True, help_text='Unique Assignment ID')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='assignments')
    recipient_name = models.CharField(max_length=255)
    recipient_id = models.CharField(max_length=100, blank=True, null=True, help_text='Student ID or similar')
    template = models.ForeignKey(AssignmentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    assignment_qr = models.ImageField(upload_to='assignment_qrs/', blank=True, null=True)
    final_pdf = models.FileField(upload_to='assigned_books_pdfs/', blank=True, null=True)
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    returned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient_name} – {self.book.name} ({self.id})"

    @property
    def assignment_qr_data_uri(self):
        if not self.assignment_qr:
            return None
        try:
            with self.assignment_qr.open('rb') as f:
                encoded = base64.b64encode(f.read()).decode('ascii')
            mime = mimetypes.guess_type(self.assignment_qr.name)[0] or 'image/png'
            return f'data:{mime};base64,{encoded}'
        except Exception:
            return None

    def assignment_qr_url(self):
        if self.assignment_qr and self.assignment_qr.name:
            from django.conf import settings
            if settings.DEBUG:
                return self.assignment_qr.url
            return f"/media/{self.assignment_qr.name}"
        return None
