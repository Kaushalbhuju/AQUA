from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from books.models import Book, BookAssignment, AssignmentTemplate
from books.utils import generate_qr, generate_sticker, generate_assignment_image, merge_qr_into_pdf


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


def _mark_as_returned(modeladmin, request, queryset):
    count = 0
    for assignment in queryset:
        if not assignment.returned:
            assignment.returned = True
            assignment.save(update_fields=['returned'])
            if assignment.book.issued_count > 0:
                assignment.book.issued_count -= 1
                assignment.book.save(update_fields=['issued_count'])
            count += 1
    modeladmin.message_user(request, f'Marked {count} assignment(s) as returned.')


_mark_as_returned.short_description = 'Mark selected as Returned'


def _mark_as_paid(modeladmin, request, queryset):
    count = queryset.update(is_paid=True)
    modeladmin.message_user(request, f'Marked {count} assignment(s) as paid.')


_mark_as_paid.short_description = 'Mark selected as Paid'


def _mark_as_unpaid(modeladmin, request, queryset):
    count = queryset.update(is_paid=False)
    modeladmin.message_user(request, f'Marked {count} assignment(s) as unpaid.')


_mark_as_unpaid.short_description = 'Mark selected as Unpaid'


def _regenerate_assignment_image(modeladmin, request, queryset):
    count = 0
    for assignment in queryset:
        try:
            if assignment.assignment_qr:
                generate_assignment_image(assignment)
                count += 1
        except Exception as e:
            modeladmin.message_user(request, f'Error for {assignment.pk}: {e}', level='error')
    modeladmin.message_user(request, f'Generated images for {count} assignment(s).')


_regenerate_assignment_image.short_description = 'Regenerate Assignment Images'


class BookAssignmentInline(admin.TabularInline):
    model = BookAssignment
    extra = 0
    readonly_fields = ('id', 'recipient_name', 'recipient_id', 'created_at', 'returned', 'is_paid')
    can_delete = False
    fields = ('id', 'recipient_name', 'recipient_id', 'created_at', 'returned', 'is_paid')
    
    def has_add_permission(self, request, obj=None):
        return False


class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'total_stock', 'issued_count', 'remaining_stock_display',
                    'status_badge', 'current_holder', 'qr_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('id', 'name', 'author', 'current_holder', 'isbn')
    readonly_fields = ('created_at', 'qr_preview_large', 'issued_count')
    actions = [_generate_all_qr, _generate_all_stickers]
    inlines = [BookAssignmentInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'author', 'isbn', 'description')
        }),
        ('Stock Management', {
            'fields': ('total_stock', 'issued_count', 'current_holder')
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_preview_large')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

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
            return format_html('<img src="{}" style="width:50px;height:50px;" />', obj.qr_code.url)
        return '—'
    qr_preview.short_description = 'QR'

    def qr_preview_large(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="width:150px;height:150px;" />', obj.qr_code.url)
        return 'No QR Code'
    qr_preview_large.short_description = 'QR Code Preview'


class BookAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'book_link', 'recipient_name', 'recipient_id', 'created_at', 'returned', 'is_paid', 'assigned_by', 'pdf_preview', 'image_preview')
    list_filter = ('returned', 'is_paid', 'created_at', 'template')
    search_fields = ('id', 'recipient_name', 'recipient_id', 'book__name', 'book__id')
    readonly_fields = ('created_at', 'updated_at', 'assignment_qr_preview', 'final_pdf_preview', 'final_image_preview')
    actions = [_mark_as_returned, _mark_as_paid, _mark_as_unpaid, _regenerate_assignment_image]
    raw_id_fields = ('book', 'assigned_by', 'template')
    fieldsets = (
        ('Assignment Details', {
            'fields': ('id', 'book', 'recipient_name', 'recipient_id')
        }),
        ('Template & Files', {
            'fields': ('template', 'assignment_qr_preview', 'final_pdf_preview', 'final_image_preview')
        }),
        ('Status', {
            'fields': ('returned', 'is_paid', 'notes')
        }),
        ('Metadata', {
            'fields': ('assigned_by', 'created_at', 'updated_at')
        }),
    )

    def book_link(self, obj):
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.book.name)
    book_link.short_description = 'Book'

    def pdf_preview(self, obj):
        if obj.final_pdf:
            return format_html('<a href="{}" target="_blank" class="btn btn-sm btn-primary">Download PDF</a>', obj.final_pdf.url)
        return '—'
    pdf_preview.short_description = 'PDF'

    def image_preview(self, obj):
        if obj.final_image:
            return format_html('<a href="{}" target="_blank" class="btn btn-sm btn-info">Download IMG</a>', obj.final_image.url)
        return '—'
    image_preview.short_description = 'Image'

    def assignment_qr_preview(self, obj):
        if obj.assignment_qr:
            return format_html('<img src="{}" style="width:100px;height:100px;" />', obj.assignment_qr.url)
        return '—'
    assignment_qr_preview.short_description = 'Assignment QR'

    def final_pdf_preview(self, obj):
        if obj.final_pdf:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.final_pdf.url)
        return '—'
    final_pdf_preview.short_description = 'Final PDF'

    def final_image_preview(self, obj):
        if obj.final_image:
            return format_html('<img src="{}" style="width:100px;height:auto;" />', obj.final_image.url)
        return '—'
    final_image_preview.short_description = 'Final Image'


class AssignmentTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'template_preview', 'qr_x', 'qr_y', 'qr_size', 'qr_page', 'name_position', 'id_position', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'template_preview_large')
    fieldsets = (
        ('Template Information', {
            'fields': ('id', 'name', 'pdf_file', 'template_preview_large')
        }),
        ('QR Code Position', {
            'fields': ('qr_x', 'qr_y', 'qr_size', 'qr_page')
        }),
        ('Text Position (Optional)', {
            'fields': ('name_x', 'name_y', 'id_x', 'id_y'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def template_preview(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank" class="btn btn-sm btn-primary">View</a>', obj.pdf_file.url)
        return '—'
    template_preview.short_description = 'PDF'

    def template_preview_large(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Download/View PDF Template</a>', obj.pdf_file.url)
        return '—'
    template_preview_large.short_description = 'Template File'

    def name_position(self, obj):
        return f"({obj.name_x}, {obj.name_y})"
    name_position.short_description = 'Name Position'

    def id_position(self, obj):
        return f"({obj.id_x}, {obj.id_y})"
    id_position.short_description = 'ID Position'


admin.site.register(Book, BookAdmin)
admin.site.register(BookAssignment, BookAssignmentAdmin)
admin.site.register(AssignmentTemplate, AssignmentTemplateAdmin)
