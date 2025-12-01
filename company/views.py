from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import College, CollegeYearlyData
from .forms import CollegeForm, CollegeYearlyDataFormSet

class CollegeListView(ListView):
    model = College
    template_name = 'dashboards/college_list.html'
    context_object_name = 'colleges'
    paginate_by = 10
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(college_id__icontains=search_query) |
                Q(college_name_english__icontains=search_query) |
                Q(college_name_japanese__icontains=search_query) |
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
        all_colleges = College.objects.all()
        context['active_colleges_count'] = all_colleges.filter(expire_date__gte=today).count()
        context['expiring_soon_count'] = all_colleges.filter(
            expire_date__gte=today,
            expire_date__lte=today + timedelta(days=30)
        ).count()
        
        # Count colleges created this month
        current_month = today.replace(day=1)
        context['this_month_count'] = all_colleges.filter(created_at__gte=current_month).count()
        
        return context

class CollegeCreateView(CreateView):
    model = College
    form_class = CollegeForm
    template_name = 'dashboards/college_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['yearly_data_formset'] = CollegeYearlyDataFormSet(self.request.POST)
        else:
            context['yearly_data_formset'] = CollegeYearlyDataFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        yearly_data_formset = context['yearly_data_formset']
        
        if yearly_data_formset.is_valid():
            self.object = form.save()
            yearly_data_formset.instance = self.object
            yearly_data_formset.save()
            messages.success(self.request, 'College registered successfully!')
            return redirect('company:college_list')
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.form_invalid(form)

class CollegeUpdateView(UpdateView):
    model = College
    form_class = CollegeForm
    template_name = 'dashboards/college_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['yearly_data_formset'] = CollegeYearlyDataFormSet(self.request.POST, instance=self.object)
        else:
            context['yearly_data_formset'] = CollegeYearlyDataFormSet(instance=self.object)
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
        
        messages.success(self.request, 'College updated successfully!')
        return redirect('company:college_list')
    
    def form_invalid(self, form):
        # This handles cases where the form has validation errors
        messages.error(self.request, 'Please correct the errors below.')
        return self.render_to_response(self.get_context_data(form=form))

class CollegeDetailView(DetailView):
    model = College
    template_name = 'dashboards/college_detail.html'
    context_object_name = 'college'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context if needed
        return context

def college_dashboard(request):
    colleges = College.objects.all()
    today = timezone.now().date()
    
    # Calculate statistics
    active_agreements = colleges.filter(expire_date__gte=today).count()
    expired_agreements = colleges.filter(expire_date__lt=today).count()
    expiring_soon = colleges.filter(
        expire_date__gte=today,
        expire_date__lte=today + timedelta(days=30)
    ).count()
    
    # Calculate total students
    total_students = 0
    for college in colleges:
        for yearly_data in college.yearly_data.all():
            total_students += yearly_data.yearly_student_no
    
    context = {
        'colleges': colleges,
        'active_agreements': active_agreements,
        'expired_agreements': expired_agreements,
        'expiring_soon': expiring_soon,
        'total_students': total_students,
    }
    
    return render(request, 'dashboards/college_dashboard.html', context)