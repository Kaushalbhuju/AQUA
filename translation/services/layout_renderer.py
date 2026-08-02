"""
Layout-preserving bilingual PDF renderer.
Takes original PDF + translated text, produces PDF overlay with Japanese
text at the exact same positions as original English text.
Preserves all images/photos from the original document.
"""
import io
import logging
import os
from collections import defaultdict

logger = logging.getLogger(__name__)


def compute_font_size(text, bbox_width, bbox_height, max_size=14, min_size=6):
    """
    Compute optimal font size so translated text fits within the original bbox.
    Japanese text is often shorter than English, so we can use similar or slightly larger sizes.
    """
    # Estimate: Japanese chars are roughly 2x width of English
    est_char_width = 1.2  # approximate CJK char width factor
    est_len = len(text) * est_char_width

    # Try to fit within bbox
    if est_len > 0 and bbox_width > 0:
        size_by_width = (bbox_width / est_len) * 1.8
    else:
        size_by_width = max_size

    size_by_height = bbox_height * 0.85

    final_size = min(size_by_width, size_by_height, max_size)
    final_size = max(final_size, min_size)

    return round(final_size, 1)


def generate_bilingual_pdf(original_pdf_path, blocks_translated, page_images, output_path=None, full_page_translation=None):
    """
    Generate a bilingual PDF: original page as background + Japanese text overlay
    at exact positions of original English text + original images preserved.

    Args:
        original_pdf_path: Path to original PDF file
        blocks_translated: dict mapping block_id -> {text, translation, bbox, page}
            block_id format: "p{PAGE}_b{BLOCK_INDEX}"
        page_images: list of image dicts per page (from layout extraction)
        output_path: Optional path to save PDF. If None, returns bytes.
        full_page_translation: If provided, render this as a single overlay per page
            (used when template engine produced consolidated translation).

    Returns:
        bytes of the generated PDF, or writes to output_path
    """
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF (fitz) not installed. Run: pip install PyMuPDF")
        return None

    if not os.path.exists(original_pdf_path):
        raise FileNotFoundError(f"Original PDF not found: {original_pdf_path}")

    try:
        doc = fitz.open(original_pdf_path)
        output_doc = fitz.open()

        images_by_page = defaultdict(list)
        for img in page_images:
            page_num = img.get('page_number', 1)
            images_by_page[page_num].append(img)

        for page_num in range(doc.page_count):
            original_page = doc.load_page(page_num)
            rect = original_page.rect

            # Create new page with same dimensions
            new_page = output_doc.new_page(width=rect.width, height=rect.height)

            # ─── Copy original page as background image ───
            # Render at high DPI for quality background
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = original_page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            new_page.insert_image(
                rect,
                stream=img_bytes,
            )

            # ─── Overlay Japanese translations at exact positions ───
            matched_blocks = 0
            for block_id, block_data in blocks_translated.items():
                if not block_data.get('translation'):
                    continue

                # Parse page from block_id: p{PAGE}_b{BLOCK}
                try:
                    block_page = int(block_id.split('_')[0][1:])
                except (ValueError, IndexError):
                    continue

                if block_page != page_num + 1:
                    continue

                bbox = block_data.get('bbox', (0, 0, 0, 0))
                translation = block_data['translation']
                original_text = block_data.get('text', '')

                if not translation.strip():
                    continue

                bbox_width = bbox[2] - bbox[0]
                bbox_height = bbox[3] - bbox[1]

                if bbox_width <= 0 or bbox_height <= 0:
                    continue

                # Compute font size to fit within bbox
                font_size = compute_font_size(translation, bbox_width, bbox_height)

                # Create a text color that stands out but is professional
                # Dark blue for translated text
                text_color = (0.05, 0.15, 0.45)  # Dark blue

                # Draw the Japanese text at the exact position
                insert_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])

                # Draw semi-transparent white background for readability
                new_page.draw_rect(
                    insert_rect,
                    color=(1, 1, 1),
                    fill=(1, 1, 1),
                    fill_opacity=0.85,
                    width=0.5,
                )

                # Insert Japanese text
                new_page.insert_textbox(
                    insert_rect,
                    translation,
                    fontname="helv",
                    fontsize=font_size,
                    color=text_color,
                    align=fitz.TEXT_ALIGN_LEFT,
                    render_mode=0,
                    lineheight=1.3,
                )

                matched_blocks += 1

                # ─── Overlay image labels ───
            page_imgs = images_by_page.get(page_num + 1, [])
            for img in page_imgs:
                img_x0, img_y0 = img.get('x0', 0), img.get('y0', 0)
                img_x1, img_y1 = img.get('x1', 0), img.get('y1', 0)
                img_name = img.get('name', f"Image_{page_num + 1}_{img.get('image_index', '?')}")

                # Draw a subtle border around image
                img_rect = fitz.Rect(img_x0, img_y0, img_x1, img_y1)
                new_page.draw_rect(
                    img_rect,
                    color=(0.8, 0.2, 0.2),  # Red border
                    width=1.5,
                    fill=None,
                )

                # Draw image label above or inside the image
                label_rect = fitz.Rect(img_x0, max(0, img_y0 - 16), img_x1, max(0, img_y0))
                if label_rect.y1 <= 0:
                    label_rect = fitz.Rect(img_x0, img_y0, img_x1, img_y0 + 14)

                new_page.insert_textbox(
                    label_rect,
                    f" [{img_name}] ",
                    fontname="helv",
                    fontsize=8,
                    color=(0.8, 0.2, 0.2),
                    align=fitz.TEXT_ALIGN_CENTER,
                )

            # ─── Full-page consolidated translation overlay (template engine output) ───
            if full_page_translation and page_num == 0:
                margin = 72
                overlay_rect = fitz.Rect(
                    rect.x0 + margin,
                    rect.y0 + rect.height * 0.55,
                    rect.x1 - margin,
                    rect.y1 - margin,
                )
                new_page.draw_rect(
                    overlay_rect,
                    color=(1, 1, 1),
                    fill=(1, 1, 1),
                    fill_opacity=0.92,
                    width=0.5,
                )
                font_size = min(
                    (overlay_rect.width / max(len(full_page_translation) * 0.6, 1)) * 2,
                    14
                )
                font_size = max(font_size, 8)
                new_page.insert_textbox(
                    overlay_rect,
                    full_page_translation,
                    fontname="helv",
                    fontsize=font_size,
                    color=(0.05, 0.15, 0.45),
                    align=fitz.TEXT_ALIGN_LEFT,
                    lineheight=1.4,
                )

            logger.info(
                f"Page {page_num + 1}: {matched_blocks} text blocks overlaid, "
                f"{len(page_imgs)} images labeled{f', + full translation overlay' if full_page_translation and page_num == 0 else ''}"
            )

            del original_page

        # Save to bytes
        if output_path:
            output_doc.save(output_path, garbage=4, deflate=True)
            output_doc.close()
            doc.close()
            logger.info(f"Bilingual PDF saved to: {output_path}")
            return output_path
        else:
            buffer = io.BytesIO()
            output_doc.save(buffer, garbage=4, deflate=True)
            output_doc.close()
            doc.close()
            buffer.seek(0)
            logger.info("Bilingual PDF generated in memory")
            return buffer.read()

    except Exception as e:
        logger.error(f"Bilingual PDF generation error: {e}")
        raise


def generate_bilingual_pdf_placeholder(original_pdf_path, blocks_translated, page_images, output_path=None):
    """
    Simplified version: creates a new PDF page by page:
    - Original page as background image
    - Japanese text overlay at exact positions
    - Red boxes around images with labels

    Falls back gracefully if any step fails.
    """
    try:
        return generate_bilingual_pdf(
            original_pdf_path, blocks_translated, page_images, output_path
        )
    except Exception as e:
        logger.error(f"Bilingual PDF generation failed: {e}")
        # Fallback: return None
        return None
