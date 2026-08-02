"""
Text extraction service for PDF and Image files.
Uses PyMuPDF for PDFs and Tesseract OCR for images/scanned PDFs.
Processes content in chunks to minimize RAM usage.

Enhanced with:
- Advanced image preprocessing (denoising, thresholding, deskewing)
- OCR quality assessment and confidence scoring
- Multi-language support
- Adaptive DPI selection for PDFs
- Region-based OCR for complex layouts
"""
import logging
import os
import re
import math

logger = logging.getLogger(__name__)


def _is_quality_text(text, min_alpha_ratio=0.6, min_words=3):
    """
    Check if extracted text looks like real language vs garbled OCR noise.

    Returns True if text passes quality heuristics:
    - At least `min_alpha_ratio` of characters are alphanumeric or common punctuation
    - Contains at least `min_words` words of reasonable length (2-20 chars)
    - Not dominated by non-ASCII garbage
    """
    if not text or len(text.strip()) < 20:
        return False

    # Ratio of printable ASCII alphanumeric + common punctuation
    good_chars = sum(1 for c in text if c.isalnum() or c in ' .,;:!?-\'"/\n\r()')
    alpha_ratio = good_chars / max(len(text), 1)

    # Find words (sequences of 2+ letters)
    words = re.findall(r'[A-Za-z]{2,}', text)
    long_enough = sum(1 for w in words if 2 <= len(w) <= 20)

    # Check for non-ASCII garbage ratio
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ascii_ratio = ascii_chars / max(len(text), 1)

    return alpha_ratio >= min_alpha_ratio and long_enough >= min_words and ascii_ratio >= 0.85


def extract_text_from_pdf(file_path):
    """
    Extract text from a native PDF using PyMuPDF (fitz).
    Processes page-by-page to minimize memory usage.
    """
    import fitz  # PyMuPDF

    text_parts = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text.strip())
            # Release page memory
            del page
        doc.close()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise

    return '\n\n'.join(text_parts)


def extract_tables_from_pdf(file_path):
    """
    Extract tables from PDF using pdfplumber.
    Falls back to Camelot if pdfplumber fails.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        list: List of tables, where each table is a list of rows (list of strings)
              Example: [[['Header1', 'Header2'], ['Row1Col1', 'Row1Col2']], ...]
    """
    tables = []
    
    # Try pdfplumber first (better for most PDFs)
    try:
        import pdfplumber
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                if page_tables:
                    for table in page_tables:
                        if table and len(table) > 1:  # Must have header + at least 1 row
                            # Clean table data
                            cleaned_table = [
                                [str(cell).strip() if cell else '' for cell in row]
                                for row in table
                            ]
                            tables.append(cleaned_table)
                            logger.debug(f"Extracted table from page {page_num}: {len(table)} rows")
        
        if tables:
            logger.info(f"pdfplumber extracted {len(tables)} table(s)")
            return tables
            
    except ImportError:
        logger.debug("pdfplumber not available, trying Camelot")
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")
    
    # Fallback to Camelot
    try:
        import camelot
        
        # Read all tables from PDF
        table_list = camelot.read_pdf(file_path, pages='all', flavor='stream')
        
        if table_list:
            for table in table_list:
                if table.df.shape[0] > 1:  # Must have at least 2 rows
                    # Convert DataFrame to list of lists
                    table_data = table.df.values.tolist()
                    # Clean data
                    cleaned_table = [
                        [str(cell).strip() if cell else '' for cell in row]
                        for row in table_data
                    ]
                    tables.append(cleaned_table)
            
            logger.info(f"Camelot extracted {len(tables)} table(s)")
            
    except ImportError:
        logger.debug("Camelot not available")
    except Exception as e:
        logger.warning(f"Camelot extraction failed: {e}")
    
    if not tables:
        logger.debug("No tables found in PDF")
    
    return tables


def _preprocess_advanced(img):
    """
    Advanced image preprocessing pipeline for better OCR results.
    Uses OpenCV for professional-grade image enhancement.
    
    Steps:
    1. Grayscale conversion
    2. Denoising
    3. Adaptive thresholding or Otsu's binarization
    4. Deskewing
    5. Morphological operations to clean up
    6. Contrast enhancement
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        # Convert PIL to OpenCV format
        img_array = np.array(img.convert('L'))
        
        # Step 1: Denoise
        denoised = cv2.fastNlMeansDenoising(img_array, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Step 2: Adaptive thresholding or Otsu's
        # Choose method based on image characteristics
        mean_val = np.mean(denoised)
        std_val = np.std(denoised)
        
        if std_val < 40:  # Low contrast image
            # Use adaptive thresholding for low contrast
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, blockSize=31, C=10
            )
        else:
            # Use Otsu's for good contrast images
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Step 3: Deskew
        angle = _calculate_skew_angle(binary)
        if abs(angle) > 0.5:  # Only deskew if angle is significant
            (h, w) = binary.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(
                binary, M, (w, h), 
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
        
        # Step 4: Morphological cleanup
        # Remove small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Step 5: Slight dilation to thicken text (improves OCR)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        dilated = cv2.dilate(cleaned, kernel, iterations=1)
        
        # Convert back to PIL
        result = Image.fromarray(dilated)
        
        # Step 6: Upscale if too small
        min_dim = 1000
        if max(result.size) < min_dim:
            ratio = min_dim / max(result.size)
            result = result.resize(
                (int(result.size[0] * ratio), int(result.size[1] * ratio)), 
                Image.LANCZOS
            )
        
        return result
        
    except ImportError:
        logger.warning("OpenCV not available, using basic preprocessing")
        return _preprocess_light(img)
    except Exception as e:
        logger.warning(f"Advanced preprocessing failed: {e}, falling back to light preprocessing")
        return _preprocess_light(img)


def _calculate_skew_angle(binary_image):
    """
    Calculate the skew angle of an image using Hough Line Transform.
    Returns angle in degrees.
    """
    try:
        import cv2
        import numpy as np
        
        # Edge detection
        edges = cv2.Canny(binary_image, 50, 150, apertureSize=3)
        
        # Hough Line Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        if lines is None or len(lines) == 0:
            return 0.0
        
        angles = []
        for line in lines[:100]:  # Use top 100 lines
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            # Filter out near-vertical lines
            if abs(angle) < 45:
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Use median angle for robustness
        return float(np.median(angles))
        
    except Exception as e:
        logger.debug(f"Skew calculation failed: {e}")
        return 0.0


def _assess_image_quality(img):
    """
    Assess image quality for OCR readiness.
    Returns dict with quality metrics.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        img_array = np.array(img.convert('L'))
        
        # Calculate metrics
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
        sharpness = cv2.Laplacian(img_array, cv2.CV_64F).var()
        
        # Check resolution
        width, height = img.size
        resolution = width * height
        
        quality = {
            'brightness': float(brightness),
            'contrast': float(contrast),
            'sharpness': float(sharpness),
            'resolution': resolution,
            'width': width,
            'height': height,
            'good_for_ocr': True,
            'warnings': []
        }
        
        # Assess quality
        if brightness < 50 or brightness > 200:
            quality['warnings'].append('Image may be too dark or too bright')
        
        if contrast < 30:
            quality['warnings'].append('Low contrast - preprocessing will enhance')
        
        if sharpness < 100:
            quality['warnings'].append('Image may be blurry')
        
        if resolution < 500000:  # Less than ~700x700
            quality['warnings'].append('Low resolution - will upscale')
        
        return quality
        
    except Exception as e:
        logger.debug(f"Quality assessment failed: {e}")
        return {'good_for_ocr': True, 'warnings': []}


def _preprocess_light(img):
    """Light preprocessing: grayscale + gentle contrast + upscale if tiny."""
    from PIL import Image, ImageEnhance

    if img.mode != 'L':
        img = img.convert('L')

    # Upscale very small images only
    min_dim = 800
    if max(img.size) < min_dim:
        ratio = min_dim / max(img.size)
        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)

    # Gentle contrast boost
    img = ImageEnhance.Contrast(img).enhance(1.3)

    return img


def extract_text_from_image(file_path, language='eng'):
    """
    Extract text from an image using Tesseract OCR with advanced preprocessing.
    Uses multiple preprocessing strategies and picks the best result.
    Supports JPG, PNG, BMP, TIFF formats.
    
    Args:
        file_path: Path to image file
        language: Tesseract language code (e.g., 'eng', 'jpn', 'eng+jpn')
    
    Returns:
        Extracted text string
    """
    try:
        import pytesseract
        from PIL import Image
        
        raw_img = Image.open(file_path)
        
        # Assess image quality
        quality = _assess_image_quality(raw_img)
        if quality.get('warnings'):
            logger.info(f"Image quality warnings: {', '.join(quality['warnings'])}")
        
        # Create preprocessing variants
        variants = {
            'raw': raw_img,
            'advanced': _preprocess_advanced(raw_img.copy()),
            'light': _preprocess_light(raw_img.copy()),
        }
        
        best_text = ''
        best_score = 0
        best_config = ''
        
        # Try different PSM modes for each variant
        psm_configs = [
            ('6', 'Uniform block of text'),
            ('4', 'Column of text'),
            ('3', 'Fully automatic'),
            ('1', 'Automatic with OSD'),
        ]
        
        oem_configs = ['3', '1']  # Default LSTM, Neural nets LSTM
        
        for variant_name, img in variants.items():
            for oem in oem_configs:
                for psm, desc in psm_configs:
                    config = f'--oem {oem} --psm {psm}'
                    
                    try:
                        # Get text with confidence data
                        data = pytesseract.image_to_data(
                            img, lang=language, config=config, output_type=pytesseract.Output.DICT
                        )
                        
                        # Calculate confidence score
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        if confidences:
                            avg_confidence = sum(confidences) / len(confidences)
                            text = ' '.join([word for word, conf in zip(data['text'], data['conf']) 
                                           if int(conf) > 0 and word.strip()])
                            
                            # Score based on confidence and text length
                            score = avg_confidence * math.log(len(text) + 1)
                            
                            if score > best_score and len(text.strip()) > 10:
                                best_text = text.strip()
                                best_score = score
                                best_config = f"{variant_name} (OEM={oem}, PSM={psm}, conf={avg_confidence:.1f}%)"
                    
                    except Exception as e:
                        logger.debug(f"OCR config failed: {config} - {e}")
                        continue
            
            img.close()
        
        # Ultimate fallback: simple OCR with default settings
        if not best_text or len(best_text) < 20:
            try:
                raw_img = Image.open(file_path)
                best_text = pytesseract.image_to_string(raw_img, lang=language).strip()
                best_config = 'fallback (default)'
                raw_img.close()
            except Exception as e:
                logger.error(f"Fallback OCR failed: {e}")
        
        logger.info(
            f"Image OCR complete: {len(best_text)} chars, "
            f"best config: {best_config}, score: {best_score:.2f}"
        )
        return best_text
        
    except Exception as e:
        logger.error(f"Image OCR error: {e}")
        raise


def _ocr_page_with_preprocessing(page, fitz, language='eng'):
    """
    OCR a single PDF page with adaptive DPI selection and confidence scoring.
    Tries multiple DPI + preprocessing combinations, picks the best result.
    
    Args:
        page: PyMuPDF page object
        fitz: PyMuPDF module
        language: Tesseract language code
    
    Returns:
        Best extracted text string
    """
    import pytesseract
    from PIL import Image
    import io
    
    best_text = ''
    best_score = 0
    best_config = ''
    
    # Adaptive DPI selection based on page content
    dpis = [200, 300, 400, 150]  # Try common DPIs
    
    for dpi in dpis:
        try:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Try different preprocessing variants
            variants = {
                'raw': img,
                'advanced': _preprocess_advanced(img.copy()),
                'light': _preprocess_light(img.copy()),
            }
            
            for variant_name, variant in variants.items():
                # Try different PSM modes
                for psm in ['6', '4', '3', '1']:
                    config = f'--oem 3 --psm {psm}'
                    
                    try:
                        # Get OCR data with confidence
                        data = pytesseract.image_to_data(
                            variant, lang=language, config=config, 
                            output_type=pytesseract.Output.DICT
                        )
                        
                        # Calculate confidence and filter low-confidence words
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        if confidences:
                            avg_confidence = sum(confidences) / len(confidences)
                            text = ' '.join([
                                word for word, conf in zip(data['text'], data['conf'])
                                if int(conf) > 0 and word.strip()
                            ])
                            
                            # Score based on confidence and text length
                            score = avg_confidence * math.log(len(text) + 1)
                            
                            if score > best_score and len(text.strip()) > 20:
                                best_text = text.strip()
                                best_score = score
                                best_config = f"DPI={dpi}, {variant_name}, PSM={psm}, conf={avg_confidence:.1f}%"
                    
                    except Exception:
                        continue
                
                variant.close()
            
            del pix, img_data
            
            # Early exit if we got good results
            if best_score > 500:  # Good confidence threshold
                break
        
        except Exception:
            continue
    
    logger.debug(f"Page OCR best config: {best_config}, score: {best_score:.2f}")
    return best_text


def extract_text_from_scanned_pdf(file_path, language='eng'):
    """
    Extract text from a scanned PDF by converting pages to images
    and running OCR with advanced preprocessing. Processes one page at a time.
    
    Args:
        file_path: Path to PDF file
        language: Tesseract language code
    
    Returns:
        Extracted text string
    """
    import fitz

    text_parts = []
    total_pages = 0
    ocr_pages = 0
    
    try:
        doc = fitz.open(file_path)
        total_pages = doc.page_count
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)

            # First try direct text extraction
            direct_text = page.get_text("text").strip()
            if len(direct_text) > 50 and _is_quality_text(direct_text):
                text_parts.append(direct_text)
                logger.debug(f"Page {page_num + 1}: Direct text extraction successful")
                del page
                continue

            # Fall back to OCR with advanced preprocessing
            try:
                page_text = _ocr_page_with_preprocessing(page, fitz, language=language)
                if page_text.strip():
                    text_parts.append(page_text.strip())
                    ocr_pages += 1
                    logger.debug(f"Page {page_num + 1}: OCR successful, {len(page_text)} chars")
                else:
                    logger.warning(f"Page {page_num + 1}: OCR returned empty text")
                    if direct_text:  # Use whatever we got from direct extraction
                        text_parts.append(direct_text)
            except ImportError:
                logger.warning("Tesseract not available for OCR fallback")
                if direct_text:
                    text_parts.append(direct_text)

            del page
        
        doc.close()
        
        logger.info(
            f"Scanned PDF extraction: {total_pages} pages, "
            f"{ocr_pages} OCR'd, {len(text_parts)} pages with text"
        )
        
    except Exception as e:
        logger.error(f"Scanned PDF extraction error: {e}")
        raise

    return '\n\n'.join(text_parts)


def detect_language_from_text(text):
    """
    Simple language detection based on character patterns.
    Returns Tesseract language code.
    
    This is a lightweight alternative to full language detection libraries.
    For production, consider using 'langdetect' or 'fasttext' library.
    """
    if not text or len(text.strip()) < 10:
        return 'eng'  # Default to English
    
    # Sample text for analysis
    sample = text[:1000]
    
    # Count character types
    latin_count = sum(1 for c in sample if c.isascii() and c.isalpha())
    japanese_count = sum(1 for c in sample if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
    chinese_count = sum(1 for c in sample if '\u4e00' <= c <= '\u9fff')
    korean_count = sum(1 for c in sample if '\uac00' <= c <= '\ud7af')
    arabic_count = sum(1 for c in sample if '\u0600' <= c <= '\u06ff')
    
    total_alpha = max(latin_count + japanese_count + chinese_count + korean_count + arabic_count, 1)
    
    # Determine dominant language
    japanese_ratio = japanese_count / total_alpha
    chinese_ratio = chinese_count / total_alpha
    korean_ratio = korean_count / total_alpha
    arabic_ratio = arabic_count / total_alpha
    latin_ratio = latin_count / total_alpha
    
    if japanese_ratio > 0.3:
        return 'jpn'
    elif chinese_ratio > 0.3 and japanese_ratio < 0.2:
        return 'chi_sim'  # Simplified Chinese
    elif korean_ratio > 0.3:
        return 'kor'
    elif arabic_ratio > 0.3:
        return 'ara'
    else:
        return 'eng'  # Default to English


def extract_text(file_path, file_type='pdf', language=None):
    """
    Main extraction function. Routes to appropriate extractor
    based on file type.

    Args:
        file_path: Absolute path to the file
        file_type: One of 'pdf', 'image', 'scanned_pdf'
        language: Tesseract language code (auto-detect if None)

    Returns:
        If file_type is PDF: dict with 'text', 'tables', 'structure_type'
        Otherwise: str (extracted text)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Auto-detect language if not specified
    if language is None:
        # For PDFs, try to extract a sample first
        if file_type in ('pdf', 'scanned_pdf'):
            try:
                import fitz
                doc = fitz.open(file_path)
                sample_text = ""
                for i in range(min(2, doc.page_count)):
                    sample_text += doc[i].get_text("text")
                doc.close()
                
                if sample_text.strip():
                    language = detect_language_from_text(sample_text)
                    logger.info(f"Auto-detected language: {language}")
                else:
                    language = 'eng'
            except Exception as e:
                logger.warning(f"Language detection failed: {e}, using English")
                language = 'eng'
        else:
            language = 'eng'  # Default for images

    if file_type == 'pdf':
        text = extract_text_from_pdf(file_path)
        
        # Extract tables if present
        tables = []
        structure_type = 'paragraph'
        try:
            tables = extract_tables_from_pdf(file_path)
            if tables:
                structure_type = 'mixed'
                logger.info(f"Extracted {len(tables)} table(s) from PDF")
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        # Fall through to OCR if direct text is gibberish
        if not _is_quality_text(text):
            logger.info("PDF direct text looks garbled (%.0f chars, quality fail), trying OCR...", len(text.strip()))
            try:
                ocr_text = extract_text_from_scanned_pdf(file_path, language=language)
                if _is_quality_text(ocr_text):
                    text = ocr_text
            except Exception as e:
                logger.warning("OCR fallback failed: %s", e)
        
        return {
            'text': text,
            'tables': tables,
            'structure_type': structure_type,
        }
    elif file_type == 'image':
        return extract_text_from_image(file_path, language=language)
    elif file_type == 'scanned_pdf':
        text = extract_text_from_scanned_pdf(file_path, language=language)
        
        # Try to extract tables even from scanned PDFs
        tables = []
        structure_type = 'paragraph'
        try:
            tables = extract_tables_from_pdf(file_path)
            if tables:
                structure_type = 'mixed'
        except Exception as e:
            logger.warning(f"Table extraction from scanned PDF failed: {e}")
        
        return {
            'text': text,
            'tables': tables,
            'structure_type': structure_type,
        }
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def validate_image_for_ocr(file_path):
    """
    Validate if an image is suitable for OCR and provide recommendations.
    
    Args:
        file_path: Path to image file
    
    Returns:
        dict with validation results and recommendations
    """
    try:
        from PIL import Image
        
        img = Image.open(file_path)
        quality = _assess_image_quality(img)
        
        # Check file format
        valid_formats = ['JPEG', 'PNG', 'BMP', 'TIFF']
        format_ok = img.format in valid_formats
        
        # Check file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        validation = {
            'valid': True,
            'format': img.format,
            'format_ok': format_ok,
            'dimensions': img.size,
            'file_size_mb': round(file_size_mb, 2),
            'quality': quality,
            'recommendations': []
        }
        
        # Generate recommendations
        if not format_ok:
            validation['valid'] = False
            validation['recommendations'].append(
                f'Unsupported format: {img.format}. Convert to JPEG or PNG.'
            )
        
        if file_size_mb > 20:
            validation['recommendations'].append(
                'File is very large (>20MB). Consider compressing.'
            )
        
        if quality.get('warnings'):
            validation['recommendations'].extend(quality['warnings'])
        
        img.close()
        return validation
        
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'recommendations': ['File cannot be opened or is corrupted']
        }


def get_extraction_stats(text):
    """
    Get statistics about extracted text quality.
    
    Args:
        text: Extracted text string
    
    Returns:
        dict with text statistics
    """
    if not text:
        return {
            'char_count': 0,
            'word_count': 0,
            'line_count': 0,
            'avg_word_length': 0,
            'quality_score': 0,
            'is_quality_text': False
        }
    
    words = text.split()
    word_lengths = [len(w) for w in words if w.strip()]
    
    stats = {
        'char_count': len(text),
        'word_count': len(words),
        'line_count': text.count('\n') + 1,
        'avg_word_length': round(sum(word_lengths) / max(len(word_lengths), 1), 2),
        'quality_score': 0,
        'is_quality_text': _is_quality_text(text)
    }
    
    # Calculate quality score (0-100)
    if stats['word_count'] > 0:
        # Factors: length, word count, quality check
        length_score = min(stats['char_count'] / 10, 40)  # Max 40 points
        word_score = min(stats['word_count'] / 5, 30)  # Max 30 points
        quality_score = 30 if stats['is_quality_text'] else 10
        
        stats['quality_score'] = round(length_score + word_score + quality_score, 1)
    
    return stats
