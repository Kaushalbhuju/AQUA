from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import JobDemandLetter
from .forms import JobDemandLetterForm

@login_required
def letter_list(request):
    letters = JobDemandLetter.objects.all()
    return render(request, 'letters/letter_list.html', {'letters': letters})

@login_required
def letter_upload(request):
    if request.method == 'POST':
        form = JobDemandLetterForm(request.POST, request.FILES)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.uploaded_by = request.user
            letter.save()
            return redirect('letter_list')
    else:
        form = JobDemandLetterForm()
    return render(request, 'letters/letter_upload.html', {'form': form})

@login_required
def letter_detail(request, pk):
    letter = get_object_or_404(JobDemandLetter, pk=pk)
    return render(request, 'letters/letter_detail.html', {'letter': letter})

@login_required
def letter_delete(request, pk):
    letter = get_object_or_404(JobDemandLetter, pk=pk)
    letter.delete()
    return redirect('letter_list')