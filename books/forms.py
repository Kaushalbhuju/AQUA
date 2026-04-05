from django import forms
from .models import AssignmentTemplate, BookAssignment

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
