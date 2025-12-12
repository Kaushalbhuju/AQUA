from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Document
from .forms import DocumentForm

def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Document uploaded successfully.")
            return redirect('sswdash:list_documents')
    else:
        form = DocumentForm()
    return render(request, 'upload.html', {'form': form})

def list_documents(request):
    documents = Document.objects.all().order_by('-upload_date')
    return render(request, 'list.html', {'documents': documents})

@require_POST
def delete_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.delete()
    messages.success(request, f"Document '{doc.title}' deleted successfully.")
    return redirect('sswdash:list_documents')
