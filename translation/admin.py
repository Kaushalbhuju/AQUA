from django.contrib import admin
from translation.models import Document, DocumentType, TranslationMemory, TranslationHistory


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'keywords_short', 'created_at']
    search_fields = ['name', 'keywords']
    ordering = ['name']

    def keywords_short(self, obj):
        kw = obj.keywords
        return kw[:80] + '...' if len(kw) > 80 else kw
    keywords_short.short_description = 'Keywords'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'document_type', 'status', 'uploaded_by', 'created_at']
    list_filter = ['status', 'file_type', 'document_type', 'created_at']
    search_fields = ['title', 'extracted_text', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 20

    fieldsets = (
        ('Document Info', {
            'fields': ('title', 'original_file', 'file_type', 'document_type',
                       'auto_detected_type', 'status')
        }),
        ('Content', {
            'fields': ('extracted_text', 'translated_text', 'translated_file'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'reviewed_by', 'notes', 'error_message',
                       'created_at', 'updated_at'),
        }),
    )


@admin.register(TranslationMemory)
class TranslationMemoryAdmin(admin.ModelAdmin):
    list_display = ['english_short', 'japanese_short', 'document_type',
                    'source', 'usage_count', 'is_verified', 'updated_at']
    list_filter = ['source', 'is_verified', 'document_type', 'created_at']
    search_fields = ['english_text', 'japanese_text']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    list_editable = ['is_verified']
    list_per_page = 25
    actions = ['mark_verified', 'mark_unverified']

    def english_short(self, obj):
        text = obj.english_text
        return text[:60] + '...' if len(text) > 60 else text
    english_short.short_description = 'English'

    def japanese_short(self, obj):
        text = obj.japanese_text
        return text[:60] + '...' if len(text) > 60 else text
    japanese_short.short_description = 'Japanese'

    def mark_verified(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} entries marked as verified.')
    mark_verified.short_description = 'Mark selected as verified'

    def mark_unverified(self, request, queryset):
        count = queryset.update(is_verified=False)
        self.message_user(request, f'{count} entries marked as unverified.')
    mark_unverified.short_description = 'Mark selected as unverified'


@admin.register(TranslationHistory)
class TranslationHistoryAdmin(admin.ModelAdmin):
    list_display = ['action', 'document', 'user', 'details_short', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['details', 'document__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    list_per_page = 30

    def details_short(self, obj):
        text = obj.details
        return text[:80] + '...' if len(text) > 80 else text
    details_short.short_description = 'Details'
