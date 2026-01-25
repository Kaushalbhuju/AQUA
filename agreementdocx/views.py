from django.shortcuts import render, get_object_or_404, redirect
from .models import Agreement
from .forms import AgreementForm

# CREATE + READ
def agreement_list(request):
    agreements = Agreement.objects.all()
    return render(request, "agreement_list.html", {"agreements": agreements})

def agreement_create(request):
    if request.method == "POST":
        form = AgreementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("agreement_list")
    else:
        form = AgreementForm()
    return render(request, "agreement_form.html", {"form": form})

# UPDATE
def agreement_update(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)
    if request.method == "POST":
        form = AgreementForm(request.POST, request.FILES, instance=agreement)
        if form.is_valid():
            form.save()
            return redirect("agreement_list")
    else:
        form = AgreementForm(instance=agreement)
    return render(request, "agreement_form.html", {"form": form})

# DELETE
def agreement_delete(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)
    if request.method == "POST":
        agreement.delete()
        return redirect("agreement_list")
    return render(request, "agreement_confirm_delete.html", {"agreement": agreement})

def agreement_by_year(request, year):
    if request.method == 'POST':
        form = AgreementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    else:
        form = AgreementForm()

    agreements = Agreement.objects.filter(uploaded_at__year=year)
    return render(request, "agreement_by_year.html", {"year": year, "form": form, "agreements": agreements})



def year_buttons(request):
    # Generate years from 2025 to 2036
    years = list(range(2025, 2025 + 12))
    return render(request, "year_buttons.html", {"years": years})


