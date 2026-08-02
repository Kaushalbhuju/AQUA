# Enhanced Text Extraction from Images - Documentation

## Overview

The Django translation app now features **advanced OCR (Optical Character Recognition)** capabilities with significant improvements to text extraction from images and scanned PDFs.

## Key Improvements

### 1. **Advanced Image Preprocessing**
The system now uses OpenCV for professional-grade image enhancement:

- **Denoising**: Removes noise and artifacts using Non-Local Means Denoising
- **Adaptive Thresholding**: Automatically chooses between Otsu's binarization and adaptive thresholding based on image characteristics
- **Deskewing**: Detects and corrects skewed text using Hough Line Transform
- **Morphological Operations**: Cleans up small noise and thickens text for better OCR
- **Contrast Enhancement**: Improves low-contrast images automatically
- **Smart Upscaling**: Upscales low-resolution images to optimal size (1000+ pixels)

### 2. **OCR Quality Assessment & Confidence Scoring**
- **Quality Metrics**: Evaluates brightness, contrast, sharpness, and resolution
- **Confidence Scoring**: Each OCR result is scored based on Tesseract's confidence levels
- **Best Result Selection**: Automatically selects the best preprocessing + OCR configuration
- **Quality Warnings**: Provides feedback on image quality issues

### 3. **Multi-Language Support**
- **Automatic Language Detection**: Detects English, Japanese, Chinese, Korean, and Arabic
- **Language Codes**: Supports Tesseract language codes (eng, jpn, chi_sim, kor, ara)
- **Multi-language OCR**: Can process documents with mixed languages (e.g., 'eng+jpn')

### 4. **Adaptive DPI Selection for PDFs**
- **Smart DPI Testing**: Tests multiple DPI levels (150, 200, 300, 400) automatically
- **Early Exit**: Stops testing once good quality is achieved
- **Page-by-Page Processing**: Each page gets optimal DPI selection

### 5. **Advanced OCR Strategies**
- **Multiple PSM Modes**: Tests different Page Segmentation Modes:
  - PSM 6: Uniform block of text
  - PSM 4: Column of text
  - PSM 3: Fully automatic
  - PSM 1: Automatic with OSD
- **Multiple OEM Engines**: Tests both LSTM and Neural Nets LSTM engines
- **Variant Testing**: Tests raw, light preprocessing, and advanced preprocessing

### 6. **Utility Functions**
- **`validate_image_for_ocr()`**: Validates image suitability and provides recommendations
- **`get_extraction_stats()`**: Provides detailed statistics about extracted text
- **`detect_language_from_text()`**: Lightweight language detection

## Installation Requirements

### New Dependencies
The following packages have been added to `requirements.txt`:

```
pytesseract==0.3.10
opencv-python==4.8.1.78
numpy==1.24.3
```

### Tesseract OCR Installation

**Windows:**
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR`
3. Add to system PATH or set environment variable:
   ```
   TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-jpn  # For Japanese
sudo apt-get install tesseract-ocr-chi-sim  # For Chinese
sudo apt-get install tesseract-ocr-kor  # For Korean
sudo apt-get install tesseract-ocr-ara  # For Arabic
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # All language packs
```

### Language Packs
Install language packs for the languages you need:
- English: `eng` (usually pre-installed)
- Japanese: `jpn`
- Chinese Simplified: `chi_sim`
- Korean: `kor`
- Arabic: `ara`

## Usage

### Basic Usage (Automatic)
The system automatically:
1. Detects the language from document content
2. Applies optimal preprocessing
3. Tests multiple OCR configurations
4. Selects the best result based on confidence scoring

```python
from translation.services.extractor import extract_text

# Automatic language detection and extraction
text = extract_text('/path/to/document.pdf', file_type='pdf')

# Or specify language manually
text = extract_text('/path/to/document.jpg', file_type='image', language='jpn')
```

### Image Validation
Check if an image is suitable for OCR before processing:

```python
from translation.services.extractor import validate_image_for_ocr

validation = validate_image_for_ocr('/path/to/image.jpg')

if validation['valid']:
    print(f"Format: {validation['format']}")
    print(f"Dimensions: {validation['dimensions']}")
    print(f"File size: {validation['file_size_mb']} MB")
    if validation['recommendations']:
        print("Recommendations:")
        for rec in validation['recommendations']:
            print(f"  - {rec}")
else:
    print(f"Error: {validation['error']}")
```

### Extraction Statistics
Get detailed statistics about extracted text:

```python
from translation.services.extractor import get_extraction_stats

text = extract_text('/path/to/document.pdf')
stats = get_extraction_stats(text)

print(f"Characters: {stats['char_count']}")
print(f"Words: {stats['word_count']}")
print(f"Lines: {stats['line_count']}")
print(f"Avg word length: {stats['avg_word_length']}")
print(f"Quality score: {stats['quality_score']}%")
print(f"Is quality text: {stats['is_quality_text']}")
```

### Language Detection
Detect the language of text:

```python
from translation.services.extractor import detect_language_from_text

text = "Some sample text to detect..."
language = detect_language_from_text(text)
print(f"Detected language: {language}")  # Returns: 'eng', 'jpn', etc.
```

## Supported File Types

- **Images**: JPG, JPEG, PNG, BMP, TIFF
- **PDFs**: Native PDFs (direct text extraction)
- **Scanned PDFs**: Image-based PDFs (OCR required)

## Performance Considerations

### Processing Time
- **Simple images**: 2-5 seconds
- **Complex documents**: 10-30 seconds
- **Multi-page PDFs**: 5-15 seconds per page

### Optimization Tips
1. **Resolution**: 200-300 DPI is optimal for OCR
2. **File Size**: Keep images under 10MB when possible
3. **Format**: PNG or high-quality JPEG works best
4. **Contrast**: High contrast between text and background improves accuracy

### Memory Usage
- The system processes pages one at a time to minimize RAM usage
- Images are closed immediately after processing
- Temporary data is cleaned up automatically

## Quality Scoring

The quality score (0-100%) is calculated based on:
- **Text Length** (40%): Longer text gets higher scores (up to 400 chars)
- **Word Count** (30%): More words indicate better extraction (up to 150 words)
- **Quality Check** (30%): Passes heuristic tests for valid text

**Score Interpretation:**
- **70-100%**: Excellent extraction, ready for translation
- **40-70%**: Good extraction, may need minor corrections
- **20-40%**: Fair extraction, review recommended
- **0-20%**: Poor extraction, consider re-scanning or manual entry

## Troubleshooting

### Tesseract Not Found
**Error**: `Tesseract is not installed or not in your PATH`

**Solution**:
1. Install Tesseract (see Installation section)
2. Add to PATH or set `TESSDATA_PREFIX` environment variable
3. Restart your Django server

### Poor OCR Results
**Problem**: Extracted text contains garbled characters or missing text

**Solutions**:
1. **Check image quality**: Use `validate_image_for_ocr()` for recommendations
2. **Increase resolution**: Scan at 300 DPI or higher
3. **Improve contrast**: Ensure dark text on light background
4. **Remove noise**: Clean scans without artifacts
5. **Try different language**: Specify correct language code

### Language Detection Issues
**Problem**: Wrong language detected

**Solutions**:
1. **Manual override**: Specify language parameter explicitly
2. **Multi-language**: Use combined codes like `'eng+jpn'`
3. **More text**: Language detection works better with more sample text

### Memory Errors
**Problem**: Out of memory on large files

**Solutions**:
1. **Compress images**: Reduce file size before upload
2. **Lower DPI**: Use 200 DPI instead of 300+
3. **Split PDFs**: Process large PDFs in smaller chunks

## API Reference

### `extract_text(file_path, file_type='pdf', language=None)`
Main extraction function.

**Parameters:**
- `file_path` (str): Path to the file
- `file_type` (str): 'pdf', 'image', or 'scanned_pdf'
- `language` (str, optional): Tesseract language code (auto-detect if None)

**Returns:** Extracted text (str)

### `validate_image_for_ocr(file_path)`
Validate image suitability for OCR.

**Parameters:**
- `file_path` (str): Path to image file

**Returns:** Dict with validation results

### `get_extraction_stats(text)`
Get statistics about extracted text.

**Parameters:**
- `text` (str): Extracted text

**Returns:** Dict with statistics

### `detect_language_from_text(text)`
Detect language from text sample.

**Parameters:**
- `text` (str): Text to analyze

**Returns:** Language code (str)

## Future Enhancements

Potential improvements for future versions:
1. **GPU acceleration** for faster OCR processing
2. **Deep learning models** for better handwriting recognition
3. **Table detection** and structured data extraction
4. **Batch processing** queue for multiple documents
5. **Progress tracking** for long-running extractions
6. **Custom training** for domain-specific documents

## Support

For issues or questions:
1. Check the logs: `logger` provides detailed extraction information
2. Review validation recommendations from `validate_image_for_ocr()`
3. Test with different preprocessing options
4. Consult Tesseract documentation: https://tesseract-ocr.github.io/

## Credits

- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **PyMuPDF**: https://pymupdf.readthedocs.io/
- **OpenCV**: https://opencv.org/
- **Pillow**: https://pillow.readthedocs.io/
