from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Company, CompanyYearlyData
from .forms import CompanyForm, CompanyYearlyDataFormSet

class CompanyListView(ListView):
    model = Company
    template_name = 'regcompany/company_list.html'
    context_object_name = 'companies'
    paginate_by = 10
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(company_id__icontains=search_query) |
                Q(company_name_english__icontains=search_query) |
                Q(company_name_japanese__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_no__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        today = timezone.now().date()
        
        if status_filter == 'active':
            queryset = queryset.filter(expire_date__gte=today)
        elif status_filter == 'expired':
            queryset = queryset.filter(expire_date__lt=today)
        elif status_filter == 'expiring':
            queryset = queryset.filter(
                expire_date__gte=today,
                expire_date__lte=today + timedelta(days=30)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Add statistics to context
        all_companies = Company.objects.all()
        context['active_companies_count'] = all_companies.filter(expire_date__gte=today).count()
        context['expiring_soon_count'] = all_companies.filter(
            expire_date__gte=today,
            expire_date__lte=today + timedelta(days=30)
        ).count()
        
        # Count companies created this month
        current_month = today.replace(day=1)
        context['this_month_count'] = all_companies.filter(created_at__gte=current_month).count()
        
        return context

class CompanyCreateView(CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'regcompany/company_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['yearly_data_formset'] = CompanyYearlyDataFormSet(self.request.POST)
        else:
            context['yearly_data_formset'] = CompanyYearlyDataFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        yearly_data_formset = context['yearly_data_formset']
        
        if yearly_data_formset.is_valid():
            self.object = form.save()
            yearly_data_formset.instance = self.object
            yearly_data_formset.save()
            messages.success(self.request, 'Company registered successfully!')
            return redirect('regcompany:company_list')
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.form_invalid(form)

class CompanyUpdateView(UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'regcompany/company_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['yearly_data_formset'] = CompanyYearlyDataFormSet(self.request.POST, instance=self.object)
        else:
            context['yearly_data_formset'] = CompanyYearlyDataFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        yearly_data_formset = context['yearly_data_formset']
        
        # Save the main form (will only update provided fields)
        self.object = form.save()
        
        # Save the formset
        if yearly_data_formset.is_valid():
            yearly_data_formset.instance = self.object
            yearly_data_formset.save()
        
        messages.success(self.request, 'Company updated successfully!')
        return redirect('regcompany:company_list')

class CompanyDetailView(DetailView):
    model = Company
    template_name = 'regcompany/company_detail.html'
    context_object_name = 'company'

def company_dashboard(request):
    companies = Company.objects.all()
    today = timezone.now().date()
    
    # Calculate statistics
    active_agreements = companies.filter(expire_date__gte=today).count()
    expired_agreements = companies.filter(expire_date__lt=today).count()
    expiring_soon = companies.filter(
        expire_date__gte=today,
        expire_date__lte=today + timedelta(days=30)
    ).count()
    
    context = {
        'companies': companies,
        'active_agreements': active_agreements,
        'expired_agreements': expired_agreements,
        'expiring_soon': expiring_soon,
    }
    
    return render(request, 'regcompany/company_dashboard.html', context)