from django.contrib import admin
from django.utils.html import format_html
from books.models import Book
from books.utils import generate_qr, generate_sticker


def _generate_all_qr(modeladmin, request, queryset):
    count = 0
    for book in queryset:
        try:
            generate_qr(book)
            count += 1
        except Exception as e:
            modeladmin.message_user(request, f'Error generating QR for {book.pk}: {e}', level='error')
    modeladmin.message_user(request, f'Generated QR codes for {count} book(s).')


_generate_all_qr.short_description = 'Generate QR codes for selected books'


def _generate_all_stickers(modeladmin, request, queryset):
    count = 0
    for book in queryset:
        try:
            generate_sticker(book)
            count += 1
        except Exception as e:
            modeladmin.message_user(request, f'Error generating sticker for {book.pk}: {e}', level='error')
    modeladmin.message_user(request, f'Generated stickers for {count} book(s).')


_generate_all_stickers.short_description = 'Generate stickers for selected books'



class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'total_stock', 'issued_count', 'remaining_stock_display',
                    'status_badge', 'current_holder', 'qr_preview')
    list_filter = ('created_at',)
    search_fields = ('id', 'name', 'current_holder')
    readonly_fields = ('created_at', 'qr_preview')
    actions = [_generate_all_qr, _generate_all_stickers]

    def remaining_stock_display(self, obj):
        return obj.remaining_stock
    remaining_stock_display.short_description = 'Remaining'

    def status_badge(self, obj):
        if obj.status == 'available':
            color = '#28a745'
            label = 'Available'
        else:
            color = '#dc3545'
            label = 'Out of Stock'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="width:80px;height:80px;" />', obj.qr_code.url)
        return '—'
    qr_preview.short_description = 'QR Code'
