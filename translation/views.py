import io
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from translation.models import Document, DocumentType, TranslationMemory, TranslationHistory
from translation.forms import (
    DocumentUploadForm,
    DocumentTypeOverrideForm,
    TranslationReviewForm,
    TranslationMemoryForm,
    TranslationMemorySearchForm,
)
from translation.services.extractor import extract_text, validate_image_for_ocr, get_extraction_stats
from translation.services.layout_extractor import extract_layout, extract_text_with_positions
from translation.services.detector import detect_document_type, seed_document_types
from translation.services.translator import translate_text, save_translation_memory
from translation.services.docx_generator import generate_translated_docx
from translation.services.layout_renderer import generate_bilingual_pdf
from translation.services.parsers import get_parser_for_document
from translation.services.parsers.character_certificate import parse_character_certificate

logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 15


# ─── Dashboard ──────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """Translation dashboard with stats and recent activity."""
    total_documents = Document.objects.count()
    translated_documents = Document.objects.filter(
        status__in=['translated', 'reviewing', 'completed']
    ).count()
    tm_count = TranslationMemory.objects.count()
    pending_review = Document.objects.filter(status='translated').count()

    recent_documents = Document.objects.select_related(
        'document_type', 'uploaded_by'
    ).order_by('-created_at')[:10]

    recent_history = TranslationHistory.objects.select_related(
        'document', 'user'
    ).order_by('-created_at')[:15]

    # Stats by document type
    type_stats = Document.objects.values(
        'document_type__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Stats by status
    status_stats = Document.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'total_documents': total_documents,
        'translated_documents': translated_documents,
        'tm_count': tm_count,
        'pending_review': pending_review,
        'recent_documents': recent_documents,
        'recent_history': recent_history,
        'type_stats': type_stats,
        'status_stats': status_stats,
    }
    return render(request, 'translation/dashboard.html', context)


# ─── Document Upload ────────────────────────────────────────────────────────

@login_required
def document_upload(request):
    """Upload a new document for translation."""
    # Ensure document types exist
    seed_document_types()

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.status = 'uploaded'
            doc.save()

            TranslationHistory.objects.create(
                document=doc,
                action='upload',
                details=f'Document "{doc.title}" uploaded ({doc.file_type})',
                user=request.user,
            )

            messages.success(request, f'Document "{doc.title}" uploaded successfully.')
            return redirect('translation:document_process', pk=doc.pk)
    else:
        form = DocumentUploadForm()

    return render(request, 'translation/document_upload.html', {'form': form})


# ─── Document Process (Extract → Detect → Translate) ───────────────────────

@login_required
def document_process(request, pk):
    """
    Process a document: extract text, detect type, and translate.
    Steps shown to user with progress feedback.
    """
    doc = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'extract':
            return _handle_extraction(request, doc)
        elif action == 'detect':
            return _handle_detection(request, doc)
        elif action == 'override_type':
            return _handle_type_override(request, doc)
        elif action == 'translate':
            return _handle_translation(request, doc)
        elif action == 'update_extracted':
            return _handle_update_extracted(request, doc)
        elif action == 'update_translated':
            return _handle_update_translated(request, doc)
        elif action == 'update_fields':
            return _handle_update_fields(request, doc)

    override_form = DocumentTypeOverrideForm(
        initial={'document_type': doc.document_type}
    )

    # Build structured Character Certificate context (second stage)
    structured_fields = None
    structured_flat = None
    field_confidences = {}
    try:
        layout = doc.parsed_layout
        sd = layout.get('structured_data', {})
        # structured_data may be the new service format with flat/spec
        if isinstance(sd, dict) and sd.get('flat'):
            structured_flat = sd.get('flat')
            # also expose per-field confidence if available
            if sd.get('fields'):
                field_confidences = sd.get('fields', {})
        elif isinstance(sd, dict) and sd.get('fields'):
            # legacy parser result format
            raw = sd.get('fields', {})
            # Re-run mapping to spec flat for display
            from translation.services.parsers.character_certificate import _spec_mapped_fields  # noqa
            structured_flat = _spec_mapped_fields(raw)
            field_confidences = sd.get('fields', {})
            # Also try to get detailed fields if present
            if sd.get('metadata'):
                pass
        # If still empty, try live parse for Character Certificate types for preview
        if not structured_flat:
            doc_type_name = (doc.document_type.name if doc.document_type else '') or (doc.auto_detected_type.name if doc.auto_detected_type else '')
            is_char = 'Character Certificate' in doc_type_name or 'character' in doc_type_name.lower() or 'NEB Certificate' in doc_type_name
            if is_char and doc.extracted_text:
                live = parse_character_certificate(doc.extracted_text)
                structured_flat = live.get('flat', {})
                field_confidences = live.get('fields', {})
    except Exception:
        pass

    context = {
        'document': doc,
        'override_form': override_form,
        'structured_fields': structured_fields,
        'structured_flat': structured_flat,
        'field_confidences': field_confidences,
    }
    return render(request, 'translation/document_process.html', context)


def _handle_extraction(request, doc):
    """Extract text and layout from uploaded document."""
    try:
        doc.status = 'extracting'
        doc.save(update_fields=['status'])

        file_path = doc.original_file.path
        
        # Validate image before OCR (for image files)
        if doc.file_type == 'image':
            validation = validate_image_for_ocr(file_path)
            if validation.get('recommendations'):
                for rec in validation['recommendations']:
                    logger.info(f"Image validation: {rec}")
        
        # Extract text (now returns dict for PDFs with tables)
        extraction_result = extract_text(file_path, doc.file_type)
        
        # Handle both old string format and new dict format
        if isinstance(extraction_result, dict):
            extracted_text = extraction_result.get('text', '')
            tables = extraction_result.get('tables', [])
            structure_type = extraction_result.get('structure_type', 'paragraph')
        else:
            extracted_text = extraction_result
            tables = []
            structure_type = 'paragraph'

        doc.extracted_text = extracted_text
        doc.status = 'extracted'
        doc.save(update_fields=['extracted_text', 'status'])
        
        # Get extraction statistics
        stats = get_extraction_stats(extracted_text)
        logger.info(f"Extraction stats: {stats}")

        # Auto-detect type if not set, so field extraction can run as second stage
        if not doc.document_type and extracted_text:
            try:
                auto = detect_document_type(extracted_text)
                if auto:
                    doc.auto_detected_type = auto
                    doc.document_type = auto
                    doc.save(update_fields=['auto_detected_type', 'document_type'])
                    logger.info(f"Auto-detected during extraction: {auto.name}")
            except Exception as e:
                logger.debug(f"Auto-detect during extraction failed: {e}")

        # SECOND STAGE: Character Certificate field extraction (RAW OCR -> structured)
        # Runs for Character Certificate / NEB Certificate; keeps RAW OCR as extracted_text
        structured_data = {}
        doc_type_name = (doc.document_type.name if doc.document_type else '')
        # Also treat NEB Certificate as Character Certificate for field extraction
        is_character = ('Character Certificate' in doc_type_name or 'character' in doc_type_name.lower() or 'NEB Certificate' in doc_type_name)
        # Fallback: if still unknown, try character parser speculatively and keep if confident
        try_parse = is_character or not doc.document_type
        if try_parse and extracted_text:
            try:
                # Use the position-independent service API
                svc = parse_character_certificate(extracted_text)
                # Store both flat spec and detailed fields for UI/editing
                structured_data = {
                    'fields': svc.get('raw_fields', {}),
                    'flat': svc.get('flat', {}),
                    'detailed': svc.get('fields', {}),
                    'metadata': svc.get('metadata', {}),
                }
                # Also keep legacy parser path for compatibility
                parser = get_parser_for_document('Character Certificate')
                parser_result = parser.parse(extracted_text, layout_data=doc.parsed_layout if hasattr(doc, 'parsed_layout') else None, tables=tables)
                # Merge legacy fields if svc missed something
                for k, v in parser_result.fields.items():
                    if k not in structured_data['fields'] and v:
                        structured_data['fields'][k] = v
                logger.info(f"Character Certificate field extraction: {len(structured_data['fields'])} fields, overall_conf={svc['metadata'].get('overall_confidence',0):.2f}")
            except Exception as e:
                logger.warning(f"Character Certificate field extraction failed: {e}")
                # Fallback to legacy parser if service fails
                if doc.document_type:
                    try:
                        parser = get_parser_for_document(doc.document_type.name)
                        parser_result = parser.parse(extracted_text, layout_data=doc.parsed_layout if hasattr(doc, 'parsed_layout') else None, tables=tables)
                        structured_data = parser_result.to_dict()
                    except Exception as e2:
                        logger.warning(f"Legacy parsing also failed: {e2}")

        # New: extract layout data for PDFs (text blocks with positions + images)
        if doc.file_type in ('pdf', 'scanned_pdf'):
            try:
                layout_result = extract_text_with_positions(file_path)
                layout_data = layout_result.get('layout_data', {'pages': []})
                # Also save the block-level mapping for bilingual PDF generation
                layout_data['_blocks'] = {
                    bid: {
                        'text': bdata.get('text', ''),
                        'bbox': list(bdata.get('bbox', (0,0,0,0))),
                        'page': bdata.get('page', 1),
                    }
                    for bid, bdata in layout_result.get('blocks', {}).items()
                }
                # Add structured data from parser
                if structured_data:
                    layout_data['structured_data'] = structured_data
                    layout_data['structure_type'] = structure_type
                    
                doc.parsed_layout = layout_data
                doc.save(update_fields=['layout_data'])
                img_count = layout_result['layout_data'].get('total_images', 0)
                block_count = layout_result['layout_data'].get('total_text_blocks', 0)
                extra = f', {block_count} text blocks, {img_count} images detected'
                if tables:
                    extra += f', {len(tables)} tables extracted'
                if structured_data:
                    extra += f', {len(structured_data.get("fields", {}))} fields parsed'
            except Exception as e:
                logger.warning(f"Layout extraction optional step failed: {e}")
                extra = ''
        else:
            extra = ''

        TranslationHistory.objects.create(
            document=doc,
            action='extract',
            details=f'Text extracted: {stats["char_count"]} chars, {stats["word_count"]} words, quality: {stats["quality_score"]}%{extra}',
            user=request.user,
        )

        messages.success(
            request, 
            f'Text extracted successfully: {stats["char_count"]} characters, '
            f'{stats["word_count"]} words (quality: {stats["quality_score"]}%)'
        )
    except Exception as e:
        doc.status = 'failed'
        doc.error_message = str(e)
        doc.save(update_fields=['status', 'error_message'])

        TranslationHistory.objects.create(
            document=doc,
            action='error',
            details=f'Extraction failed: {str(e)}',
            user=request.user,
        )
        messages.error(request, f'Text extraction failed: {str(e)}')

    return redirect('translation:document_process', pk=doc.pk)


def _handle_detection(request, doc):
    """Auto-detect document type."""
    detected = detect_document_type(doc.extracted_text)
    if detected:
        doc.auto_detected_type = detected
        if not doc.document_type:
            doc.document_type = detected
        doc.save(update_fields=['auto_detected_type', 'document_type'])
        messages.success(request, f'Document type detected: {detected.name}')
        # If character/NEB, run field extraction as second stage immediately
        if detected and ('Character Certificate' in detected.name or 'character' in detected.name.lower() or 'NEB Certificate' in detected.name):
            if doc.extracted_text:
                try:
                    svc = parse_character_certificate(doc.extracted_text)
                    layout = doc.parsed_layout
                    layout['structured_data'] = {'fields': svc.get('raw_fields', {}), 'flat': svc.get('flat', {}), 'detailed': svc.get('fields', {}), 'metadata': svc.get('metadata', {})}
                    doc.parsed_layout = layout
                    doc.save(update_fields=['layout_data'])
                except Exception as e:
                    logger.warning(f"Field extraction after detect failed: {e}")
    else:
        messages.warning(request, 'Could not auto-detect document type. Please select manually.')

    return redirect('translation:document_process', pk=doc.pk)


def _handle_type_override(request, doc):
    """Manually override document type."""
    form = DocumentTypeOverrideForm(request.POST)
    if form.is_valid():
        doc.document_type = form.cleaned_data['document_type']
        doc.save(update_fields=['document_type'])
        messages.success(request, f'Document type set to: {doc.document_type.name}')
        # Run field extraction if character/NEB selected
        name = doc.document_type.name if doc.document_type else ''
        if 'Character Certificate' in name or 'character' in name.lower() or 'NEB Certificate' in name:
            if doc.extracted_text:
                try:
                    svc = parse_character_certificate(doc.extracted_text)
                    layout = doc.parsed_layout
                    layout['structured_data'] = {'fields': svc.get('raw_fields', {}), 'flat': svc.get('flat', {}), 'detailed': svc.get('fields', {}), 'metadata': svc.get('metadata', {})}
                    doc.parsed_layout = layout
                    doc.save(update_fields=['layout_data'])
                except Exception as e:
                    logger.warning(f"Field extraction after override failed: {e}")
    return redirect('translation:document_process', pk=doc.pk)


def _handle_translation(request, doc):
    """Translate extracted text using TM-first strategy."""
    try:
        doc.status = 'translating'
        doc.save(update_fields=['status'])

        translated = translate_text(
            doc.extracted_text,
            document_type=doc.document_type,
            document=doc,
        )

        doc.translated_text = translated
        doc.status = 'translated'
        doc.save(update_fields=['translated_text', 'status'])

        messages.success(request, 'Translation completed successfully.')
    except Exception as e:
        doc.status = 'failed'
        doc.error_message = str(e)
        doc.save(update_fields=['status', 'error_message'])

        TranslationHistory.objects.create(
            document=doc,
            action='error',
            details=f'Translation failed: {str(e)}',
            user=request.user,
        )
        messages.error(request, f'Translation failed: {str(e)}')

    return redirect('translation:document_process', pk=doc.pk)


def _handle_update_extracted(request, doc):
    """Update extracted English text with user edits."""
    edited_text = request.POST.get('extracted_text', '').strip()
    if edited_text:
        doc.extracted_text = edited_text
        doc.translated_text = ''
        if doc.status in ('translated', 'detected'):
            doc.status = 'extracted'
        doc.save(update_fields=['extracted_text', 'translated_text', 'status', 'updated_at'])

        TranslationHistory.objects.create(
            document=doc,
            action='edit',
            details=f'Extracted text edited by {request.user} (translation reset)',
            user=request.user,
        )
        messages.success(request, 'Extracted text updated. Translation reset — re-translate when ready.')
    else:
        messages.warning(request, 'No text provided.')

    return redirect('translation:document_process', pk=doc.pk)


def _handle_update_translated(request, doc):
    """Update Japanese translation text with user edits."""
    edited_text = request.POST.get('translated_text', '').strip()
    if edited_text:
        doc.translated_text = edited_text
        # Update status to translated if it was already translated or completed
        if doc.status in ('completed',):
            doc.status = 'translated'
        doc.save(update_fields=['translated_text', 'status', 'updated_at'])

        TranslationHistory.objects.create(
            document=doc,
            action='edit_translation',
            details=f'Japanese translation edited by {request.user}',
            user=request.user,
        )
        messages.success(request, 'Japanese translation updated. Download DOCX to see changes.')
    else:
        messages.warning(request, 'No translation text provided.')

    return redirect('translation:document_process', pk=doc.pk)


def _handle_update_fields(request, doc):
    """Save edited Character Certificate structured fields (human review)."""
    # Fields per spec - editable in second section
    spec_keys = ['serial_number','registration_number','student_name','school_name','school_location','grade','gpa','examination_year_bs','examination_year_ad','certificate_date_bs','certificate_date_ad']
    # Map spec -> internal for storage
    flat = {}
    for k in spec_keys:
        v = request.POST.get(k, '').strip()
        flat[k] = v if v else None

    # Convert flat spec back to internal parser keys for template filler
    internal = {}
    if flat.get('serial_number'):
        internal['serial_no'] = flat['serial_number']
    if flat.get('registration_number'):
        internal['reg_no'] = flat['registration_number']
    if flat.get('student_name'):
        internal['student_name'] = flat['student_name']
    if flat.get('school_name'):
        internal['school_name'] = flat['school_name']
    if flat.get('school_location'):
        internal['location'] = flat['school_location']
    if flat.get('grade'):
        internal['grade'] = flat['grade']
    if flat.get('gpa'):
        internal['gpa'] = flat['gpa']
    if flat.get('examination_year_bs'):
        internal['year_bs'] = flat['examination_year_bs']
    if flat.get('examination_year_ad'):
        internal['year_ad'] = flat['examination_year_ad']
    # Recombine certificate dates into issue_date for parser
    cert_bs = flat.get('certificate_date_bs') or ''
    cert_ad = flat.get('certificate_date_ad') or ''
    if cert_bs:
        # store as "BS (AD)" if AD present, else just BS
        if cert_ad:
            # cert_ad is YYYY/MM/DD -> convert to M/D/YYYY for issue_date format
            try:
                y, m, d = cert_ad.split('/')
                ad_paren = f'{int(m)}/{int(d)}/{y}'
                internal['issue_date'] = f'{cert_bs} ({ad_paren})'
            except Exception:
                internal['issue_date'] = cert_bs
        else:
            internal['issue_date'] = cert_bs

    layout = doc.parsed_layout
    # Preserve existing structured_data metadata, overwrite flat/fields
    existing = layout.get('structured_data', {})
    if not isinstance(existing, dict):
        existing = {}
    existing['fields'] = internal
    existing['flat'] = flat
    existing['edited_by'] = request.user.username if request.user else 'unknown'
    layout['structured_data'] = existing
    doc.parsed_layout = layout
    doc.save(update_fields=['layout_data'])

    TranslationHistory.objects.create(
        document=doc,
        action='edit',
        details=f'Character Certificate fields updated by {request.user}: {flat}',
        user=request.user,
    )
    messages.success(request, 'Character Certificate fields saved. Generate DOCX to apply.')
    return redirect('translation:document_process', pk=doc.pk)


# ─── Document List ──────────────────────────────────────────────────────────

@login_required
def document_list(request):
    """List all uploaded documents with search and filtering."""
    queryset = Document.objects.select_related('document_type', 'uploaded_by')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(extracted_text__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Filter by document type
    type_filter = request.GET.get('type', '')
    if type_filter:
        queryset = queryset.filter(document_type_id=type_filter)

    paginator = Paginator(queryset, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    document_types = DocumentType.objects.all()
    status_choices = Document.STATUS_CHOICES

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'document_types': document_types,
        'status_choices': status_choices,
    }
    return render(request, 'translation/document_list.html', context)


# ─── Document Detail ────────────────────────────────────────────────────────

@login_required
def document_detail(request, pk):
    """View document details."""
    doc = get_object_or_404(
        Document.objects.select_related('document_type', 'uploaded_by', 'reviewed_by'),
        pk=pk
    )
    history = doc.history.select_related('user').order_by('-created_at')[:20]

    context = {
        'document': doc,
        'history': history,
    }
    return render(request, 'translation/document_detail.html', context)


# ─── Review Screen (Side-by-Side Editor) ────────────────────────────────────

@login_required
def document_review(request, pk):
    """Side-by-side review/editing screen for translations."""
    doc = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        form = TranslationReviewForm(request.POST)
        if form.is_valid():
            new_translated = form.cleaned_data['translated_text']
            update_tm = form.cleaned_data.get('update_tm', False)

            # Check if text was actually changed
            text_changed = new_translated != doc.translated_text

            doc.translated_text = new_translated
            doc.status = 'reviewing'
            doc.reviewed_by = request.user
            doc.save(update_fields=['translated_text', 'status', 'reviewed_by', 'updated_at'])

            if text_changed and update_tm:
                # Update TM with reviewed translations
                old_paragraphs = (doc.extracted_text or '').split('\n')
                new_paragraphs = new_translated.split('\n')

                updated_count = 0
                for eng, jpn in zip(old_paragraphs, new_paragraphs):
                    eng = eng.strip()
                    jpn = jpn.strip()
                    if eng and jpn:
                        save_translation_memory(
                            eng, jpn,
                            document_type=doc.document_type,
                            source='review'
                        )
                        updated_count += 1

                messages.success(
                    request,
                    f'Review saved. {updated_count} Translation Memory entries updated.'
                )
            else:
                messages.success(request, 'Review saved successfully.')

            TranslationHistory.objects.create(
                document=doc,
                action='review' if text_changed else 'edit',
                details=f'Review completed by {request.user}',
                user=request.user,
            )

            return redirect('translation:document_detail', pk=doc.pk)
    else:
        form = TranslationReviewForm(initial={
            'translated_text': doc.translated_text,
            'update_tm': True,
        })

    # Prepare side-by-side data
    english_paragraphs = (doc.extracted_text or '').split('\n')
    japanese_paragraphs = (doc.translated_text or '').split('\n')

    # Pad shorter list
    max_len = max(len(english_paragraphs), len(japanese_paragraphs))
    english_paragraphs.extend([''] * (max_len - len(english_paragraphs)))
    japanese_paragraphs.extend([''] * (max_len - len(japanese_paragraphs)))

    side_by_side = list(zip(english_paragraphs, japanese_paragraphs))

    context = {
        'document': doc,
        'form': form,
        'side_by_side': side_by_side,
    }
    return render(request, 'translation/document_review.html', context)


# ─── Mark Complete ──────────────────────────────────────────────────────────

@login_required
@require_POST
def document_complete(request, pk):
    """Mark a document as completed after review."""
    doc = get_object_or_404(Document, pk=pk)
    doc.status = 'completed'
    doc.reviewed_by = request.user
    doc.save(update_fields=['status', 'reviewed_by', 'updated_at'])

    TranslationHistory.objects.create(
        document=doc,
        action='review',
        details=f'Document marked as completed by {request.user}',
        user=request.user,
    )

    messages.success(request, f'Document "{doc.title}" marked as completed.')
    return redirect('translation:document_detail', pk=doc.pk)


# ─── DOCX Download ─────────────────────────────────────────────────────────

@login_required
def document_download(request, pk):
    """Generate and download DOCX file.
    
    For Character Certificates: uses template filling from extracted text
    (no translation step required).
    
    For other document types: uses translated text.
    """
    doc = get_object_or_404(Document, pk=pk)

    # Check if this is a Character Certificate (template-filled, no translation needed)
    doc_type = doc.document_type.name if doc.document_type else ''
    is_character_cert = 'Character Certificate' in doc_type or 'character' in doc_type.lower()

    if is_character_cert:
        # Character Certificates only need extracted text
        if not doc.extracted_text:
            messages.error(request, 'No extracted text available. Please extract text first.')
            return redirect('translation:document_process', pk=doc.pk)
    else:
        # Other documents need translated text
        if not doc.translated_text:
            messages.error(request, 'No translated text available for download.')
            return redirect('translation:document_detail', pk=doc.pk)

    # Generate DOCX
    docx_content = generate_translated_docx(doc)
    if not docx_content:
        messages.error(request, 'Failed to generate DOCX file.')
        return redirect('translation:document_detail', pk=doc.pk)

    # Save to model
    doc.translated_file.save(docx_content.name, docx_content, save=True)

    TranslationHistory.objects.create(
        document=doc,
        action='download',
        details=f'DOCX downloaded by {request.user}' + (' (template filled)' if is_character_cert else ''),
        user=request.user,
    )

    # Serve the file
    file_path = doc.translated_file.path
    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{docx_content.name}"'
    return response


# ─── Bilingual PDF Download ────────────────────────────────────────────────

@login_required
def document_bilingual_pdf(request, pk):
    """
    Generate and download a bilingual PDF preserving original layout.
    Japanese text is placed at exact same positions as English text.
    Images from the original document are preserved with labels.
    """
    doc = get_object_or_404(Document, pk=pk)

    if not doc.translated_text:
        messages.error(request, 'No translated text available.')
        return redirect('translation:document_detail', pk=doc.pk)

    if not doc.layout_data:
        messages.error(request, 'No layout data available. Please extract text first.')
        return redirect('translation:document_detail', pk=doc.pk)

    if doc.file_type not in ('pdf', 'scanned_pdf'):
        messages.error(request, 'Bilingual PDF is only available for PDF documents.')
        return redirect('translation:document_detail', pk=doc.pk)

    try:
        layout_data = doc.parsed_layout
        pages = layout_data.get('pages', [])
        saved_blocks = layout_data.get('_blocks', {})

        # Flatten all images across pages
        all_images = []
        for page in pages:
            all_images.extend(page.get('images', []))

        blocks_translated = {}

        # Split translations into lines
        japanese_lines = [p.strip() for p in (doc.translated_text or '').split('\n') if p.strip()]
        total_jp_lines = len(japanese_lines)

        if saved_blocks:
            # Use saved block-level mapping (precise positions from extraction)
            sorted_block_ids = sorted(saved_blocks.keys(), key=lambda x: (
                saved_blocks[x].get('page', 1),
                saved_blocks[x].get('bbox', [0,0,0,0])[1],
                saved_blocks[x].get('bbox', [0,0,0,0])[0],
            ))

            # If template engine produced consolidated translation (far fewer lines than blocks),
            # render full translation across the main text blocks
            total_blocks = len(sorted_block_ids)
            is_consolidated = total_jp_lines > 0 and total_blocks > total_jp_lines * 2

            for idx, bid in enumerate(sorted_block_ids):
                bdata = saved_blocks[bid]
                eng_text = bdata.get('text', '')

                if is_consolidated and idx == 0:
                    # Put full consolidated translation in first block
                    translation = doc.translated_text
                elif is_consolidated:
                    # Skip remaining blocks (text handled by first block + background)
                    translation = ''
                elif idx < total_jp_lines:
                    translation = japanese_lines[idx]
                else:
                    translation = ''

                blocks_translated[bid] = {
                    'text': eng_text,
                    'translation': translation,
                    'bbox': tuple(bdata.get('bbox', [0, 0, 0, 0])),
                    'page': bdata.get('page', 1),
                }
        else:
            # Fallback: pair by index from page text_blocks
            block_idx = 0
            for page in pages:
                page_num = page.get('page_number', 1)
                for i, block in enumerate(page.get('text_blocks', [])):
                    block_id = f"p{page_num}_b{i}"
                    eng_text = block.get('text', '')
                    translation = japanese_lines[block_idx] if block_idx < total_jp_lines else ''
                    blocks_translated[block_id] = {
                        'text': eng_text,
                        'translation': translation,
                        'bbox': (block['x0'], block['y0'], block['x1'], block['y1']),
                        'page': page_num,
                    }
                    block_idx += 1

        # Generate bilingual PDF
        file_path = doc.original_file.path

        # Detect if template engine produced consolidated translation
        is_consolidated = False
        if saved_blocks:
            total_blocks = len(saved_blocks)
            is_consolidated = total_jp_lines > 0 and total_blocks > total_jp_lines * 2

        full_page_translation = doc.translated_text if is_consolidated else None

        pdf_bytes = generate_bilingual_pdf(
            file_path,
            blocks_translated,
            all_images,
            full_page_translation=full_page_translation,
        )

        if pdf_bytes is None:
            messages.error(request, 'Failed to generate bilingual PDF.')
            return redirect('translation:document_detail', pk=doc.pk)

        # Save to model
        from django.core.files.base import ContentFile
        safe_title = ''.join(c for c in doc.title if c.isalnum() or c in ' _-')[:50]
        filename = f"{safe_title}_bilingual.pdf"
        doc.translated_file.save(filename, ContentFile(pdf_bytes), save=True)

        TranslationHistory.objects.create(
            document=doc,
            action='download',
            details=f'Bilingual PDF downloaded by {request.user}',
            user=request.user,
        )

        # Serve
        response = FileResponse(
            io.BytesIO(pdf_bytes),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Bilingual PDF generation failed: {e}")
        messages.error(request, f'Failed to generate bilingual PDF: {str(e)}')
        return redirect('translation:document_detail', pk=doc.pk)


# ─── Document Delete ────────────────────────────────────────────────────────

@login_required
@require_POST
def document_delete(request, pk):
    """Delete a document."""
    doc = get_object_or_404(Document, pk=pk)
    title = doc.title

    # Delete associated files
    if doc.original_file:
        try:
            os.remove(doc.original_file.path)
        except (OSError, FileNotFoundError):
            pass
    if doc.translated_file:
        try:
            os.remove(doc.translated_file.path)
        except (OSError, FileNotFoundError):
            pass

    doc.delete()
    messages.success(request, f'Document "{title}" deleted.')
    return redirect('translation:document_list')


# ─── Translation Memory Views ──────────────────────────────────────────────

@login_required
def tm_list(request):
    """List Translation Memory entries with search."""
    form = TranslationMemorySearchForm(request.GET)
    queryset = TranslationMemory.objects.select_related('document_type')

    if form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(english_text__icontains=q) |
                Q(japanese_text__icontains=q)
            )

        doc_type = form.cleaned_data.get('document_type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)

        if form.cleaned_data.get('verified_only'):
            queryset = queryset.filter(is_verified=True)

    paginator = Paginator(queryset, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'form': form,
    }
    return render(request, 'translation/tm_list.html', context)


@login_required
def tm_add(request):
    """Add a new Translation Memory entry."""
    if request.method == 'POST':
        form = TranslationMemoryForm(request.POST)
        if form.is_valid():
            tm = form.save(commit=False)
            tm.source = 'manual'
            tm.save()
            messages.success(request, 'Translation Memory entry added.')
            return redirect('translation:tm_list')
    else:
        form = TranslationMemoryForm()

    return render(request, 'translation/tm_form.html', {
        'form': form,
        'title': 'Add Translation Memory',
    })


@login_required
def tm_edit(request, pk):
    """Edit a Translation Memory entry."""
    tm = get_object_or_404(TranslationMemory, pk=pk)

    if request.method == 'POST':
        form = TranslationMemoryForm(request.POST, instance=tm)
        if form.is_valid():
            form.save()
            messages.success(request, 'Translation Memory entry updated.')
            return redirect('translation:tm_list')
    else:
        form = TranslationMemoryForm(instance=tm)

    return render(request, 'translation/tm_form.html', {
        'form': form,
        'title': 'Edit Translation Memory',
        'tm': tm,
    })


@login_required
@require_POST
def tm_delete(request, pk):
    """Delete a Translation Memory entry."""
    tm = get_object_or_404(TranslationMemory, pk=pk)
    tm.delete()
    messages.success(request, 'Translation Memory entry deleted.')
    return redirect('translation:tm_list')


@login_required
@require_POST
def tm_clear(request):
    """Clear all Translation Memory entries."""
    count = TranslationMemory.objects.count()
    TranslationMemory.objects.all().delete()

    TranslationHistory.objects.create(
        action='edit',
        details=f'All Translation Memory cleared ({count} entries) by {request.user}',
        user=request.user,
    )

    messages.success(request, f'All {count} Translation Memory entries cleared.')
    return redirect('translation:tm_list')


# ─── Translation History ───────────────────────────────────────────────────

@login_required
def history_list(request):
    """View translation history with filtering."""
    queryset = TranslationHistory.objects.select_related('document', 'user')

    action_filter = request.GET.get('action', '')
    if action_filter:
        queryset = queryset.filter(action=action_filter)

    paginator = Paginator(queryset, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'action_choices': TranslationHistory.ACTION_CHOICES,
    }
    return render(request, 'translation/history_list.html', context)


# ─── Seed Document Types ───────────────────────────────────────────────────

@login_required
def seed_types(request):
    """Seed default document types."""
    count = seed_document_types()
    if count > 0:
        messages.success(request, f'{count} document types created.')
    else:
        messages.info(request, 'All document types already exist.')
    return redirect('translation:dashboard')
