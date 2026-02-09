# other_documents/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import FinancialDocument, DocumentComment
from .forms import FinancialDocumentForm, DocumentCommentForm

@login_required
def document_list(request):
    documents = FinancialDocument.objects.all()
    
    # Restrict confidential documents to managers only
    if not hasattr(request.user, 'role') or request.user.role != 'manager':
        documents = documents.filter(is_confidential=False)
    
    # Simple search
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client_name__icontains=search_query)
        )
    
    # Filter by type
    doc_type = request.GET.get('type', '')
    if doc_type:
        documents = documents.filter(document_type=doc_type)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        documents = documents.filter(status=status)
    
    # Pagination
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate document type counts
    type_counts = {}
    for doc_type, type_name in FinancialDocument.DOCUMENT_TYPES:
        type_counts[doc_type] = documents.filter(document_type=doc_type).count()
    
    # Prepare type_counts_list for template
    type_counts_list = []
    for doc_type, type_name in FinancialDocument.DOCUMENT_TYPES:
        count = documents.filter(document_type=doc_type).count()
        type_counts_list.append({
            'code': doc_type,
            'name': type_name,
            'count': count,
            'percentage': (count / documents.count() * 100) if documents.count() > 0 else 0
        })
    
    context = {
        'page_obj': page_obj,
        'document_types': FinancialDocument.DOCUMENT_TYPES,
        'status_choices': FinancialDocument.STATUS_CHOICES,
        'approved_count': documents.filter(status='approved').count(),
        'pending_count': documents.filter(status='pending').count(),
        'confidential_count': documents.filter(is_confidential=True).count(),
        'type_counts': type_counts,
        'type_counts_list': type_counts_list,  # Add this for the template
    }
    
    return render(request, 'other_document/document_list.html', context)  # Only one return statement

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('document_list')
    else:
        form = FinancialDocumentForm()
    
    return render(request, 'other_document/upload_document.html', {'form': form})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(FinancialDocument, pk=pk)

    # Check for confidential access
    if document.is_confidential and (not hasattr(request.user, 'role') or request.user.role != 'manager'):
        messages.error(request, 'Access denied: This document is confidential and restricted to managers only.')
        return redirect('document_list')
    
    # Handle comments
    if request.method == 'POST':
        comment_form = DocumentCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.document = document
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added!')
            return redirect('document_detail', pk=pk)
    else:
        comment_form = DocumentCommentForm()
    
    comments = document.comments.all()
    
    return render(request, 'other_document/document_detail.html', {
        'document': document,
        'comments': comments,
        'comment_form': comment_form,
    })

@login_required
def edit_document(request, pk):
    document = get_object_or_404(FinancialDocument, pk=pk)
    
    # Check permission
    if not (request.user.is_staff or document.uploaded_by == request.user):
        messages.error(request, 'You do not have permission to edit this document.')
        return redirect('document_list')
    
    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'Document updated successfully!')
            return redirect('document_detail', pk=pk)
    else:
        form = FinancialDocumentForm(instance=document)
    
    return render(request, 'other_document/edit_document.html', {
        'form': form,
        'document': document,
    })

@login_required
def delete_document(request, pk):
    document = get_object_or_404(FinancialDocument, pk=pk)
    
    # Check permission
    if not (request.user.is_staff or document.uploaded_by == request.user):
        messages.error(request, 'You do not have permission to delete this document.')
        return redirect('document_list')
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('document_list')
    
    return render(request, 'other_document/confirm_delete.html', {'document': document})