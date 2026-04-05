from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from books.models import Book, AssignmentTemplate, BookAssignment
from books.forms import AssignBookForm, AssignmentTemplateForm
from books.decorators import manager_or_staff_required, manager_required
from books.utils import generate_qr, generate_sticker, generate_assignment_qr, merge_qr_into_pdf


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
    context = {
        'assignments': assignments,
        'page_title': 'All Assignments',
    }
    return render(request, 'books/assignment_list.html', context)


@login_required
def download_assignment_pdf(request, assignment_id):
    assignment = get_object_or_404(BookAssignment, pk=assignment_id)
    if not assignment.final_pdf:
        messages.error(request, 'No PDF file found for this assignment.')
        return redirect('books:assignment_detail', assignment_id=assignment_id)
    from django.http import FileResponse, Http404
    import os
    file_path = assignment.final_pdf.path
    if not os.path.exists(file_path):
        messages.error(request, 'PDF file not found on server.')
        return redirect('books:assignment_detail', assignment_id=assignment_id)
    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{assignment.id}_document.pdf"'
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
