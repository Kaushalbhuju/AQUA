import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    qrcode = None
    QRCODE_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def generate_qr(book):
    """
    Generate a QR code PNG for the given book pointing to /books/scan/book/<book.id>/
    This is for public/visitor tracking.
    """
    if not QRCODE_AVAILABLE:
        raise RuntimeError('qrcode is not installed. Run: pip install qrcode[pil]')

    from django.conf import settings
    site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    url = f'{site_url}/books/scan/book/{book.pk}/'
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    filename = f'{book.pk}.png'
    # Use update() to avoid triggering save() again
    from books.models import Book  # local import to avoid circular dependency
    Book.objects.filter(pk=book.pk).update(
        qr_code=f'qr_codes/{filename}'
    )
    # Write the file to disk
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)
    filepath = os.path.join(qr_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())
    return filepath


def generate_sticker(book):
    """
    Generate a printable sticker PNG for the given book using Pillow.
    Sticker includes: Book ID, Name, Stock info, and QR code.
    Saves to media/stickers/<book_id>.png and returns the filepath.
    """
    if not PILLOW_AVAILABLE:
        raise RuntimeError('Pillow is not installed. Run: pip install Pillow')

    sticker_dir = os.path.join(settings.MEDIA_ROOT, 'stickers')
    os.makedirs(sticker_dir, exist_ok=True)

    # Load QR image
    qr_path = os.path.join(settings.MEDIA_ROOT, 'qr_codes', f'{book.pk}.png')
    if not os.path.exists(qr_path):
        generate_qr(book)

    qr_img = Image.open(qr_path).convert('RGBA')
    qr_size = 200
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    # Sticker canvas
    width, height = 600, 260
    sticker = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(sticker)

    # Border
    draw.rectangle([(2, 2), (width - 3, height - 3)], outline=(30, 30, 30), width=3)

    # Paste QR
    sticker.paste(qr_img, (20, 30))

    # Text area
    text_x = qr_size + 40
    try:
        # Try to use a nice font if available
        font_large = ImageFont.truetype('arial.ttf', 22)
        font_medium = ImageFont.truetype('arial.ttf', 16)
        font_small = ImageFont.truetype('arial.ttf', 13)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    draw.text((text_x, 25), book.pk, fill=(20, 20, 20), font=font_large)
    draw.text((text_x, 60), book.name, fill=(40, 40, 40), font=font_medium)
    draw.text((text_x, 100), f'Total Stock: {book.total_stock}', fill=(80, 80, 80), font=font_small)
    draw.text((text_x, 125), f'Issued:      {book.issued_count}', fill=(80, 80, 80), font=font_small)
    draw.text((text_x, 150), f'Remaining:   {book.remaining_stock}', fill=(80, 80, 80), font=font_small)

    status_color = (34, 139, 34) if book.status == 'available' else (200, 30, 30)
    draw.text((text_x, 185), f'Status: {book.status.replace("_", " ").title()}',
              fill=status_color, font=font_medium)

    filepath = os.path.join(sticker_dir, f'{book.pk}.png')
    sticker.save(filepath, format='PNG')
    return filepath

def generate_assignment_qr(assignment, request=None):
    """
    Generate a QR code for a specific book assignment.
    Points to the scan landing page: /books/scan/<assignment_id>/
    """
    if not QRCODE_AVAILABLE:
        raise RuntimeError('qrcode is not installed. Run: pip install qrcode[pil]')

    from django.conf import settings
    base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    if request:
        # If we have a request, prioritize it to ensure it matches current host
        base_url = f"{request.scheme}://{request.get_host()}"
    
    url = f"{base_url}/books/scan/{assignment.id}/"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # Higher correction for embedding
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    filename = f"asgn_{assignment.id}.png"
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'assignment_qrs')
    os.makedirs(qr_dir, exist_ok=True)
    filepath = os.path.join(qr_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())
        
    assignment.assignment_qr = f'assignment_qrs/{filename}'
    assignment.save(update_fields=['assignment_qr'])
    return filepath


def merge_qr_into_pdf(assignment):
    """
    Overlays the assignment QR code AND text (Name, ID) onto the template.
    Supports both PDF and Image templates.
    """
    if not assignment.template or not assignment.template.pdf_file:
        return None

    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PyPDF3 import PdfFileWriter, PdfFileReader

    template_path = assignment.template.pdf_file.path
    if not os.path.exists(template_path) or os.path.getsize(template_path) == 0:
        return None

    qr_path = assignment.assignment_qr.path if assignment.assignment_qr else generate_assignment_qr(assignment)
    is_image = template_path.lower().endswith(('.png', '.jpg', '.jpeg'))
    
    # Create the overlay/content layer
    packet = BytesIO()
    can = canvas.Canvas(packet)
    
    # If it's an image, we draw it as the background first
    if is_image:
        img = Image.open(template_path)
        img_w, img_h = img.size
        # Maintain aspect ratio in a standard PDF page or use image size
        # Let's use a scale factor to map pixels to points (1 pt = 1/72 inch)
        can.setPageSize((img_w, img_h))
        can.drawImage(template_path, 0, 0, width=img_w, height=img_h)
    
    # Draw QR
    qr_size = assignment.template.qr_size
    can.drawImage(qr_path, assignment.template.qr_x, assignment.template.qr_y, width=qr_size, height=qr_size)
    
    # Draw Dynamic Text (Book Name, ID)
    can.setFont("Helvetica-Bold", 18)
    can.setFillColorRGB(0.1, 0.2, 0.4) # Dark blue-ish
    
    if assignment.template.name_x > 0:
        can.drawString(assignment.template.name_x, assignment.template.name_y, assignment.book.name)
    
    if assignment.template.id_x > 0:
        can.drawString(assignment.template.id_x, assignment.template.id_y, assignment.book.id)
    
    can.showPage()
    can.save()
    packet.seek(0)
    
    try:
        new_pdf_layer = PdfFileReader(packet, strict=False)
        output = PdfFileWriter()

        if is_image:
            # The "layer" is already the whole document for an image
            page = new_pdf_layer.getPage(0)
            output.addPage(page)
        else:
            with open(template_path, "rb") as f_in:
                existing_pdf = PdfFileReader(f_in, strict=False)
                qr_page_num = max(0, min(assignment.template.qr_page - 1, len(existing_pdf.pages) - 1))
                
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.getPage(i)
                    if i == qr_page_num:
                        page.mergePage(new_pdf_layer.getPage(0))
                    output.addPage(page)

        # Save final PDF
        filename = f"asgn_doc_{assignment.id}.pdf"
        final_dir = os.path.join(settings.MEDIA_ROOT, 'assigned_books_pdfs')
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, filename)
        
        with open(final_path, "wb") as f_out:
            output.write(f_out)
            
        assignment.final_pdf = f'assigned_books_pdfs/{filename}'
        assignment.save(update_fields=['final_pdf'])
        return final_path
    except Exception as e:
        print(f"Error merging PDF: {e}")
        return None

def generate_assignment_image(assignment):
    """
    Generates a PNG image of the assignment with the QR overlaid.
    """
    if not PILLOW_AVAILABLE:
        print("Pillow not available")
        return None

    from PIL import Image, ImageDraw, ImageFont
    import tempfile

    qr_path = assignment.assignment_qr.path if assignment.assignment_qr else generate_assignment_qr(assignment)
    if not qr_path or not os.path.exists(qr_path):
        return None

    has_template = bool(assignment.template and assignment.template.pdf_file)
    template_path = assignment.template.pdf_file.path if has_template else None
    
    base_img = None
    if has_template and template_path and template_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        base_img = Image.open(template_path).convert('RGBA')
    
    if not base_img:
        # Fallback card
        base_img = Image.new('RGBA', (800, 1000), (255, 255, 255, 255))
        draw = ImageDraw.Draw(base_img)
        draw.rectangle([(10, 10), (790, 990)], outline=(200, 200, 200), width=5)

    qr_img = Image.open(qr_path).convert('RGBA')
    
    try:
        font_large = ImageFont.truetype('arial.ttf', 24)
        font_medium = ImageFont.truetype('arial.ttf', 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = font_large

    draw = ImageDraw.Draw(base_img)

    if has_template:
        qr_size = getattr(assignment.template, 'qr_size', 150)
        qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
        base_img.paste(qr_img, (int(assignment.template.qr_x), int(assignment.template.qr_y)), mask=qr_img)

        if assignment.template.name_x > 0:
            draw.text((int(assignment.template.name_x), int(assignment.template.name_y)), 
                      assignment.book.name, fill=(20, 50, 100), font=font_large)
        if assignment.template.id_x > 0:
            draw.text((int(assignment.template.id_x), int(assignment.template.id_y)), 
                      assignment.book.id, fill=(20, 50, 100), font=font_medium)
    else:
        qr_img = qr_img.resize((300, 300), Image.LANCZOS)
        base_img.paste(qr_img, (250, 100), mask=qr_img)
        draw.text((250, 450), f"Book: {assignment.book.name}", fill=(0, 0, 0), font=font_large)
        draw.text((250, 500), f"ID: {assignment.book.id}", fill=(0, 0, 0), font=font_medium)
        draw.text((250, 550), f"Assigned to: {assignment.recipient_name}", fill=(50, 50, 50), font=font_medium)

    filename = f"asgn_img_{assignment.id}.png"
    img_dir = os.path.join(settings.MEDIA_ROOT, 'assigned_books_images')
    os.makedirs(img_dir, exist_ok=True)
    final_path = os.path.join(img_dir, filename)

    base_img.save(final_path, format='PNG')
    assignment.final_image = f'assigned_books_images/{filename}'
    assignment.save(update_fields=['final_image'])
    
    return final_path
