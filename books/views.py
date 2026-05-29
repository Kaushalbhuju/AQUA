from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.core.paginator import Paginator

from books.models import Book, AssignmentTemplate, BookAssignment
from books.forms import AssignBookForm, AssignmentTemplateForm, BookForm
from books.utils import generate_qr, generate_sticker, generate_assignment_qr, merge_qr_into_pdf, generate_assignment_image
from books.decorators import manager_or_staff_required, manager_required


@login_required
def book_list(request):
    books = Book.objects.all()
    context = {
        'books': books,
        'page_title': 'Book Inventory',
    }
    return render(request, 'books/book_list.html', context)


@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    assignments = book.assignments.all()
    context = {
        'book': book,
        'assignments': assignments,
        'page_title': f'Book – {book.name}',
    }
    return render(request, 'books/book_detail.html', context)


@manager_or_staff_required
def assign_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    if book.status == 'out_of_stock':
        messages.error(request, f'"{book.name}" is currently out of stock.')
        return redirect('books:book_detail', book_id=book_id)

    if request.method == 'POST':
        form = AssignBookForm(request.POST)
        if form.is_valid():
            recipient_name = form.cleaned_data['recipient_name']
            recipient_id = form.cleaned_data['recipient_id']
            template = form.cleaned_data['template']
            
            import uuid
            asgn_id = f"ASGN-{uuid.uuid4().hex[:8].upper()}"
            
            assignment = BookAssignment.objects.create(
                id=asgn_id,
                book=book,
                recipient_name=recipient_name,
                recipient_id=recipient_id,
                template=template,
                assigned_by=request.user
            )
            
            # Generate QR and Merge PDF
            generate_assignment_qr(assignment, request)
            if template:
                merge_qr_into_pdf(assignment)
                messages.success(request, f'Book assigned and PDF generated for {recipient_name}.')
            else:
                messages.success(request, f'Book assigned to {recipient_name}. (No template selected)')

            # Update book stock
            book.issued_count += 1
            book.current_holder = recipient_name
            book.save(update_fields=['issued_count', 'current_holder'])
            
            return redirect('books:assignment_detail', assignment_id=asgn_id)
    else:
        form = AssignBookForm()

    context = {
        'book': book,
        'form': form,
        'page_title': f'Assign – {book.name}',
    }
    return render(request, 'books/book_assign.html', context)


@manager_or_staff_required
def return_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    if request.method == 'POST':
        if book.issued_count > 0:
            book.issued_count -= 1
            if book.issued_count == 0:
                book.current_holder = None
            book.save(update_fields=['issued_count', 'current_holder'])
            
            # Mark the most recent active assignment as returned
            last_active = book.assignments.filter(returned=False).first()
            if last_active:
                last_active.returned = True
                last_active.save(update_fields=['returned'])
            
            messages.success(request, f'Book "{book.name}" returned. '
                                       f'{book.remaining_stock} copy(ies) now available.')
        else:
            messages.warning(request, f'No copies of "{book.name}" are currently issued.')
        return redirect('books:book_detail', book_id=book_id)

    context = {
        'book': book,
        'page_title': f'Return – {book.name}',
    }
    return render(request, 'books/book_return_confirm.html', context)


@login_required
def qr_page(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    # Ensure QR exists
    if not book.qr_code:
        generate_qr(book)
        book.refresh_from_db()
    context = {
        'book': book,
        'page_title': f'QR Code – {book.name}',
    }
    return render(request, 'books/book_qr.html', context)


@manager_required
def generate_all_qr(request):
    books = Book.objects.all()
    count = 0
    errors = []
    for book in books:
        try:
            generate_qr(book)
            count += 1
        except Exception as e:
            errors.append(f'{book.pk}: {e}')
    if errors:
        messages.warning(request, f'Generated {count} QR codes with {len(errors)} error(s): ' + ', '.join(errors))
    else:
        messages.success(request, f'Successfully generated QR codes for all {count} book(s).')
    return redirect('books:book_list')


@manager_required
def generate_all_stickers(request):
    books = Book.objects.all()
    count = 0
    errors = []
    for book in books:
        try:
            generate_sticker(book)
            count += 1
        except Exception as e:
            errors.append(f'{book.pk}: {e}')
    if errors:
        messages.warning(request, f'Generated {count} stickers with {len(errors)} error(s): ' + ', '.join(errors))
    else:
        messages.success(request, f'Successfully generated stickers for all {count} book(s).')
    return redirect('books:book_list')


def assignment_detail(request, assignment_id):
    """
    Public landing page for scanned QRs (or private detail page for staff).
    """
    assignment = get_object_or_404(BookAssignment, pk=assignment_id)
    
    # If not logged in as staff, show minimal view
    if not request.user.is_authenticated or request.user.role not in ['manager', 'staff', 'operation_head']:
        return render(request, 'books/scan_landing.html', {'assignment': assignment, 'is_public': True})

    context = {
        'assignment': assignment,
        'page_title': f'Assignment – {assignment.id}',
    }
    return render(request, 'books/assignment_detail.html', context)


def scan_book(request, book_id):
    """
    Publicly accessible view for scanning the sticker in the book.
    Shows current assignment info minimalistically.
    """
    book = get_object_or_404(Book, pk=book_id)
    # Find latest active assignment
    last_asgn = book.assignments.filter(returned=False).first()
    
    context = {
        'book': book,
        'assignment': last_asgn,
        'is_public': True,
        'page_title': 'Book Status'
    }
    return render(request, 'books/scan_landing.html', context)


@manager_or_staff_required
def assignment_list(request):
    assignments = BookAssignment.objects.all()

    search = request.GET.get('search', '').strip()
    book_filter = request.GET.get('book', '')
    status_filter = request.GET.get('status', '')
    paid_filter = request.GET.get('paid', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if book_filter:
        assignments = assignments.filter(book_id=book_filter)

    if search:
        assignments = assignments.filter(
            Q(recipient_name__icontains=search) |
            Q(recipient_id__icontains=search) |
            Q(book__name__icontains=search) |
            Q(book__id__icontains=search) |
            Q(id__icontains=search)
        )

    if status_filter == 'active':
        assignments = assignments.filter(returned=False)
    elif status_filter == 'returned':
        assignments = assignments.filter(returned=True)

    if paid_filter == 'paid':
        assignments = assignments.filter(is_paid=True)
    elif paid_filter == 'unpaid':
        assignments = assignments.filter(is_paid=False)

    if date_from:
        assignments = assignments.filter(created_at__gte=date_from)
    if date_to:
        assignments = assignments.filter(created_at__lte=date_to)

    paginator = Paginator(assignments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_books = Book.objects.all().order_by('name')
    all_assignments = BookAssignment.objects.all()
    context = {
        'assignments': page_obj,
        'all_books': all_books,
        'page_title': 'All Assignments',
        'search': search,
        'book_filter': book_filter,
        'status_filter': status_filter,
        'paid_filter': paid_filter,
        'date_from': date_from,
        'date_to': date_to,
        'is_paginated': page_obj.has_other_pages(),
        'active_count': all_assignments.filter(returned=False).count(),
        'returned_count': all_assignments.filter(returned=True).count(),
        'unpaid_count': all_assignments.filter(is_paid=False).count(),
    }
    return render(request, 'books/assignment_list.html', context)


@manager_or_staff_required
def update_assignment(request, assignment_id):
    assignment = get_object_or_404(BookAssignment, pk=assignment_id)
    
    if request.method == 'POST':
        old_book_name = assignment.book.name
        
        # Update paid status
        is_paid = request.POST.get('is_paid') == 'on'
        assignment.is_paid = is_paid

        # Update recipient name
        recipient_name = request.POST.get('recipient_name')
        if recipient_name:
            assignment.recipient_name = recipient_name.strip()
        
        # Update book (if changed)
        new_book_id = request.POST.get('book_id')
        if new_book_id and new_book_id != str(assignment.book.id):
            new_book = get_object_or_404(Book, pk=new_book_id)
            assignment.book = new_book
        
        # Update notes
        notes = request.POST.get('notes', '').strip()
        assignment.notes = notes if notes else None
        
        assignment.save()
        
        new_book_name = assignment.book.name
        if old_book_name != new_book_name:
            messages.success(request, f'Assignment updated. Book changed from "{old_book_name}" to "{new_book_name}".')
        else:
            messages.success(request, f'Assignment updated successfully.')
        
    return redirect('books:assignment_list')
    
@manager_required
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(BookAssignment, pk=assignment_id)
    if request.method == 'POST':
        asgn_id = assignment.id
        # If the book was issued and not returned, we might want to adjust stock?
        # Usually deletion is for errors. If it was an active assignment, maybe decrement issued_count.
        if not assignment.returned:
            book = assignment.book
            if book.issued_count > 0:
                book.issued_count -= 1
                book.save(update_fields=['issued_count'])
        
        assignment.delete()
        messages.success(request, f'Assignment {asgn_id} deleted successfully.')
        return redirect('books:assignment_list')
    return redirect('books:assignment_detail', assignment_id=assignment_id)



@login_required
def download_assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(BookAssignment, pk=assignment_id)
    from django.http import FileResponse
    import os

    # Regenerate PDF if it's missing or the file no longer exists on disk
    needs_regen = (
        not assignment.final_pdf or
        not os.path.exists(assignment.final_pdf.path)
    )
    if needs_regen and assignment.template:
        final_path = merge_qr_into_pdf(assignment)
        if not final_path:
            messages.error(request, 'Could not generate PDF for this assignment.')
            return redirect('books:assignment_detail', assignment_id=assignment_id)
        assignment.refresh_from_db()

    if not assignment.final_pdf:
        messages.error(request, 'No PDF file found for this assignment.')
        return redirect('books:assignment_detail', assignment_id=assignment_id)

    file_path = assignment.final_pdf.path
    if not os.path.exists(file_path):
        messages.error(request, 'PDF file not found on server.')
        return redirect('books:assignment_detail', assignment_id=assignment_id)

    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{assignment.id}_document.pdf"'
    return response


@login_required
def download_assignment_png(request, assignment_id):
    assignment = get_object_or_404(BookAssignment, pk=assignment_id)
    from django.http import FileResponse
    import os

    # Regenerate PNG if it's missing or the file no longer exists on disk
    needs_regen = (
        not assignment.final_image or
        not os.path.exists(assignment.final_image.path)
    )
    if needs_regen:
        final_path = generate_assignment_image(assignment)
        if not final_path:
            messages.error(request, 'Could not generate PNG for this assignment.')
            return redirect('books:assignment_detail', assignment_id=assignment_id)
        assignment.refresh_from_db()

    if not assignment.final_image:
        messages.error(request, 'No PNG file found for this assignment.')
        return redirect('books:assignment_detail', assignment_id=assignment_id)

    file_path = assignment.final_image.path
    if not os.path.exists(file_path):
        messages.error(request, 'PNG file not found on server.')
        return redirect('books:assignment_detail', assignment_id=assignment_id)

    response = FileResponse(open(file_path, 'rb'), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{assignment.id}_document.png"'
    return response


@manager_or_staff_required
def bulk_download_pngs(request):
    import zipfile
    import os
    from django.http import FileResponse
    from io import BytesIO

    # Get all active assignments
    assignments = BookAssignment.objects.filter(returned=False)
    if not assignments.exists():
        messages.warning(request, 'There are no active assignments to download.')
        return redirect('books:assignment_list')

    # Create an in-memory zip file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for assignment in assignments:
            # Ensure PNG is generated
            needs_regen = (
                not assignment.final_image or
                not os.path.exists(assignment.final_image.path)
            )
            if needs_regen:
                final_path = generate_assignment_image(assignment)
                if final_path:
                    assignment.refresh_from_db()
            
            if assignment.final_image and os.path.exists(assignment.final_image.path):
                file_path = assignment.final_image.path
                filename = f"{assignment.id}_{assignment.recipient_name}.png"
                # Add to zip
                zip_file.write(file_path, arcname=filename)
    
    zip_buffer.seek(0)
    response = FileResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="bulk_assignment_pngs.zip"'
    return response

@manager_required
def template_list(request):
    templates = AssignmentTemplate.objects.all()
    if request.method == 'POST':
        form = AssignmentTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment template uploaded successfully.')
            return redirect('books:template_list')
    else:
        form = AssignmentTemplateForm()
    
    context = {
        'templates': templates,
        'form': form,
        'page_title': 'PDF Templates',
    }
    return render(request, 'books/template_list.html', context)


@manager_required
def template_create(request):
    if request.method == 'POST':
        form = AssignmentTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template created successfully.')
            return redirect('books:template_list')
    else:
        form = AssignmentTemplateForm()
    context = {'form': form, 'page_title': 'Create Template'}
    return render(request, 'books/template_form.html', context)


@manager_required
def template_update(request, template_id):
    template = get_object_or_404(AssignmentTemplate, pk=template_id)
    if request.method == 'POST':
        form = AssignmentTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            
            # Regenerate PDFs for all existing assignments using this template
            assignments = BookAssignment.objects.filter(template=template)
            regen_count = 0
            regen_errors = 0
            for assignment in assignments:
                try:
                    if assignment.assignment_qr:
                        merge_qr_into_pdf(assignment)
                        regen_count += 1
                except Exception:
                    regen_errors += 1
            
            if regen_count > 0:
                messages.success(
                    request,
                    f'Template updated successfully. {regen_count} existing PDF(s) regenerated.'
                )
            else:
                messages.success(request, 'Template updated successfully.')
            
            if regen_errors > 0:
                messages.warning(request, f'{regen_errors} PDF(s) could not be regenerated.')
            
            return redirect('books:template_list')
    else:
        form = AssignmentTemplateForm(instance=template)
    context = {'form': form, 'template': template, 'page_title': 'Edit Template'}
    return render(request, 'books/template_form.html', context)


@manager_required
def template_delete(request, template_id):
    template = get_object_or_404(AssignmentTemplate, pk=template_id)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template deleted successfully.')
        return redirect('books:template_list')
    return render(request, 'books/template_confirm_delete.html', {'template': template})


@manager_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.save()
            generate_qr(book)
            messages.success(request, f'Book "{book.name}" created successfully.')
            return redirect('books:book_list')
    else:
        form = BookForm()
    context = {'form': form, 'page_title': 'Add Book'}
    return render(request, 'books/book_form.html', context)


@manager_required
def book_update(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.name}" updated successfully.')
            return redirect('books:book_list')
    else:
        form = BookForm(instance=book)
    context = {'form': form, 'book': book, 'page_title': 'Edit Book'}
    return render(request, 'books/book_form.html', context)


@manager_required
def book_delete(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        book_name = book.name
        book.delete()
        messages.success(request, f'Book "{book_name}" deleted successfully.')
        return redirect('books:book_list')
    context = {'book': book, 'page_title': 'Delete Book'}
    return render(request, 'books/book_confirm_delete.html', context)
