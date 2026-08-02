"""
Layout-preserving PDF extractor.
Extracts text blocks with exact bounding box positions and detects images.
Uses PyMuPDF natively - no Tesseract required for layout extraction.
"""
import logging
import json
import os

logger = logging.getLogger(__name__)


def extract_layout(file_path):
    """
    Extract full layout from a PDF: text blocks with positions + images.

    Args:
        file_path: Absolute path to PDF file

    Returns:
        dict with 'pages' list, each page containing:
          - page_number: int
          - width, height: page dimensions in points
          - text_blocks: list of {x0,y0,x1,y1,text,font,size,block_type}
          - images: list of {x0,y0,x1,y1,width,height,image_index,name}
          - raw_text: full text of the page
    """
    import fitz

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    result = {
        'pages': [],
        'total_text_blocks': 0,
        'total_images': 0,
    }

    try:
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            rect = page.rect

            page_data = {
                'page_number': page_num + 1,
                'width': rect.width,
                'height': rect.height,
                'text_blocks': [],
                'images': [],
                'raw_text': '',
            }

            # ─── Extract text blocks with positions ───
            # Use "dict" mode for fine-grained position data
            text_dict = page.get_text("dict")
            for block in text_dict.get('blocks', []):
                if block.get('type') == 0:  # Text block
                    bbox = block.get('bbox', (0, 0, 0, 0))
                    block_text_parts = []
                    fonts_used = set()
                    sizes_used = set()

                    for line in block.get('lines', []):
                        for span in line.get('spans', []):
                            block_text_parts.append(span.get('text', ''))
                            fonts_used.add(span.get('font', ''))
                            sizes_used.add(span.get('size', 0))

                    text = ''.join(block_text_parts).strip()
                    if text:
                        block_info = {
                            'x0': round(bbox[0], 2),
                            'y0': round(bbox[1], 2),
                            'x1': round(bbox[2], 2),
                            'y1': round(bbox[3], 2),
                            'text': text,
                            'fonts': list(fonts_used),
                            'sizes': [round(s, 1) for s in sizes_used],
                        }
                        page_data['text_blocks'].append(block_info)

                elif block.get('type') == 1:  # Image block
                    bbox = block.get('bbox', (0, 0, 0, 0))
                    img_info = block.get('image', {})
                    img_width = img_info.get('width', 0)
                    img_height = img_info.get('height', 0)
                    transform = block.get('transform', [1, 0, 0, 1, 0, 0])

                    # Infer image name from transform / position
                    img_index = len(page_data['images']) + 1

                    image_info = {
                        'x0': round(bbox[0], 2),
                        'y0': round(bbox[1], 2),
                        'x1': round(bbox[2], 2),
                        'y1': round(bbox[3], 2),
                        'width': round(bbox[2] - bbox[0], 2),
                        'height': round(bbox[3] - bbox[1], 2),
                        'image_width': img_width,
                        'image_height': img_height,
                        'image_index': img_index,
                        'name': f"Image_{page_num + 1}_{img_index}",
                    }
                    page_data['images'].append(image_info)

            # Also get raw text for backward compatibility
            page_data['raw_text'] = page.get_text("text").strip()

            result['pages'].append(page_data)
            result['total_text_blocks'] += len(page_data['text_blocks'])
            result['total_images'] += len(page_data['images'])

            del page

        doc.close()
        logger.info(
            f"Layout extracted: {doc.page_count} pages, "
            f"{result['total_text_blocks']} text blocks, "
            f"{result['total_images']} images"
        )

    except Exception as e:
        logger.error(f"Layout extraction error: {e}")
        raise

    return result


def detect_images_in_pdf(file_path, page_number=0):
    """
    Extract image data from a specific PDF page.

    Args:
        file_path: Absolute path to PDF file
        page_number: Page index (0-based)

    Returns:
        list of image info dicts with position and dimensions
    """
    import fitz

    doc = fitz.open(file_path)
    page = doc.load_page(page_number)
    images = []

    for block in page.get_text("dict").get('blocks', []):
        if block.get('type') == 1:
            bbox = block.get('bbox', (0, 0, 0, 0))
            img_info = block.get('image', {})
            img_index = len(images) + 1
            images.append({
                'x0': round(bbox[0], 2),
                'y0': round(bbox[1], 2),
                'x1': round(bbox[2], 2),
                'y1': round(bbox[3], 2),
                'width': round(bbox[2] - bbox[0], 2),
                'height': round(bbox[3] - bbox[1], 2),
                'name': f"Image_{page_number + 1}_{img_index}",
                'image_px_width': img_info.get('width', 0),
                'image_px_height': img_info.get('height', 0),
            })

    doc.close()
    return images


def extract_text_with_positions(file_path):
    """
    Extract text grouped by paragraphs with position info.
    Returns text suitable for translation with position mapping.
    """
    layout = extract_layout(file_path)

    text_with_positions = {}
    full_text_parts = []

    for page in layout['pages']:
        for i, block in enumerate(page['text_blocks']):
            block_id = f"p{page['page_number']}_b{i}"
            text_with_positions[block_id] = {
                'text': block['text'],
                'bbox': (block['x0'], block['y0'], block['x1'], block['y1']),
                'page': page['page_number'],
            }
            full_text_parts.append(block['text'])

    full_text = '\n'.join(full_text_parts)

    return {
        'full_text': full_text,
        'blocks': text_with_positions,
        'layout_data': layout,
    }
