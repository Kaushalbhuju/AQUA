from django import forms
from translation.models import Document, DocumentType, TranslationMemory


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents for translation."""

    class Meta:
        model = Document
        fields = ['title', 'original_file', 'file_type', 'document_type', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter document title...',
                'id': 'id_title',
            }),
            'original_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
                'id': 'id_original_file',
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_file_type',
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_document_type',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes...',
                'id': 'id_notes',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].required = False
        self.fields['document_type'].empty_label = '-- Auto-detect --'
        self.fields['notes'].required = False

    def clean_original_file(self):
        f = self.cleaned_data.get('original_file')
        if f:
            ext = f.name.lower().rsplit('.', 1)[-1] if '.' in f.name else ''
            allowed = ['pdf', 'jpg', 'jpeg', 'png']
            if ext not in allowed:
                raise forms.ValidationError(
                    f'Unsupported file format ".{ext}". Allowed: {", ".join(allowed)}'
                )
            # Limit file size to 20MB
            if f.size > 20 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 20MB.')
        return f


class DocumentTypeOverrideForm(forms.Form):
    """Form for manually overriding the detected document type."""

    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_override_type',
        }),
        required=True,
        label='Document Type',
    )


class TranslationReviewForm(forms.Form):
    """Form for reviewing/editing translated text side-by-side."""

    translated_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 20,
            'dir': 'ltr',
            'id': 'id_translated_text',
            'style': 'font-family: "MS Gothic", "Yu Gothic", sans-serif; font-size: 14px;',
        }),
        required=True,
    )
    update_tm = forms.BooleanField(
        required=False,
        initial=True,
        label='Update Translation Memory with edits',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_update_tm',
        }),
    )


class TranslationMemoryForm(forms.ModelForm):
    """Form for manually adding/editing Translation Memory entries."""

    class Meta:
        model = TranslationMemory
        fields = ['english_text', 'japanese_text', 'document_type', 'is_verified']
        widgets = {
            'english_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'English text...',
                'id': 'id_tm_english',
            }),
            'japanese_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Japanese translation...',
                'style': 'font-family: "MS Gothic", "Yu Gothic", sans-serif;',
                'id': 'id_tm_japanese',
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_tm_doctype',
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_tm_verified',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].required = False
        self.fields['document_type'].empty_label = '-- Any type --'


class TranslationMemorySearchForm(forms.Form):
    """Form for searching Translation Memory."""

    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search English or Japanese text...',
            'id': 'id_tm_search',
        }),
    )
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
        required=False,
        empty_label='-- All Types --',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tm_search_type',
        }),
    )
    verified_only = forms.BooleanField(
        required=False,
        label='Verified Only',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_tm_verified_only',
        }),
    )
