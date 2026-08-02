import json
import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


def document_upload_path(instance, filename):
    """Generate upload path for documents: media/translation/documents/YYYY/MM/filename"""
    ext = os.path.splitext(filename)[1]
    new_filename = f"{uuid.uuid4().hex[:12]}{ext}"
    return os.path.join('translation', 'documents', timezone.now().strftime('%Y/%m'), new_filename)


def translated_upload_path(instance, filename):
    """Generate upload path for translated DOCX files."""
    ext = os.path.splitext(filename)[1]
    new_filename = f"{uuid.uuid4().hex[:12]}{ext}"
    return os.path.join('translation', 'translated', timezone.now().strftime('%Y/%m'), new_filename)


class DocumentType(models.Model):
    """Predefined document types for classification."""

    name = models.CharField(max_length=100, unique=True)
    keywords = models.TextField(
        help_text="Comma-separated keywords for auto-detection (e.g. 'transcript,grade sheet,marks')"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Document Type'
        verbose_name_plural = 'Document Types'

    def __str__(self):
        return self.name

    def get_keywords_list(self):
        """Return keywords as a list."""
        return [kw.strip().lower() for kw in self.keywords.split(',') if kw.strip()]


class Document(models.Model):
    """Uploaded document for translation."""

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('extracting', 'Extracting Text'),
        ('extracted', 'Text Extracted'),
        ('translating', 'Translating'),
        ('translated', 'Translated'),
        ('reviewing', 'Under Review'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('image', 'Image (JPG/PNG)'),
        ('scanned_pdf', 'Scanned PDF'),
    ]

    title = models.CharField(max_length=255)
    original_file = models.FileField(upload_to=document_upload_path)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents'
    )
    auto_detected_type = models.ForeignKey(
        DocumentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='auto_detected_documents',
        help_text='Auto-detected document type (may differ from manual override)'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    extracted_text = models.TextField(blank=True, help_text='Extracted English text')
    translated_text = models.TextField(blank=True, help_text='Translated Japanese text')
    layout_data = models.TextField(
        blank=True, default='',
        help_text='JSON: text block positions, image positions per page'
    )
    translated_file = models.FileField(upload_to=translated_upload_path, blank=True, null=True)
    notes = models.TextField(blank=True, help_text='Staff notes about this document')
    error_message = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='uploaded_translations'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_translations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['document_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def file_extension(self):
        if self.original_file:
            return os.path.splitext(self.original_file.name)[1].lower()
        return ''

    @property
    def parsed_layout(self):
        """Returns layout_data parsed as dict, or empty dict."""
        if not self.layout_data:
            return {'pages': []}
        try:
            return json.loads(self.layout_data)
        except (json.JSONDecodeError, TypeError):
            return {'pages': []}

    @parsed_layout.setter
    def parsed_layout(self, data):
        """Set layout_data from a dict."""
        if data is None:
            self.layout_data = ''
        else:
            self.layout_data = json.dumps(data)

    @property
    def text_with_image_markers(self):
        """
        Return extracted text with image rectangle markers appended.
        Image markers are appended AFTER the user's extracted_text.
        """
        if not self.extracted_text:
            return ''

        pages = self.parsed_layout.get('pages', [])
        if not pages or not any(p.get('images') for p in pages):
            return self.extracted_text

        markers = []
        for page_data in pages:
            images = page_data.get('images', [])
            if images:
                page_num = page_data.get('page_number', 1)
                markers.append(f'--- Page {page_num} Images ---')
                for img in images:
                    img_name = img.get('name', 'Image')
                    img_w = img.get('width', 0)
                    img_h = img.get('height', 0)
                    markers.append(
                        f'[IMAGE: {img_name} ({img_w:.0f}x{img_h:.0f} pts)]'
                    )

        if not markers:
            return self.extracted_text

        return self.extracted_text + '\n\n' + '\n'.join(markers)

    @property
    def file_size_display(self):
        """Human-readable file size."""
        try:
            if not self.original_file or not self.original_file.name:
                return "N/A"
            size = self.original_file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except (OSError, FileNotFoundError, ValueError):
            return "N/A"


class TranslationMemory(models.Model):
    """
    Translation Memory - stores English-to-Japanese translation pairs.
    This is the PRIMARY translation source. Google Translate is only used
    when no match is found here.
    """

    english_text = models.TextField(db_index=True)
    japanese_text = models.TextField()
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='translation_memories'
    )
    source = models.CharField(
        max_length=50,
        choices=[
            ('google', 'Google Translate'),
            ('manual', 'Manual Entry'),
            ('review', 'Staff Review'),
            ('import', 'Imported'),
        ],
        default='google'
    )
    usage_count = models.PositiveIntegerField(default=0, help_text='Number of times this translation was reused')
    is_verified = models.BooleanField(default=False, help_text='Has been verified by staff')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Translation Memory'
        verbose_name_plural = 'Translation Memories'
        indexes = [
            models.Index(fields=['english_text']),
            models.Index(fields=['document_type']),
            models.Index(fields=['-usage_count']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        eng = self.english_text[:60] + '...' if len(self.english_text) > 60 else self.english_text
        return f"TM: {eng}"

    def increment_usage(self):
        """Increment usage count efficiently."""
        TranslationMemory.objects.filter(pk=self.pk).update(
            usage_count=models.F('usage_count') + 1
        )


class TranslationHistory(models.Model):
    """Tracks translation activity for audit and reporting."""

    ACTION_CHOICES = [
        ('upload', 'Document Uploaded'),
        ('extract', 'Text Extracted'),
        ('translate', 'Translation Completed'),
        ('review', 'Review Completed'),
        ('edit', 'Translation Edited'),
        ('download', 'DOCX Downloaded'),
        ('tm_hit', 'Translation Memory Hit'),
        ('tm_miss', 'Translation Memory Miss'),
        ('error', 'Error Occurred'),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='history', null=True, blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Translation History'
        verbose_name_plural = 'Translation Histories'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
