# guarantee_letter/views.py - CORRECTED VERSION
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from .models import Client, JobGuaranteeLetter, JobGuaranteeLetterTemplate, LetterLog
from .forms import ClientForm, UploadLetterForm, CreateLetterForm, TemplateForm

@login_required
def dashboard(request):
    """Main dashboard view"""
    total_letters = JobGuaranteeLetter.objects.count()
    uploaded_letters = JobGuaranteeLetter.objects.filter(source='uploaded').count()
    created_letters = JobGuaranteeLetter.objects.filter(source='created').count()
    draft_letters = JobGuaranteeLetter.objects.filter(status='draft').count()
    issued_letters = JobGuaranteeLetter.objects.filter(status='issued').count()
    pending_letters = JobGuaranteeLetter.objects.filter(status='pending').count()
    verified_letters = JobGuaranteeLetter.objects.filter(status='verified').count()
    
    recent_letters = JobGuaranteeLetter.objects.all().order_by('-date_created')[:10]
    
    context = {
        'total_letters': total_letters,
        'uploaded_letters': uploaded_letters,
        'created_letters': created_letters,
        'draft_letters': draft_letters,
        'issued_letters': issued_letters,
        'pending_letters': pending_letters,
        'verified_letters': verified_letters,
        'recent_letters': recent_letters,
    }
    return render(request, 'upload/dashboard.html', context)  # Fixed path

@login_required
def letter_list(request):
    """List all letters with basic filtering"""
    letters = JobGuaranteeLetter.objects.all()
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    if search:
        letters = letters.filter(
            Q(letter_number__icontains=search) |
            Q(candidate_name__icontains=search) |
            Q(candidate_email__icontains=search) |
            Q(job_title__icontains=search)
        )
    
    if status:
        letters = letters.filter(status=status)
    
    # Simple counts
    uploaded_count = letters.filter(source='uploaded').count()
    created_count = letters.filter(source='created').count()
    
    context = {
        'letters': letters,
        'search': search,
        'status': status,
        'uploaded_count': uploaded_count,
        'created_count': created_count,
        'STATUS_CHOICES': JobGuaranteeLetter.STATUS_CHOICES,
    }
    return render(request, 'guarantee_letter/letter_list.html', context)

@login_required
def create_letter(request):
    """Create new letter from template"""
    if request.method == 'POST':
        form = CreateLetterForm(request.POST)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.source = 'created'
            letter.issued_by = request.user
            
            # Generate content from template
            template = form.cleaned_data['template']
            letter.generated_content = template.content.format(
                client_name=letter.client.name,
                passport_number=letter.passport_number or 'N/A',
                issue_date=letter.issue_date.strftime('%B %d, %Y'),
                job_title=letter.job_title,
                company_name=letter.company_name or 'N/A',
                candidate_name=letter.candidate_name,
                candidate_email=letter.candidate_email,
                candidate_phone=letter.candidate_phone or 'N/A',
                department=letter.department or 'N/A',
                salary_amount=letter.salary_amount or 'N/A',
                salary_currency=letter.salary_currency or 'USD',
                start_date=letter.start_date.strftime('%B %d, %Y') if letter.start_date else 'N/A',
                end_date=letter.expiry_date.strftime('%B %d, %Y') if letter.expiry_date else 'N/A',
                letter_number=letter.letter_number,
                issued_by=request.user.get_full_name() or request.user.username,
                expiry_date=letter.expiry_date.strftime('%B %d, %Y') if letter.expiry_date else 'N/A'
            )
            
            letter.save()
            
            # Create log entry - WITHOUT ip_address
            LetterLog.objects.create(
                letter=letter,
                action='create',
                user=request.user,
                details=f'Created letter from template: {template.name}'
            )
            
            messages.success(request, f'Letter for {letter.candidate_name} created successfully!')
            return redirect('guarantee_letter:letter_detail', pk=letter.pk)
    else:
        form = CreateLetterForm()
    
    context = {
        'form': form,
        'title': 'Create New Job Guarantee Letter'
    }
    # Render CREATE template, not ISSUE template
    return render(request, 'guarantee_letter/issue_letter.html', context)  # Fixed template

@login_required
def upload_letter(request):
    """Upload existing PDF letter"""
    if request.method == 'POST':
        form = UploadLetterForm(request.POST, request.FILES)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.source = 'uploaded'
            letter.uploaded_by = request.user
            letter.save()
            
            # Create log entry - WITHOUT ip_address
            LetterLog.objects.create(
                letter=letter,
                action='upload',
                user=request.user,
                details=f'Uploaded PDF letter for {letter.candidate_name}'
            )
            
            messages.success(request, f'PDF letter for {letter.candidate_name} uploaded successfully!')
            return redirect('guarantee_letter:letter_detail', pk=letter.pk)
    else:
        form = UploadLetterForm()
    
    context = {
        'form': form,
        'title': 'Upload Job Guarantee Letter (PDF)'
    }
    return render(request, 'upload/upload_letter.html', context)  # Fixed path

@login_required
def letter_detail(request, pk):
    """View letter details"""
    letter = get_object_or_404(JobGuaranteeLetter, pk=pk)
    logs = letter.logs.all().order_by('-created_at')[:10]
    
    context = {
        'letter': letter,
        'logs': logs,
    }
    return render(request, 'guarantee_letter/letter_detail.html', context)

@login_required
def edit_letter(request, pk):
    """Edit an existing letter"""
    letter = get_object_or_404(JobGuaranteeLetter, pk=pk)
    
    if request.method == 'POST':
        if letter.source == 'uploaded':
            form = UploadLetterForm(request.POST, request.FILES, instance=letter)
        else:
            form = CreateLetterForm(request.POST, instance=letter)
        
        if form.is_valid():
            letter = form.save()
            
            # Create log entry - WITHOUT ip_address
            LetterLog.objects.create(
                letter=letter,
                action='update',
                user=request.user,
                details=f'Updated letter {letter.letter_number}'
            )
            
            messages.success(request, 'Letter updated successfully!')
            return redirect('guarantee_letter:letter_detail', pk=letter.pk)
    else:
        if letter.source == 'uploaded':
            form = UploadLetterForm(instance=letter)
        else:
            form = CreateLetterForm(instance=letter)
    
    context = {
        'form': form,
        'letter': letter,
        'title': f'Edit Letter - {letter.letter_number}'
    }
    return render(request, 'guarantee_letter/letter_form.html', context)

@login_required
def download_letter(request, pk):
    """Download letter PDF"""
    letter = get_object_or_404(JobGuaranteeLetter, pk=pk)
    
    if letter.source == 'uploaded' and letter.pdf_file:
        try:
            file_path = letter.pdf_file.path
            filename = f"{letter.letter_number}.pdf"
            
            # Create log entry - WITHOUT ip_address
            LetterLog.objects.create(
                letter=letter,
                action='download',
                user=request.user,
                details=f'Downloaded PDF for letter {letter.letter_number}'
            )
            
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, f'Error downloading file: {str(e)}')
    else:
        messages.error(request, 'PDF file not found or not uploaded.')
    
    return redirect('guarantee_letter:letter_detail', pk=pk)

@login_required
def update_status(request, pk):
    """Update letter status"""
    letter = get_object_or_404(JobGuaranteeLetter, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        
        if new_status in dict(JobGuaranteeLetter.STATUS_CHOICES):
            old_status = letter.status
            letter.status = new_status
            letter.remarks = remarks
            
            if new_status == 'issued':
                letter.issued_by = request.user
            
            letter.save()
            
            # Create log entry - WITHOUT ip_address
            LetterLog.objects.create(
                letter=letter,
                action='status_change',
                user=request.user,
                details=f'Status changed from {old_status} to {new_status}. Remarks: {remarks}'
            )
            
            messages.success(request, f'Status updated to {new_status}')
    
    return redirect('guarantee_letter:letter_detail', pk=pk)

@login_required
def delete_letter(request, pk):
    """Delete a letter"""
    letter = get_object_or_404(JobGuaranteeLetter, pk=pk)
    
    if request.method == 'POST':
        # Create log entry before deletion - WITHOUT ip_address
        LetterLog.objects.create(
            letter=letter,
            action='delete',
            user=request.user,
            details=f'Deleted letter {letter.letter_number}'
        )
        
        letter.delete()
        messages.success(request, 'Letter deleted successfully!')
        return redirect('guarantee_letter:letter_list_list')
    
    context = {'letter': letter}
    return render(request, 'guarantee_letter/delete_letter.html', context)

# ============ CLIENT MANAGEMENT ============
@login_required
def client_list(request):
    """List all clients"""
    clients = Client.objects.all()
    context = {'clients': clients}
    return render(request, 'guarantee_letter/client_list.html', context)

@login_required
def add_client(request):
    """Add new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client added successfully!')
            return redirect('guarantee_letter:client_list')
    else:
        form = ClientForm()
    
    context = {'form': form}
    return render(request, 'guarantee_letter/client_form.html', context)

@login_required
def client_detail(request, pk):
    """View client details"""
    client = get_object_or_404(Client, pk=pk)
    client_letters = client.letters.all().order_by('-date_created')
    
    context = {
        'client': client,
        'letters': client_letters,
    }
    return render(request, 'guarantee_letter/client_detail.html', context)

@login_required
def edit_client(request, pk):
    """Edit existing client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully!')
            return redirect('guarantee_letter:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    context = {
        'form': form,
        'client': client,
    }
    return render(request, 'guarantee_letter/client_form.html', context)

@login_required
def delete_client(request, pk):
    """Delete a client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        messages.success(request, f'Client {client_name} deleted successfully!')
        return redirect('guarantee_letter:client_list')
    
    context = {'client': client}
    return render(request, 'guarantee_letter/delete_client.html', context)

# ============ TEMPLATE MANAGEMENT ============
@login_required
def template_list(request):
    """List all templates"""
    templates = JobGuaranteeLetterTemplate.objects.all()
    context = {'templates': templates}
    return render(request, 'guarantee_letter/template_list.html', context)

@login_required
def add_template(request):
    """Add new template"""
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Template added successfully!')
            return redirect('guarantee_letter:template_list')
    else:
        form = TemplateForm()
    
    context = {'form': form}
    return render(request, 'guarantee_letter/template_form.html', context)

@login_required
def edit_template(request, pk):
    """Edit existing template"""
    template = get_object_or_404(JobGuaranteeLetterTemplate, pk=pk)
    
    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template updated successfully!')
            return redirect('guarantee_letter:template_list')
    else:
        form = TemplateForm(instance=template)
    
    context = {'form': form, 'template': template}
    return render(request, 'guarantee_letter/template_form.html', context)