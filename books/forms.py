from django import forms
from .models import AssignmentTemplate, BookAssignment, Book

class AssignBookForm(forms.Form):
    recipient_name = forms.CharField(
        max_length=200,
        label='Recipient Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter full name of the recipient',
            'autofocus': True,
        })
    )
    recipient_id = forms.CharField(
        max_length=100,
        required=False,
        label='Recipient ID (optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Student ID',
        })
    )
    template = forms.ModelChoiceField(
        queryset=AssignmentTemplate.objects.all(),
        required=False,
        label='PDF Template (optional)',
        empty_label="No Template (QR only)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_recipient_name(self):
        name = self.cleaned_data.get('recipient_name', '').strip()
        if not name:
            raise forms.ValidationError('Recipient name cannot be blank.')
        return name


class AssignmentTemplateForm(forms.ModelForm):
    class Meta:
        model = AssignmentTemplate
        fields = ['name', 'pdf_file', 'qr_x', 'qr_y', 'qr_page']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control'}),
            'qr_x': forms.NumberInput(attrs={'class': 'form-control'}),
            'qr_y': forms.NumberInput(attrs={'class': 'form-control'}),
            'qr_page': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['id', 'name', 'author', 'isbn', 'description', 'total_stock']
        widgets = {
            'id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BK-ENG-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN number'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Book description'}),
            'total_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def clean_id(self):
        book_id = self.cleaned_data.get('id', '').strip().upper()
        if self.instance.pk is None:
            if Book.objects.filter(pk=book_id).exists():
                raise forms.ValidationError(f'Book ID "{book_id}" already exists.')
        return book_id
