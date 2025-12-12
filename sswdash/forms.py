from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'uploaded_file']

    def clean_uploaded_file(self):
        file = self.cleaned_data.get('uploaded_file')
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError("Only PDF files are allowed.")
            if file.size > 5 * 1024 * 1024:  # 5 MB limit
                raise forms.ValidationError("File size must be under 5MB.")
        return file
