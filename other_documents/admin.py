# other_documents/admin.py
from django.contrib import admin
from .models import FinancialDocument, DocumentComment

@admin.register(FinancialDocument)
class FinancialDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'status', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'status', 'uploaded_at']
    search_fields = ['title', 'description', 'client_name']

@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment', 'document__title']