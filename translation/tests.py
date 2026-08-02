from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

from translation.models import Document, DocumentType, TranslationMemory, TranslationHistory
from translation.forms import DocumentUploadForm, TranslationMemoryForm
from translation.services.detector import detect_document_type
from translation.services.translator import translate_text, translate_paragraph, apply_document_rules

User = get_user_model()


class TranslationModelTests(TestCase):
    """Test translation app database models."""

    def setUp(self):
        self.doc_type = DocumentType.objects.create(
            name="Transcript",
            keywords="transcript,grade sheet,gpa,academic record",
            description="Academic transcripts"
        )
        self.user = User.objects.create_user(
            username="staff_user",
            password="testpassword123",
            email="staff@example.com"
        )

    def test_document_type_creation(self):
        self.assertEqual(self.doc_type.name, "Transcript")
        self.assertEqual(self.doc_type.get_keywords_list(), ["transcript", "grade sheet", "gpa", "academic record"])
        self.assertEqual(str(self.doc_type), "Transcript")

    def test_document_creation(self):
        doc = Document.objects.create(
            title="John Doe Transcript",
            file_type="pdf",
            document_type=self.doc_type,
            uploaded_by=self.user,
            status="uploaded"
        )
        self.assertEqual(doc.title, "John Doe Transcript")
        self.assertEqual(doc.status, "uploaded")
        self.assertEqual(str(doc), "John Doe Transcript (Uploaded)")

    def test_translation_memory_creation(self):
        tm = TranslationMemory.objects.create(
            english_text="This is a test transcript.",
            japanese_text="これはテストの成績証明書です。",
            document_type=self.doc_type,
            source="manual",
            is_verified=True
        )
        self.assertEqual(tm.english_text, "This is a test transcript.")
        self.assertEqual(tm.japanese_text, "これはテストの成績証明書です。")
        self.assertTrue(tm.is_verified)
        self.assertEqual(str(tm), "TM: This is a test transcript.")


class TranslationServiceTests(TestCase):
    """Test translation and text rules services."""

    def setUp(self):
        self.doc_type = DocumentType.objects.create(
            name="Transcript",
            keywords="transcript,grade sheet,gpa,academic record",
            description="Academic transcripts"
        )

    def test_apply_document_rules_transcript(self):
        text = "Subject Code CS101, GPA 3.95, Registration No 987654"
        # For transcripts, we keep GPA, Reg Numbers, Subject codes
        # CS101 matches [A-Z]{2,}\s*\d+
        # 3.95 matches \d+\.?\d*
        # 987654 matches \d+
        rules_applied = apply_document_rules(text, "Transcript")

        # Check that we split the text and some parts should NOT be translated
        self.assertTrue(len(rules_applied) > 1)

    def test_detect_document_type(self):
        text = "This is the official transcript of academic record."
        detected = detect_document_type(text)
        self.assertEqual(detected, self.doc_type)

    @patch('translation.services.translator.translate_with_google')
    def test_translate_paragraph_tm_miss(self, mock_translate):
        mock_translate.return_value = "日本語の翻訳"
        text = "Translate this text please."

        # Verify translation memory is empty first
        self.assertEqual(TranslationMemory.objects.count(), 0)

        # Translate - should trigger Google translate mock
        translated, source = translate_paragraph(text, self.doc_type, "Transcript")

        self.assertEqual(translated, "日本語の翻訳")
        self.assertEqual(source, "google")

        # Verify it got saved to Translation Memory
        self.assertEqual(TranslationMemory.objects.count(), 1)
        tm = TranslationMemory.objects.first()
        self.assertEqual(tm.english_text, text)
        self.assertEqual(tm.japanese_text, "日本語の翻訳")

    def test_translate_paragraph_tm_hit(self):
        text = "Reuse this translation."
        translation = "この翻訳を再利用します。"

        # Add to TM
        TranslationMemory.objects.create(
            english_text=text,
            japanese_text=translation,
            document_type=self.doc_type
        )

        # Translate - should use TM directly without calling Google
        with patch('translation.services.translator.translate_with_google') as mock_translate:
            translated, source = translate_paragraph(text, self.doc_type, "Transcript")
            mock_translate.assert_not_called()

        self.assertEqual(translated, translation)
        self.assertEqual(source, "tm")


class TranslationViewTests(TestCase):
    """Test dashboard, upload, review, and detail views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="staff_user",
            password="testpassword123",
            email="staff@example.com"
        )
        self.doc_type = DocumentType.objects.create(
            name="Transcript",
            keywords="transcript,grade sheet,gpa,academic record"
        )
        # Create a document
        self.document = Document.objects.create(
            title="Test Doc",
            file_type="pdf",
            document_type=self.doc_type,
            uploaded_by=self.user,
            status="extracted",
            extracted_text="Hello World. This is a transcript."
        )

    def test_dashboard_unauthenticated(self):
        response = self.client.get(reverse('translation:dashboard'))
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)

    def test_dashboard_authenticated(self):
        self.client.login(username="staff_user", password="testpassword123")
        response = self.client.get(reverse('translation:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translation/dashboard.html')
        self.assertEqual(response.context['total_documents'], 1)

    def test_document_list_view(self):
        self.client.login(username="staff_user", password="testpassword123")
        response = self.client.get(reverse('translation:document_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Doc")

    def test_document_detail_view(self):
        self.client.login(username="staff_user", password="testpassword123")
        response = self.client.get(reverse('translation:document_detail', args=[self.document.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Doc")
        self.assertContains(response, "Hello World. This is a transcript.")

    def test_document_upload_view(self):
        self.client.login(username="staff_user", password="testpassword123")
        pdf_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        
        response = self.client.post(reverse('translation:document_upload'), {
            'title': 'New Uploaded Doc',
            'original_file': pdf_file,
            'file_type': 'pdf',
            'document_type': self.doc_type.pk,
            'notes': 'Some test notes'
        })
        # Post request should redirect to process page
        self.assertEqual(response.status_code, 302)
        # Check if document was created
        self.assertTrue(Document.objects.filter(title="New Uploaded Doc").exists())
