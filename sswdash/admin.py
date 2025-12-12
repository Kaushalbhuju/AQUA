from django.contrib import admin
from django.utils.html import format_html
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'upload_date', 'file_link')
    search_fields = ('title',)
    list_filter = ('upload_date',)
    ordering = ('-upload_date',)
    readonly_fields = ('upload_date',)

    def file_link(self, obj):
        if obj.uploaded_file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.uploaded_file.url)
        return "-"
    file_link.short_description = "File"
