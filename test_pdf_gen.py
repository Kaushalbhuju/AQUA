from books.models import Book, AssignmentTemplate, BookAssignment
from books.utils import generate_assignment_qr, merge_qr_into_pdf
import uuid

# Get test book and template
book = Book.objects.get(id='MnN-3A')
template = AssignmentTemplate.objects.get(name='AQUA Smart Card')

# Create assignment
asgn_id = f"TEST-{uuid.uuid4().hex[:6].upper()}"
assignment = BookAssignment.objects.create(
    id=asgn_id,
    book=book,
    recipient_name='Test Student',
    recipient_id='STU-123',
    template=template
)

# Process
generate_assignment_qr(assignment)
pdf_path = merge_qr_into_pdf(assignment)

print(f"Test Successful!")
print(f"Assignment ID: {assignment.id}")
print(f"Final PDF Path: {pdf_path}")
