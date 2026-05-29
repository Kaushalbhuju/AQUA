from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.db.models import Q
from dashboard.models import SharedMaterial


def is_teacher(user):
    return user.is_authenticated and user.role in ['teacher', 'staff', 'manager', 'admin', 'superuser']


def is_student(user):
    return user.is_authenticated and user.role in ['student', 'candidate']


@login_required
@user_passes_test(is_teacher)
def share_materials(request):
    """Teacher view to upload and manage shared materials"""
    materials = SharedMaterial.objects.filter(uploaded_by=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        material_type = request.POST.get('material_type')
        category = request.POST.get('category')
        target_class = request.POST.get('target_class')
        external_link = request.POST.get('external_link')
        material_file = request.FILES.get('material_file')
        
        if title:
            if material_type == 'link' and external_link:
                SharedMaterial.objects.create(
                    title=title,
                    description=description,
                    material_type=material_type,
                    category=category,
                    external_link=external_link,
                    target_class=target_class,
                    uploaded_by=request.user
                )
                messages.success(request, f'Material "{title}" shared successfully!')
            elif material_file:
                SharedMaterial.objects.create(
                    title=title,
                    description=description,
                    material_type=material_type,
                    category=category,
                    material_file=material_file,
                    target_class=target_class,
                    uploaded_by=request.user
                )
                messages.success(request, f'Material "{title}" uploaded successfully!')
            else:
                messages.error(request, 'Please provide a file or external link.')
            
            return redirect('dashboard:share_materials')
        else:
            messages.error(request, 'Title is required.')
    
    context = {
        'materials': materials,
        'page_title': 'Share Materials',
        'document_count': materials.filter(material_type='document').count(),
        'video_count': materials.filter(material_type='video').count(),
        'total_downloads': sum(m.download_count for m in materials),
    }
    return render(request, 'dashboards/share_materials.html', context)


@login_required
@user_passes_test(is_teacher)
def delete_material(request, material_id):
    """Delete a shared material"""
    material = get_object_or_404(SharedMaterial, pk=material_id, uploaded_by=request.user)
    material.delete()
    messages.success(request, 'Material deleted successfully.')
    return redirect('dashboard:share_materials')


@login_required
def view_shared_materials(request):
    """Student view to browse and download shared materials"""
    materials = SharedMaterial.objects.filter(is_active=True).order_by('-created_at')
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        materials = materials.filter(material_type=type_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        materials = materials.filter(category=category_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        materials = materials.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(uploaded_by__username__icontains=search_query)
        )
    
    context = {
        'materials': materials,
        'page_title': 'Shared Materials',
        'document_count': materials.filter(material_type='document').count(),
        'video_count': materials.filter(material_type='video').count(),
    }
    return render(request, 'dashboards/view_shared_materials.html', context)


def public_materials(request):
    """Public view for students to browse shared materials without login"""
    materials = SharedMaterial.objects.filter(is_active=True).order_by('-created_at')
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        materials = materials.filter(material_type=type_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        materials = materials.filter(category=category_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        materials = materials.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(uploaded_by__username__icontains=search_query)
        )
    
    context = {
        'materials': materials,
        'page_title': 'Learning Materials',
        'document_count': materials.filter(material_type='document').count(),
        'video_count': materials.filter(material_type='video').count(),
    }
    return render(request, 'dashboards/public_materials.html', context)


def download_material(request, material_id):
    """Download a shared material file (public access)"""
    material = get_object_or_404(SharedMaterial, pk=material_id, is_active=True)
    
    if material.material_file:
        material.download_count += 1
        material.save(update_fields=['download_count'])
        
        response = FileResponse(material.material_file.open('rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{material.material_file.name.split("/")[-1]}"'
        return response
    elif material.external_link:
        return redirect(material.external_link)
    else:
        messages.error(request, 'File not available for download.')
        return redirect('dashboard:public_materials')
