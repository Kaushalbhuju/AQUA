# ============================================
# views.py - FIXED VERSION
# ============================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from .models import StaffRegistration, DrivingLicense
from .forms import (
    StaffRegistrationForm, EducationalHistoryFormSet, WorkingExperienceFormSet,
    CertificateFormSet, TrainingFormSet, DrivingLicenseForm, BankFormSet,
    StaffSelfRegistrationForm

)
from .models import (
    StaffRegistration, EducationalHistory, WorkingExperience,
    CertificateOfSkills, SkillsTrainingStatus, DrivingLicense, BankInformation
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import StaffAttendance


def staff_registration_create(request, self_registration=False):
    registration_form = StaffSelfRegistrationForm if self_registration else StaffRegistrationForm
    form_valid = education_valid = work_valid = certificate_valid = training_valid = license_valid = bank_valid = True
    if request.method == 'POST':
        print("POST Data:", request.POST)  # Debug
        print("FILES Data:", request.FILES)  # Debug
        
        form = registration_form(request.POST, request.FILES)
        education_formset = EducationalHistoryFormSet(request.POST, prefix='education')
        work_formset = WorkingExperienceFormSet(request.POST, prefix='work')
        certificate_formset = CertificateFormSet(request.POST, prefix='certificate')
        training_formset = TrainingFormSet(request.POST, prefix='training')
        license_form = DrivingLicenseForm(request.POST, prefix='license')
        bank_formset = BankFormSet(request.POST, prefix='bank')
        
        # Check all forms validity
        form_valid = form.is_valid()
        education_valid = education_formset.is_valid()
        work_valid = work_formset.is_valid()
        certificate_valid = certificate_formset.is_valid()
        training_valid = training_formset.is_valid()
        license_valid = license_form.is_valid()
        bank_valid = bank_formset.is_valid()


        print("Bank Valid:", bank_valid)                          # ✅ NEW
        if not bank_valid:
            print("Bank Errors:", bank_formset.errors)            # ✅ NEW
        print("Form Valid:", form_valid)
        print("Education Valid:", education_valid)
        print("Work Valid:", work_valid)
        print("Certificate Valid:", certificate_valid)
        print("Training Valid:", training_valid)
        print("License Valid:", license_valid)

        
        if not form_valid:
            print("Form Errors:", form.errors)
        if not education_valid:
            print("Education Errors:", education_formset.errors)
        if not work_valid:
            print("Work Errors:", work_formset.errors)
        if not certificate_valid:
            print("Certificate Errors:", certificate_formset.errors)
        if not training_valid:
            print("Training Errors:", training_formset.errors)
        if not license_valid:
            print("License Errors:", license_form.errors)
        
        if form_valid and education_valid and work_valid and certificate_valid and training_valid and license_valid and bank_valid:
            try:
                with transaction.atomic():
                    # Save main staff form
                    staff = form.save()
                    
                    # Save education formset
                    education_instances = education_formset.save(commit=False)
                    for edu in education_instances:
                        edu.staff = staff
                        edu.save()
                    
                    # Save work formset
                    work_instances = work_formset.save(commit=False)
                    for work in work_instances:
                        work.staff = staff
                        work.save()
                    
                    # Save certificate formset
                    certificate_instances = certificate_formset.save(commit=False)
                    for cert in certificate_instances:
                        cert.staff = staff
                        cert.save()
                    
                    # Save training formset
                    training_instances = training_formset.save(commit=False)
                    for train in training_instances:
                        train.staff = staff
                        train.save()
                    
                    # Save license
                    if license_form.cleaned_data.get('pass_year') or license_form.cleaned_data.get('pass_month') or license_form.cleaned_data.get('discretion_of_license'):
                        license = license_form.save(commit=False)
                        license.staff = staff
                        license.save()
                        #Bank Information 
                    bank_instances = bank_formset.save(commit=False)
                    if not bank_instances:
                        raise ValueError("At least one bank information record is required.")
                    for bank in bank_instances:
                        bank.staff = staff
                        bank.save()

                    
                if self_registration:
                    return render(request, 'dashboards/staff_self_registration_success.html')
                messages.success(request, 'Staff registration completed successfully!')
                return redirect('staff_detail', pk=staff.pk)
            except Exception as e:
                messages.error(request, f'Error saving data: {str(e)}')
                print("Exception:", str(e))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = registration_form()
        education_formset = EducationalHistoryFormSet(prefix='education', queryset=EducationalHistory.objects.none())
        work_formset = WorkingExperienceFormSet(prefix='work', queryset=WorkingExperience.objects.none())
        certificate_formset = CertificateFormSet(prefix='certificate', queryset=CertificateOfSkills.objects.none())
        training_formset = TrainingFormSet(prefix='training', queryset=SkillsTrainingStatus.objects.none())
        license_form = DrivingLicenseForm(prefix='license')
        bank_formset = BankFormSet(instance=None, prefix='bank', queryset=BankInformation.objects.none())  # ✅ NEW

    
    context = {
        'form': form,
        'education_formset': education_formset,
        'work_formset': work_formset,
        'certificate_formset': certificate_formset,
        'training_formset': training_formset,
        'license_form': license_form,
        'bank_formset': bank_formset, 
        'has_errors': (not form_valid or not education_valid or not work_valid or 
                        not certificate_valid or not training_valid or not license_valid or not bank_valid),
    }
    
    return render(request, 'dashboards/staff_registration.html', context)


@login_required(login_url='/')
def staff_self_registration(request):
    return staff_registration_create(request, self_registration=True)


def staff_registration_update(request, pk):
    form_valid = education_valid = work_valid = certificate_valid = training_valid = license_valid = bank_valid = True
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, request.FILES, instance=staff)
        education_formset = EducationalHistoryFormSet(request.POST, instance=staff, prefix='education')
        work_formset = WorkingExperienceFormSet(request.POST, instance=staff, prefix='work')
        certificate_formset = CertificateFormSet(request.POST, instance=staff, prefix='certificate')
        training_formset = TrainingFormSet(request.POST, instance=staff, prefix='training')
        bank_formset = BankFormSet(request.POST,instance=staff, prefix='bank')

        
        try:
            license = staff.driving_license
            license_form = DrivingLicenseForm(request.POST, instance=license, prefix='license')
        except DrivingLicense.DoesNotExist:
            license_form = DrivingLicenseForm(request.POST, prefix='license')
        
        # Check validity
        form_valid = form.is_valid()
        education_valid = education_formset.is_valid()
        work_valid = work_formset.is_valid()
        certificate_valid = certificate_formset.is_valid()
        training_valid = training_formset.is_valid()
        license_valid = license_form.is_valid()
        bank_valid = bank_formset.is_valid()

        if form_valid and education_valid and work_valid and certificate_valid and training_valid and license_valid and bank_valid:
            try:
                with transaction.atomic():
                    staff = form.save()
                    
                    # Save formsets
                    education_formset.instance = staff
                    education_formset.save()
                    
                    work_formset.instance = staff
                    work_formset.save()
                    
                    certificate_formset.instance = staff
                    certificate_formset.save()
                    
                    training_formset.instance = staff
                    training_formset.save()
                    
                    # Save license
                    if license_form.cleaned_data.get('pass_year') or license_form.cleaned_data.get('pass_month') or license_form.cleaned_data.get('discretion_of_license'):
                        license = license_form.save(commit=False)
                        license.staff = staff
                        license.save()
                     # ✅ NEW — Save bank formset
                    bank_formset.save()

                    
                messages.success(request, 'Staff registration updated successfully!')
                return redirect('staff_detail', pk=staff.pk)
            except Exception as e:
                messages.error(request, f'Error updating data: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffRegistrationForm(instance=staff)
        education_formset = EducationalHistoryFormSet(instance=staff, prefix='education')
        work_formset = WorkingExperienceFormSet(instance=staff, prefix='work')
        certificate_formset = CertificateFormSet(instance=staff, prefix='certificate')
        training_formset = TrainingFormSet(instance=staff, prefix='training')
        # Use instance so management_form counts stay consistent on POST
        bank_formset = BankFormSet(instance=staff, prefix='bank')


        
        try:
            license = staff.driving_license
            license_form = DrivingLicenseForm(instance=license, prefix='license')
        except DrivingLicense.DoesNotExist:
            license_form = DrivingLicenseForm(prefix='license')
    
    context = {
        'form': form,
        'education_formset': education_formset,
        'work_formset': work_formset,
        'certificate_formset': certificate_formset,
        'training_formset': training_formset,
        'license_form': license_form,
        'staff': staff,
        'bank_formset': bank_formset,
        'has_errors': (request.method == 'POST' and (
            not form_valid or not education_valid or not work_valid or 
            not certificate_valid or not training_valid or not license_valid or not bank_valid
        )),
    }
    
    return render(request, 'dashboards/staff_registration.html', context)


def staff_list(request):
    staff_list = StaffRegistration.objects.all()
    context = {'staff_list': staff_list}
    return render(request, 'dashboards/staff_list.html', context)


@login_required
def staff_attendance(request):
    selected_date = parse_date(request.GET.get('date', '')) or timezone.localdate()
    staff_members = StaffRegistration.objects.all().order_by('full_name')
    existing = {
        record.staff_id: record
        for record in StaffAttendance.objects.filter(attendance_date=selected_date)
    }
    for staff in staff_members:
        staff.attendance_record = existing.get(staff.pk)

    if request.method == 'POST':
        submitted_date = parse_date(request.POST.get('date', ''))
        if not submitted_date:
            messages.error(request, 'Choose a valid attendance date.')
            return redirect('manager:staff_attendance')
        for staff in staff_members:
            status = request.POST.get(f'status_{staff.pk}', '')
            if status not in dict(StaffAttendance.STATUS_CHOICES):
                continue
            StaffAttendance.objects.update_or_create(
                staff=staff,
                attendance_date=submitted_date,
                defaults={
                    'status': status,
                    'note': request.POST.get(f'note_{staff.pk}', '').strip()[:500],
                    'marked_by': request.user,
                },
            )
        messages.success(request, f'Attendance saved for {submitted_date:%B %d, %Y}.')
        return redirect(f"/manager/staff-attendance/?date={submitted_date.isoformat()}")

    return render(request, 'dashboards/staff_attendance.html', {
        'staff_members': staff_members,
        'attendance': existing,
        'selected_date': selected_date,
        'status_choices': StaffAttendance.STATUS_CHOICES,
    })


@login_required
def staff_attendance_export_excel(request):
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo

    selected_date = parse_date(request.GET.get('date', '')) or timezone.localdate()
    date_from = parse_date(request.GET.get('date_from', ''))
    date_to = parse_date(request.GET.get('date_to', ''))
    if not date_from and not date_to:
        date_from = date_to = selected_date
    else:
        date_from = date_from or date_to
        date_to = date_to or date_from

    if date_from > date_to:
        messages.error(request, 'The start date must be on or before the end date.')
        return redirect(f'/manager/staff-attendance/?date={selected_date.isoformat()}')

    records = list(
        StaffAttendance.objects.filter(
            attendance_date__range=(date_from, date_to)
        ).select_related('staff', 'marked_by').order_by('attendance_date', 'staff__full_name')
    )
    staff_members = StaffRegistration.objects.all().order_by('full_name')
    status_counts = {value: 0 for value, _label in StaffAttendance.STATUS_CHOICES}
    per_staff = {
        staff.pk: {
            'staff': staff,
            'present': 0,
            'late': 0,
            'absent': 0,
            'leave': 0,
            'record_count': 0,
        }
        for staff in staff_members
    }
    for record in records:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
        summary = per_staff.get(record.staff_id)
        if summary is not None:
            summary[record.status] = summary.get(record.status, 0) + 1
            summary['record_count'] += 1

    workbook = openpyxl.Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = 'Summary'
    detail_sheet = workbook.create_sheet('Attendance Log')
    matrix_sheet = workbook.create_sheet('Daily Overview')
    navy, blue, light_blue = '17365D', '2F75B5', 'D9EAF7'
    light_gray, white = 'F3F6FA', 'FFFFFF'
    thin_gray = Side(style='thin', color='D9E1EA')
    border = Border(bottom=thin_gray)

    # Staff-by-day matrix for scanning a month or custom date range.
    from datetime import timedelta
    report_dates = []
    current_date = date_from
    while current_date <= date_to:
        report_dates.append(current_date)
        current_date += timedelta(days=1)
    matrix_headers = ['Staff ID', 'Staff Name'] + report_dates + ['Present', 'Late', 'Absent', 'On Leave']
    matrix_sheet.append(['AQUA | DAILY ATTENDANCE OVERVIEW'])
    matrix_sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(matrix_headers))
    matrix_sheet['A1'].font = Font(name='Aptos Display', size=16, bold=True, color='FFFFFF')
    matrix_sheet['A1'].fill = PatternFill('solid', fgColor=navy)
    matrix_sheet.append([f'{date_from:%d %b %Y} – {date_to:%d %b %Y}; blank = not recorded'])
    matrix_sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(matrix_headers))
    matrix_sheet.append(matrix_headers)
    for cell in matrix_sheet[3]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor=blue)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    by_staff_date = {(record.staff_id, record.attendance_date): record for record in records}
    status_fills = {
        'Present': 'E2F0D9',
        'Late': 'FFF2CC',
        'Absent': 'FCE4D6',
        'On leave': 'DDEBF7',
    }
    for staff in staff_members:
        row = [staff.staff_id or '', staff.full_name]
        for day in report_dates:
            record = by_staff_date.get((staff.pk, day))
            row.append(record.get_status_display() if record else '')
        staff_counts = per_staff[staff.pk]
        row.extend([staff_counts['present'], staff_counts['late'], staff_counts['absent'], staff_counts['leave']])
        matrix_sheet.append(row)
        for cell in matrix_sheet[matrix_sheet.max_row]:
            cell.alignment = Alignment(horizontal='center' if cell.column > 2 else 'left', vertical='center')
            cell.border = border
            if cell.value in status_fills:
                cell.fill = PatternFill('solid', fgColor=status_fills[cell.value])
    matrix_sheet.freeze_panes = 'C4'
    matrix_sheet.sheet_view.showGridLines = False
    matrix_sheet.column_dimensions['A'].width = 16
    matrix_sheet.column_dimensions['B'].width = 28
    for column in range(3, 3 + len(report_dates)):
        matrix_sheet.cell(3, column).number_format = 'dd mmm'
        matrix_sheet.column_dimensions[get_column_letter(column)].width = 13
    for column in range(3 + len(report_dates), len(matrix_headers) + 1):
        matrix_sheet.column_dimensions[get_column_letter(column)].width = 12
    matrix_sheet.auto_filter.ref = f'A3:{get_column_letter(len(matrix_headers))}{matrix_sheet.max_row}'
    matrix_sheet.sheet_properties.pageSetUpPr.fitToPage = True
    matrix_sheet.page_setup.orientation = 'landscape'
    matrix_sheet.page_setup.fitToWidth = 1
    matrix_sheet.page_setup.fitToHeight = 0
    matrix_sheet.print_title_rows = '1:3'

    # Summary sheet
    summary_sheet.merge_cells('A1:F1')
    summary_sheet['A1'] = 'AQUA | STAFF ATTENDANCE REPORT'
    summary_sheet['A1'].font = Font(name='Aptos Display', size=18, bold=True, color=white)
    summary_sheet['A1'].fill = PatternFill('solid', fgColor=navy)
    summary_sheet['A1'].alignment = Alignment(vertical='center')
    summary_sheet.row_dimensions[1].height = 34
    summary_sheet.merge_cells('A2:F2')
    summary_sheet['A2'] = f'Attendance period: {date_from:%d %b %Y} – {date_to:%d %b %Y}'
    summary_sheet['A2'].font = Font(name='Aptos', size=11, bold=True, color=navy)
    summary_sheet['A2'].fill = PatternFill('solid', fgColor=light_blue)
    summary_sheet['A2'].alignment = Alignment(vertical='center')
    summary_sheet.row_dimensions[2].height = 24
    summary_sheet.append([])
    summary_sheet.append(['Report metric', 'Value'])
    for cell in summary_sheet[4][:2]:
        cell.font = Font(name='Aptos', bold=True, color=white)
        cell.fill = PatternFill('solid', fgColor=blue)
        cell.alignment = Alignment(vertical='center')
    generated_at = timezone.localtime(timezone.now()).replace(tzinfo=None)
    metrics = [
        ('Registered staff', len(staff_members)),
        ('Attendance entries', len(records)),
        ('Present', status_counts.get('present', 0)),
        ('Late', status_counts.get('late', 0)),
        ('Absent', status_counts.get('absent', 0)),
        ('On leave', status_counts.get('leave', 0)),
        ('Generated at', generated_at),
    ]
    for label, value in metrics:
        summary_sheet.append([label, value])
        for cell in summary_sheet[summary_sheet.max_row][:2]:
            cell.border = border
            cell.alignment = Alignment(vertical='center')
        summary_sheet.cell(summary_sheet.max_row, 1).font = Font(name='Aptos', bold=True, color=navy)
    summary_sheet['B11'].number_format = 'dd mmm yyyy hh:mm'
    summary_sheet.column_dimensions['A'].width = 28
    summary_sheet.column_dimensions['B'].width = 28
    summary_sheet.sheet_view.showGridLines = False
    summary_sheet.freeze_panes = 'A5'

    # Per-staff roll-up for the selected range
    summary_headers = ['Staff ID', 'Staff Name', 'Present', 'Late', 'Absent', 'On Leave', 'Recorded Days']
    summary_sheet.append([])
    summary_sheet.append(summary_headers)
    staff_header_row = summary_sheet.max_row
    for cell in summary_sheet[staff_header_row]:
        cell.font = Font(name='Aptos', bold=True, color=white)
        cell.fill = PatternFill('solid', fgColor=blue)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    for staff_summary in per_staff.values():
        staff = staff_summary['staff']
        summary_sheet.append([
            staff.staff_id or '', staff.full_name, staff_summary['present'],
            staff_summary['late'], staff_summary['absent'], staff_summary['leave'],
            staff_summary['record_count'],
        ])
        for cell in summary_sheet[summary_sheet.max_row]:
            cell.border = border
            cell.alignment = Alignment(vertical='center')
    for column, width in enumerate([18, 30, 13, 13, 13, 13, 17], start=1):
        summary_sheet.column_dimensions[get_column_letter(column)].width = width

    # Detailed, filterable attendance log
    detail_headers = ['Date', 'Staff ID', 'Staff Name', 'Status', 'Note', 'Marked By', 'Last Updated']
    detail_sheet.merge_cells('A1:G1')
    detail_sheet['A1'] = 'AQUA | ATTENDANCE ENTRIES'
    detail_sheet['A1'].font = Font(name='Aptos Display', size=16, bold=True, color=white)
    detail_sheet['A1'].fill = PatternFill('solid', fgColor=navy)
    detail_sheet['A1'].alignment = Alignment(vertical='center')
    detail_sheet.row_dimensions[1].height = 32
    detail_sheet.merge_cells('A2:G2')
    detail_sheet['A2'] = f'{date_from:%d %b %Y} – {date_to:%d %b %Y}  |  {len(records)} attendance entries'
    detail_sheet['A2'].font = Font(name='Aptos', size=10, italic=True, color='526174')
    detail_sheet.append([])
    detail_sheet.append(detail_headers)
    detail_header_row = 4
    for cell in detail_sheet[detail_header_row]:
        cell.font = Font(name='Aptos', bold=True, color=white)
        cell.fill = PatternFill('solid', fgColor=blue)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    detail_sheet.row_dimensions[detail_header_row].height = 28
    for row_number, record in enumerate(records, start=detail_header_row + 1):
        marked_by = record.marked_by
        updated_at = timezone.localtime(record.updated_at).replace(tzinfo=None)
        values = [
            record.attendance_date, record.staff.staff_id or '', record.staff.full_name,
            record.get_status_display(), record.note or '',
            (marked_by.get_full_name() or marked_by.username) if marked_by else '', updated_at,
        ]
        detail_sheet.append(values)
        for cell in detail_sheet[row_number]:
            cell.font = Font(name='Aptos', size=10, color='263445')
            cell.border = border
            cell.alignment = Alignment(vertical='top', wrap_text=cell.column == 5)
            if row_number % 2:
                cell.fill = PatternFill('solid', fgColor=light_gray)
        detail_sheet.cell(row_number, 1).number_format = 'dd mmm yyyy'
        detail_sheet.cell(row_number, 7).number_format = 'dd mmm yyyy hh:mm'

    if records:
        table = Table(displayName='StaffAttendanceLog', ref=f'A{detail_header_row}:G{detail_sheet.max_row}')
        table.tableStyleInfo = TableStyleInfo(name='TableStyleMedium2', showRowStripes=True, showColumnStripes=False)
        detail_sheet.add_table(table)
    else:
        detail_sheet.auto_filter.ref = f'A{detail_header_row}:G{detail_header_row}'
    for column, width in enumerate([18, 18, 30, 18, 44, 24, 22], start=1):
        detail_sheet.column_dimensions[get_column_letter(column)].width = width
    detail_sheet.freeze_panes = 'A5'
    detail_sheet.sheet_view.showGridLines = False
    detail_sheet.sheet_properties.pageSetUpPr.fitToPage = True
    detail_sheet.page_setup.orientation = 'landscape'
    detail_sheet.page_setup.fitToWidth = 1
    detail_sheet.page_setup.fitToHeight = 0
    detail_sheet.print_title_rows = '1:4'
    workbook.properties.title = 'AQUA Staff Attendance Report'
    workbook.properties.subject = f'Staff attendance from {date_from} through {date_to}'

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="staff_attendance_{date_from:%Y-%m-%d}_to_{date_to:%Y-%m-%d}.xlsx"'
    workbook.save(response)
    return response


def staff_detail(request, pk):
    staff = get_object_or_404(StaffRegistration, pk=pk)
    context = {'staff': staff}
    return render(request, 'dashboards/staff_detail.html', context)


def staff_delete(request, pk):
    staff = get_object_or_404(StaffRegistration, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff deleted successfully!')
        return redirect('staff_list')
    context = {'staff': staff}
    return render(request, 'dashboards/staff_confirm_delete.html', context)


#New
def generate_staff_registration_pdf(request, pk):
    """Generate Staff Registration PDF matching the exact form layout - fits on single A4 page."""
    staff = get_object_or_404(StaffRegistration, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="staff_registration_{staff.staff_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=0.35 * inch, rightMargin=0.35 * inch,
        topMargin=0.3 * inch, bottomMargin=0.3 * inch,
    )
    elements = []
    W = 7.77 * inch  # usable width on A4 with 0.35" margins each side

    BLACK = colors.black
    PEACH = colors.HexColor('#F5C9A0')
    GREY  = colors.HexColor('#E8E8E8')
    WHITE = colors.white
    LN    = 0.5
    PAD   = 2

    def p(text, size=7, bold=False, align=TA_LEFT):
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        return Paragraph(
            str(text) if text else '',
            ParagraphStyle('s', fontName=font, fontSize=size, leading=size + 2,
                           alignment=align, spaceAfter=0, spaceBefore=0),
        )

    def _val(v, fallback=''):
        return str(v) if v and str(v).strip() else fallback

    BASE_STYLE = [
        ('GRID',         (0, 0), (-1, -1), LN,  BLACK),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING',   (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING',(0, 0), (-1, -1), PAD),
    ]

    # ── TITLE ──────────────────────────────────────────────────────────────────
    title_tbl = Table([[p('STAFF MANAGEMENT', 14, True, TA_CENTER)]], colWidths=[W])
    title_tbl.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('LINEBELOW',     (0, 0), (-1, -1), 0, WHITE),
    ]))
    elements.append(title_tbl)

    sub_tbl = Table([[p('STAFF REGISTRATION', 9, True, TA_CENTER)]], colWidths=[W])
    sub_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), PEACH),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(sub_tbl)
    elements.append(Spacer(1, 2))

    # ── MAIN INFO (STAFF ID / FULL NAME / ADDRESS / PHOTO) ────────────────────
    main_c = [
        W * 0.085,   # col0: STAFF ID / Full Name / Address label
        W * 0.070,   # col1: Permanent / Present sub-label
        W * 0.290,   # col2: main value
        W * 0.105,   # col3: Gender / Marital Status label
        W * 0.310,   # col4: Gender / Marital Status value combined with empty space
        W * 0.140,   # col5: CANDIDATE PHOTO
    ]

    photo_cell = p('CANDIDATE\nPHOTO', 7, True, TA_CENTER)
    if staff.candidate_photo:
        try:
            photo_cell = Image(staff.candidate_photo.path, width=0.95 * inch, height=1.05 * inch)
        except Exception:
            pass

    gender_display   = staff.get_gender_display() if staff.gender else ''
    marital_display  = _val(staff.marital_status)

    main_data = [
        [p('STAFF ID',  7, True), '', p(_val(staff.staff_id), 7),
         p('Gender', 7, True), p(gender_display, 7), photo_cell],
        [p('Full Name', 7, True), '', p(_val(staff.full_name), 7),
         p('Marital Status', 7, True), p(marital_display, 7), ''],
        [p('Address', 7, True), p('Permanent', 6, True), p(_val(staff.permanent_address), 7),
         '', '', ''],
        ['', p('Present', 6, True), p(_val(staff.present_address), 7), '', '', ''],
    ]

    main_tbl = Table(main_data, colWidths=main_c, rowHeights=[0.28 * inch] * 4)
    main_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (1, 0)),        # STAFF ID spans cols 0-1
        ('SPAN', (0, 1), (1, 1)),        # Full Name spans cols 0-1
        ('SPAN', (5, 0), (5, 3)),        # Photo spans all 4 rows
        ('SPAN', (0, 2), (0, 3)),        # Address label spans rows 2-3
        ('SPAN', (2, 2), (4, 2)),        # Permanent address value spans cols 2-4
        ('SPAN', (2, 3), (4, 3)),        # Present address value spans cols 2-4
        ('BACKGROUND', (0, 0), (1, 0), GREY),
        ('BACKGROUND', (3, 0), (3, 0), GREY),
        ('BACKGROUND', (0, 1), (1, 1), GREY),
        ('BACKGROUND', (3, 1), (3, 1), GREY),
        ('BACKGROUND', (0, 2), (1, 3), GREY),
        ('ALIGN',  (5, 0), (5, 3), 'CENTER'),
        ('VALIGN', (5, 0), (5, 3), 'MIDDLE'),
    ]))
    elements.append(main_tbl)

    # ── ID / PASSPORT ─────────────────────────────────────────────────────────
    id_c = [W*0.115, W*0.225, W*0.095, W*0.175, W*0.095, W*0.295]
    id_data = [[
        p('Passport No', 7, True),
        p(_val(staff.id_passport_no), 7),
        p('Date of Issue', 7, True),
        p(str(staff.date_of_issue) if staff.date_of_issue else '', 7),
        p('Issue From', 7, True),
        p(_val(staff.issue_from), 7),
    ]]
    id_tbl = Table(id_data, colWidths=id_c, rowHeights=[0.28 * inch])
    id_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('BACKGROUND', (0, 0), (0, 0), GREY),
        ('BACKGROUND', (2, 0), (2, 0), GREY),
        ('BACKGROUND', (4, 0), (4, 0), GREY),
    ]))
    elements.append(id_tbl)

    # ── PERSONAL INFORMATION ──────────────────────────────────────────────────
    dob = staff.date_of_birth.strftime('%d-%m-%Y') if staff.date_of_birth else ''
    pi_c = [W*0.115, W*0.155, W*0.065, W*0.095, W*0.095, W*0.165, W*0.165, W*0.145]
    pi_data = [
        # Header row
        [p('Personal Information', 7, True),
         p('Date of Birth',  7, True, TA_CENTER),
         p('Eye Lense',      7, True, TA_CENTER), '',
         p('Blood Group',    7, True, TA_CENTER),
         p('Phone No.',      7, True, TA_CENTER), '',
         p('Email ID',       7, True, TA_CENTER)],
        # Value row (Right / Left eye sub-labels + data)
        ['',
         p(dob, 7, align=TA_CENTER),
         p('Right', 6, True, TA_CENTER),
         p('Left',  6, True, TA_CENTER),
         p(_val(staff.blood_group), 7, align=TA_CENTER),
         p(_val(staff.phone_no),    7, align=TA_CENTER), '',
         p(_val(staff.email_id),    7, align=TA_CENTER)],
        # Eye-lens value row
        ['', '',
         p(_val(staff.eye_lense_right), 7, align=TA_CENTER),
         p(_val(staff.eye_lense_left),  7, align=TA_CENTER),
         '', '', '', ''],
    ]
    pi_tbl = Table(pi_data, colWidths=pi_c, rowHeights=[0.22 * inch] * 3)
    pi_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 2)),   # Personal Information label spans 3 rows
        ('SPAN', (1, 0), (1, 0)),   # DOB header
        ('SPAN', (1, 1), (1, 2)),   # DOB value spans rows 1-2
        ('SPAN', (2, 0), (3, 0)),   # Eye Lense header spans 2 cols
        ('SPAN', (4, 0), (4, 0)),   # Blood Group header
        ('SPAN', (4, 1), (4, 2)),   # Blood Group value spans rows 1-2
        ('SPAN', (5, 0), (6, 0)),   # Phone No header spans 2 cols
        ('SPAN', (5, 1), (6, 2)),   # Phone value spans 2 cols x 2 rows
        ('SPAN', (7, 0), (7, 0)),   # Email header
        ('SPAN', (7, 1), (7, 2)),   # Email value spans rows 1-2
        ('BACKGROUND', (0, 0), (0, 2), GREY),
        ('BACKGROUND', (1, 0), (1, 0), GREY),
        ('BACKGROUND', (2, 0), (3, 0), GREY),
        ('BACKGROUND', (4, 0), (4, 0), GREY),
        ('BACKGROUND', (5, 0), (6, 0), GREY),
        ('BACKGROUND', (7, 0), (7, 0), GREY),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(pi_tbl)

    # ── FAMILY RECORDS ────────────────────────────────────────────────────────
    fam_c = [W*0.115, W*0.490, W*0.115, W*0.280]
    fam_data = [
        [p('Family Records', 7, True), p('', 7),
         p('CONTACT NO', 7, True, TA_CENTER), p(_val(staff.contact_no), 7)],
        [p('Spouse Name',   7, True), p(_val(staff.spouse_name), 7), '', ''],
    ]
    fam_tbl = Table(fam_data, colWidths=fam_c, rowHeights=[0.25 * inch, 0.25 * inch])
    fam_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (3, 0), (3, 1)),   # CONTACT NO value spans 2 rows
        ('SPAN', (1, 1), (2, 1)),   # Spouse Name value spans 2 cols
        ('BACKGROUND', (0, 0), (0, 0), GREY),
        ('BACKGROUND', (2, 0), (2, 0), GREY),
        ('BACKGROUND', (0, 1), (0, 1), GREY),
    ]))
    elements.append(fam_tbl)
    elements.append(Spacer(1, 3))

    # ── BANK INFORMATION ──────────────────────────────────────────────────────
    bank_hdr = Table([[p('BANK INFORMATION', 9, True, TA_CENTER)]], colWidths=[W])
    bank_hdr.setStyle(TableStyle([
        ('GRID',         (0, 0), (-1, -1), LN, BLACK),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
    ]))
    elements.append(bank_hdr)

    bank_c = [W*0.145, W*0.355, W*0.145, W*0.355]
    bank_info = staff.bank_info.first()
    
    bank_data = [
        [p('Bank Name', 7, True), p(_val(bank_info.bank_name) if bank_info else '', 7),
         p('Branch Name', 7, True), p(_val(bank_info.branch_name) if bank_info else '', 7)],
        [p('Account No.', 7, True), p(_val(bank_info.account_no) if bank_info else '', 7),
         p('Account Holder', 7, True), p(_val(bank_info.account_holder_name) if bank_info else '', 7)]
    ]
    
    bank_tbl = Table(bank_data, colWidths=bank_c, rowHeights=[0.25 * inch, 0.25 * inch])
    bank_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('BACKGROUND', (0, 0), (0, 1), GREY),
        ('BACKGROUND', (2, 0), (2, 1), GREY),
    ]))
    elements.append(bank_tbl)
    elements.append(Spacer(1, 3))

    # ── EDUCATIONAL HISTORY ───────────────────────────────────────────────────
    edu_hdr = Table([[p('EDUCATIONAL HISTORY', 9, True, TA_CENTER)]], colWidths=[W])
    edu_hdr.setStyle(TableStyle([
        ('GRID',         (0, 0), (-1, -1), LN, BLACK),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
    ]))
    elements.append(edu_hdr)

    edu_c = [W*0.135, W*0.355, W*0.075, W*0.075, W*0.075, W*0.075, W*0.095, W*0.115]
    edu_levels_display = [
        'Primary School', 'Junior H. School', 'Higher S. School',
        'College / University', 'Graduate University', 'Graduate University', 'Other School',
    ]
    edu_level_keys = ['Primary', 'Junior', 'Higher', 'College', 'Graduate', 'PostGraduate', 'Other']
    edu_map = {e.pass_level: e for e in staff.education_history.all()}

    edu_data = [
        [p('Pass Level', 7, True, TA_CENTER),
         p('Name of School', 7, True, TA_CENTER),
         p('Admission & Graduation', 7, True, TA_CENTER), '', '', '',
         p('Enrolled Years', 7, True, TA_CENTER), ''],
        ['', '',
         p('Year', 7, True, TA_CENTER), p('Month', 7, True, TA_CENTER),
         p('Year', 7, True, TA_CENTER), p('Month', 7, True, TA_CENTER),
         '', ''],
    ]
    for label, key in zip(edu_levels_display, edu_level_keys):
        e = edu_map.get(key)
        edu_data.append([
            p(label, 7),
            p(_val(e.name_of_school) if e else '', 7),
            p(_val(e.admission_year)  if e else '', 7, align=TA_CENTER),
            p(_val(e.admission_month) if e else '', 7, align=TA_CENTER),
            p(_val(e.graduation_year) if e else '', 7, align=TA_CENTER),
            p(_val(e.graduation_month)if e else '', 7, align=TA_CENTER),
            p(_val(e.enrolled_years)  if e else '', 7, align=TA_CENTER),
            p('Years', 7, align=TA_RIGHT),
        ])

    edu_tbl = Table(edu_data, colWidths=edu_c, rowHeights=[0.22 * inch] * len(edu_data))
    edu_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (5, 0)),   # Admission & Graduation header
        ('SPAN', (6, 0), (7, 0)),   # Enrolled Years header
        ('SPAN', (6, 1), (7, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(edu_tbl)
    elements.append(Spacer(1, 3))

    # ── WORKING EXPERIENCE ────────────────────────────────────────────────────
    work_hdr = Table([[p('WORKING EXPERIENCE', 9, True, TA_CENTER)]], colWidths=[W])
    work_hdr.setStyle(TableStyle([
        ('GRID',         (0, 0), (-1, -1), LN, BLACK),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
    ]))
    elements.append(work_hdr)

    work_c = [W*0.135, W*0.355, W*0.075, W*0.075, W*0.075, W*0.075, W*0.095, W*0.115]
    work_qs = list(staff.work_experience.all())
    while len(work_qs) < 3:
        work_qs.append(None)

    work_data = [
        [p('Type of Work',           7, True, TA_CENTER),
         p('Name of Working Company',7, True, TA_CENTER),
         p('Date of Join & Resign',  7, True, TA_CENTER), '', '', '',
         p('Working Years',          7, True, TA_CENTER), ''],
        ['', '',
         p('Years', 7, True, TA_CENTER), p('Months', 7, True, TA_CENTER),
         p('Years', 7, True, TA_CENTER), p('Months', 7, True, TA_CENTER),
         '', ''],
    ]
    for w in work_qs[:3]:
        work_data.append([
            p(_val(w.type_of_work)    if w else '', 7, align=TA_CENTER),
            p(_val(w.name_of_company) if w else '', 7),
            p(_val(w.join_year)       if w else '', 7, align=TA_CENTER),
            p(_val(w.join_month)      if w else '', 7, align=TA_CENTER),
            p(_val(w.resign_year)     if w else '', 7, align=TA_CENTER),
            p(_val(w.resign_month)    if w else '', 7, align=TA_CENTER),
            p(_val(w.working_years)   if w else '', 7, align=TA_CENTER),
            p('Years', 7, align=TA_RIGHT),
        ])

    work_tbl = Table(work_data, colWidths=work_c, rowHeights=[0.22 * inch] * len(work_data))
    work_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (5, 0)),
        ('SPAN', (6, 0), (7, 0)),
        ('SPAN', (6, 1), (7, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(work_tbl)
    elements.append(Spacer(1, 3))

    # ── CERTIFICATE OF SKILLS + SKILLS TRAINING STATUS ───────────────────────
    half = W / 2
    cert_qs  = list(staff.certificates.all())
    train_qs = list(staff.training_status.all())
    max_rows = max(len(cert_qs), len(train_qs), 3)

    cert_c_inner  = [half * 0.28, half * 0.72]
    train_c_inner = [half * 0.35, half * 0.65]

    cert_data = [
        [p('CERTIFICATE OF SKILLS',  8, True, TA_CENTER), ''],
        [p('Pass Year & Month',       7, True, TA_CENTER),
         p('Name of Certificate',     7, True, TA_CENTER)],
    ]
    train_data = [
        [p('SKILLS TRAINING STATUS', 8, True, TA_CENTER), ''],
        [p('Join Year and Month',     7, True, TA_CENTER),
         p('Organization',            7, True, TA_CENTER)],
    ]
    for i in range(max_rows):
        c = cert_qs[i]  if i < len(cert_qs)  else None
        t = train_qs[i] if i < len(train_qs) else None
        cert_data.append([
            p(f'{_val(c.pass_year)}/{_val(c.pass_month)}' if c else '', 7, align=TA_CENTER),
            p(_val(c.name_of_certificate) if c else '', 7),
        ])
        train_data.append([
            p(f'{_val(t.join_year)}/{_val(t.join_month)}' if t else '', 7, align=TA_CENTER),
            p(_val(t.organization) if t else '', 7),
        ])

    cert_tbl = Table(cert_data, colWidths=cert_c_inner,
                     rowHeights=[0.22 * inch] * len(cert_data))
    cert_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
    ]))

    train_tbl = Table(train_data, colWidths=train_c_inner,
                      rowHeights=[0.22 * inch] * len(train_data))
    train_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
    ]))

    skills_row = Table([[cert_tbl, train_tbl]], colWidths=[half, half])
    skills_row.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(skills_row)
    elements.append(Spacer(1, 3))

    # ── DRIVING LICENSE ───────────────────────────────────────────────────────
    license = None
    try:
        license = staff.driving_license
    except Exception:
        pass

    dl_c = [W*0.18, W*0.22, W*0.60]
    dl_data = [
        [p('DRIVING LICENSE', 8, True, TA_CENTER),
         p('Pass Year & Month', 7, True, TA_CENTER),
         p('Discretion of License', 7, True, TA_CENTER)],
        ['',
         p(f'{_val(license.pass_year)}/{_val(license.pass_month)}' if license else '', 7, align=TA_CENTER),
         p(_val(license.discretion_of_license) if license else '', 7)],
    ]
    dl_tbl = Table(dl_data, colWidths=dl_c, rowHeights=[0.25 * inch, 0.25 * inch])
    dl_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 1)),   # Driving License label spans 2 rows
        ('BACKGROUND', (0, 0), (0, 1), GREY),
        ('BACKGROUND', (1, 0), (1, 0), GREY),
        ('BACKGROUND', (2, 0), (2, 0), GREY),
        ('ALIGN', (0, 0), (0, 1), 'CENTER'),
    ]))
    elements.append(dl_tbl)
    elements.append(Spacer(1, 3))

    # ── HOBBIES & MOTIVATION ──────────────────────────────────────────────────
    hm_c = [W / 2, W / 2]
    hm_data = [
        [p('Hobbies, Special skills, etc.', 8, True),
         p('Motivation, Self-promotion',    8, True)],
        [p(_val(staff.hobbies),    7),
         p(_val(staff.motivation), 7)],
    ]
    hm_tbl = Table(hm_data, colWidths=hm_c, rowHeights=[0.25 * inch, 0.65 * inch])
    hm_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1,  0), GREY),
    ]))
    elements.append(hm_tbl)

    # ── BUILD ─────────────────────────────────────────────────────────────────
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
def generate_staff_id_card_pdf(request, pk):
    """Generate Staff ID Card PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_id_card_{staff.staff_id}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=28, textColor=colors.HexColor('#ff9966'), alignment=TA_CENTER)
    
    elements.append(Paragraph("STAFF ID CARD", title_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # ID Card Design (Front)
    card_data = [
        ['', 'AQUA GROUP'],
        ['', 'STAFF IDENTIFICATION CARD'],
        ['Photo', ''],
        ['', f"Name: {staff.full_name}"],
        ['', f"ID: {staff.staff_id}"],
        ['', f"Position: Staff Member"],
        ['', f"Department: General"],
        ['', f"Valid Until: {datetime.now().year + 5}"],
    ]
    
    card_table = Table(card_data, colWidths=[2*inch, 4*inch])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 16),
        ('FONTSIZE', (0, 2), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#667eea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(card_table)
    elements.append(Spacer(1, 0.5*inch))
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
    elements.append(Paragraph("This card is property of Aqua Group", footer_style))
    elements.append(Paragraph("If found, please return to HR Department", footer_style))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def generate_staff_login_report_pdf(request, pk):
    """Generate Staff Login Report PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_login_report_{staff.staff_id}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#667eea'), alignment=TA_CENTER)
    
    elements.append(Paragraph("STAFF LOGIN REPORT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Report Header
    report_data = [
        ['Staff ID:', staff.staff_id],
        ['Full Name:', staff.full_name],
        ['Email:', staff.email_id],
        ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
    ]
    
    report_table = Table(report_data, colWidths=[2*inch, 4*inch])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(report_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Sample Login Activity (you can customize this based on your actual login tracking)
    elements.append(Paragraph("LOGIN ACTIVITY SUMMARY", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    activity_data = [
        ['Date', 'Login Time', 'Logout Time', 'Duration', 'Status'],
        [datetime.now().strftime('%Y-%m-%d'), '09:00 AM', '05:00 PM', '8 hours', 'Active'],
        ['Sample data', 'Coming soon', 'Coming soon', '-', 'Pending'],
    ]
    
    activity_table = Table(activity_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1*inch])
    activity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(activity_table)
    elements.append(Spacer(1, 0.5*inch))
    
    elements.append(Paragraph("Note: Implement actual login tracking system for real data", styles['Normal']))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def generate_staff_login_id_pdf(request, pk):
    """Generate Staff Login ID PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_login_id_{staff.staff_id}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=28, textColor=colors.HexColor('#667eea'), alignment=TA_CENTER)
    
    elements.append(Paragraph("STAFF LOGIN CREDENTIALS", title_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Login credentials box
    login_data = [
        ['STAFF LOGIN INFORMATION'],
        [''],
        ['Full Name:', staff.full_name],
        ['Staff ID:', staff.staff_id],
        ['Email/Username:', staff.email_id],
        ['Default Password:', 'staff@' + staff.staff_id],
        [''],
        ['Portal URL:', 'https://staff.aquagroup.com'],
        [''],
        ['Please change your password after first login'],
    ]
    
    login_table = Table(login_data, colWidths=[6*inch])
    login_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 18),
        ('FONTSIZE', (0, 2), (-1, -2), 14),
        ('FONTNAME', (0, 2), (0, -2), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#667eea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(login_table)
    elements.append(Spacer(1, 0.5*inch))
    
    elements.append(Paragraph("IMPORTANT SECURITY NOTES:", styles['Heading3']))
    elements.append(Spacer(1, 0.2*inch))
    
    notes = [
        "1. Keep your login credentials confidential",
        "2. Do not share your password with anyone",
        "3. Change your password regularly",
        "4. Contact IT support if you forget your password",
        "5. Report any suspicious activity immediately",
    ]
    
    for note in notes:
        elements.append(Paragraph(note, styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response



#Manger redirect to SSW AND STUDENTS
# views.py
from django.shortcuts import render

def ssw_working_visa(request):
    return render(request, 'canstud/managerssw.html')

def student_visa(request):
    return render(request, 'canstud/manager_student.html')

def language_skill_dashboard(request):
    return render(request, 'manager/language_skill_dashboard.html')


from django.contrib.auth import get_user_model
from staff.models import StaffTask
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import StaffActivityLog
from .utils import log_staff_activity

@login_required
def manage_tasks(request):
    User = get_user_model()
    staff_users = User.objects.filter(role='staff').order_by('username')
    selected_staff_id = request.GET.get('staff', '')
    staff_tasks = StaffTask.objects.none()
    selected_staff = None

    if selected_staff_id:
        selected_staff = get_object_or_404(User, id=selected_staff_id, role='staff')
        staff_tasks = StaffTask.objects.filter(assigned_to=selected_staff).order_by('-created_at')
    else:
        staff_tasks = StaffTask.objects.all().order_by('-created_at')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        staff_id = request.POST.get('assigned_to')
        description = request.POST.get('description', '').strip()
        if title and staff_id:
            target = get_object_or_404(User, id=staff_id, role='staff')
            task = StaffTask.objects.create(
                title=title,
                description=description or None,
                assigned_by=request.user,
                assigned_to=target,
            )
            log_staff_activity(
                user=request.user,
                action='task_assigned',
                description=f"Assigned task '{title}' to {target.username}",
                request=request,
                extra_data={'task_id': task.pk, 'assigned_to': target.username, 'title': title}
            )
            # Also log for the target staff as an activity they can see?
            log_staff_activity(
                user=target,
                action='task_assigned',
                description=f"Received task '{title}' from {request.user.username}",
                request=request,
                extra_data={'task_id': task.pk, 'assigned_by': request.user.username}
            )
            messages.success(request, f'Task assigned to {target.username}')
        return redirect('manager:manage_tasks')

    # ── Activity Log section ──────────────────────────────────────────────
    # Filters
    activity_action = request.GET.get('activity_action', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    activity_search = request.GET.get('activity_search', '').strip()
    activity_staff = request.GET.get('activity_staff', '').strip()  # separate from task filter

    # Determine which staff to filter logs by: activity_staff overrides staff, else use staff filter if present
    log_staff_filter = activity_staff or selected_staff_id

    logs_qs = StaffActivityLog.objects.select_related('user').all()

    if log_staff_filter:
        try:
            uid = int(log_staff_filter)
            u = User.objects.get(id=uid)
            logs_qs = logs_qs.filter(Q(user__id=uid) | Q(username_snapshot=u.username))
        except Exception:
            # fallback: try filtering by username snapshot string
            logs_qs = logs_qs.filter(username_snapshot=log_staff_filter)

    if activity_action:
        logs_qs = logs_qs.filter(action=activity_action)

    if activity_search:
        logs_qs = logs_qs.filter(
            Q(description__icontains=activity_search) |
            Q(username_snapshot__icontains=activity_search) |
            Q(path__icontains=activity_search) |
            Q(user__username__icontains=activity_search)
        )

    # Date filtering
    from django.utils.dateparse import parse_date
    if date_from:
        d = parse_date(date_from)
        if d:
            logs_qs = logs_qs.filter(timestamp__date__gte=d)
    if date_to:
        d = parse_date(date_to)
        if d:
            logs_qs = logs_qs.filter(timestamp__date__lte=d)

    logs_qs = logs_qs.order_by('-timestamp')

    # Pagination for logs
    paginator = Paginator(logs_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Stats for header cards
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    # Counts
    total_staff = staff_users.count()
    logins_today = StaffActivityLog.objects.filter(action='login', timestamp__date=today).count()
    active_today_users = StaffActivityLog.objects.filter(timestamp__date=today).values('user').distinct().count()
    tasks_pending = StaffTask.objects.filter(status='pending').count()

    # Recent logins for quick view (last 5 logins of staff)
    recent_logins = StaffActivityLog.objects.filter(action='login').select_related('user').order_by('-timestamp')[:5]

    return render(request, 'manager/manage_tasks.html', {
        'staff_users': staff_users,
        'staff_tasks': staff_tasks,
        'selected_staff': selected_staff,
        'selected_staff_id': selected_staff_id,
        # Activity log context
        'page_obj': page_obj,
        'activity_logs': page_obj.object_list,
        'paginator': paginator,
        'activity_action': activity_action,
        'date_from': date_from,
        'date_to': date_to,
        'activity_search': activity_search,
        'activity_staff': activity_staff,
        'action_choices': StaffActivityLog.ACTION_CHOICES,
        'total_staff': total_staff,
        'logins_today': logins_today,
        'active_today_users': active_today_users,
        'tasks_pending': tasks_pending,
        'recent_logins': recent_logins,
    })


def can_view_staff_activity(user):
    return user.is_authenticated and getattr(user, 'role', '') in {'manager', 'admin', 'superuser', 'operation_head'}


@login_required
@user_passes_test(can_view_staff_activity, login_url='dashboard:manager_dashboard')
def staff_activity_log(request):
    """Dedicated full-page activity log (also accessible via /manager/staff-activity/)."""
    User = get_user_model()
    action = request.GET.get('action', '').strip()
    staff_filter = request.GET.get('staff', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search = request.GET.get('search', '').strip()
    action_values = {value for value, _label in StaffActivityLog.ACTION_CHOICES}
    logs = StaffActivityLog.objects.select_related('user').all()
    invalid_filter = False
    if action and action not in action_values:
        messages.error(request, 'Choose a valid activity action.')
        invalid_filter = True
    if action in action_values:
        logs = logs.filter(action=action)
    if staff_filter:
        logs = logs.filter(Q(username_snapshot=staff_filter) | Q(user__username=staff_filter))
    if search:
        logs = logs.filter(
            Q(description__icontains=search) | Q(username_snapshot__icontains=search) |
            Q(path__icontains=search) | Q(ip_address__icontains=search) |
            Q(method__icontains=search) | Q(user_agent__icontains=search) |
            Q(user__username__icontains=search)
        )
    parsed_from = parse_date(date_from) if date_from else None
    parsed_to = parse_date(date_to) if date_to else None
    if date_from and not parsed_from:
        messages.error(request, 'The start date is invalid.')
        invalid_filter = True
    if date_to and not parsed_to:
        messages.error(request, 'The end date is invalid.')
        invalid_filter = True
    if parsed_from and parsed_to and parsed_from > parsed_to:
        messages.error(request, 'The start date must be on or before the end date.')
        invalid_filter = True
    if parsed_from:
        logs = logs.filter(timestamp__date__gte=parsed_from)
    if parsed_to:
        logs = logs.filter(timestamp__date__lte=parsed_to)
    if invalid_filter:
        logs = logs.none()
    logs = logs.order_by('-timestamp', '-pk')

    # Include past staff accounts from their immutable log snapshots, even if
    # the account itself has since been removed.
    usernames = set(StaffActivityLog.objects.filter(role_snapshot='staff').exclude(username_snapshot='').values_list('username_snapshot', flat=True))
    usernames.update(User.objects.filter(role='staff').values_list('username', flat=True))
    staff_users = [{'username': username, 'display': username} for username in sorted(usernames, key=str.casefold)]

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))
    filter_query = request.GET.copy()
    filter_query.pop('page', None)

    return render(request, 'manager/staff_activity_log.html', {
        'staff_users': staff_users,
        'page_obj': page_obj,
        'activity_logs': page_obj.object_list,
        'paginator': paginator,
        'selected_staff': staff_filter,
        'action': action,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
        'action_choices': StaffActivityLog.ACTION_CHOICES,
        'filter_query': filter_query.urlencode(),
    })


@login_required
@user_passes_test(can_view_staff_activity, login_url='dashboard:manager_dashboard')
def staff_activity_export_csv(request):
    """Export filtered activity logs as CSV."""
    import csv
    from django.http import HttpResponse
    from django.db.models import Q
    from django.utils.dateparse import parse_date
    from django.contrib.auth import get_user_model
    User = get_user_model()

    logs = StaffActivityLog.objects.select_related('user').all()
    staff_filter = request.GET.get('staff', '').strip()
    action = request.GET.get('action', '').strip()
    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    # also support activity_* param names from manage_tasks page
    if not staff_filter:
        staff_filter = request.GET.get('activity_staff', '').strip()
    if not action:
        action = request.GET.get('activity_action', '').strip()
    if not search:
        search = request.GET.get('activity_search', '').strip()

    if staff_filter:
        logs = logs.filter(Q(username_snapshot=staff_filter) | Q(user__username=staff_filter))
    valid_actions = {value for value, _label in StaffActivityLog.ACTION_CHOICES}
    if action:
        logs = logs.filter(action=action) if action in valid_actions else logs.none()
    if search:
        logs = logs.filter(
            Q(description__icontains=search) | Q(username_snapshot__icontains=search) |
            Q(path__icontains=search) | Q(ip_address__icontains=search) |
            Q(method__icontains=search) | Q(user_agent__icontains=search) |
            Q(user__username__icontains=search)
        )
    parsed_from = parse_date(date_from) if date_from else None
    parsed_to = parse_date(date_to) if date_to else None
    if (date_from and not parsed_from) or (date_to and not parsed_to) or (parsed_from and parsed_to and parsed_from > parsed_to):
        logs = logs.none()
    else:
        if parsed_from:
            logs = logs.filter(timestamp__date__gte=parsed_from)
        if parsed_to:
            logs = logs.filter(timestamp__date__lte=parsed_to)
    logs = logs.order_by('-timestamp', '-pk')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="staff_activity_log.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Staff', 'Role', 'Action', 'Description', 'IP Address', 'Path', 'Method', 'User Agent'])
    for log in logs.iterator():
        values = [
            timezone.localtime(log.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            log.username_snapshot or (log.user.username if log.user else ''),
            log.role_snapshot,
            log.get_action_display(),
            log.description,
            log.ip_address or '',
            log.path,
            log.method,
            log.user_agent,
        ]
        # Prevent spreadsheet applications from evaluating log text as formulas.
        writer.writerow([("'" + value if isinstance(value, str) and value.lstrip(' \t\r\n')[:1] in ('=', '+', '-', '@') else value) for value in values])
    return response


# Scan Documents Feature
import os
import uuid
import json
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.db import models
from .models import ScannedDocument
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

def is_manager(user):
    return user.is_authenticated and user.role in ['manager', 'admin', 'superuser', 'staff', 'operation_head']

@login_required
@user_passes_test(is_manager)
def scan_documents(request):
    documents = ScannedDocument.objects.all()
    
    # Filter by document type
    doc_type_filter = request.GET.get('document_type')
    if doc_type_filter:
        documents = documents.filter(document_type=doc_type_filter)
    
    # Search by name or candidate
    search_query = request.GET.get('search')
    if search_query:
        documents = documents.filter(
            models.Q(document_name__icontains=search_query) |
            models.Q(candidate_name__icontains=search_query) |
            models.Q(candidate_id__icontains=search_query)
        )
    
    # Handle simple single-document upload
    if request.method == 'POST' and 'document_name' in request.POST and 'document_file' in request.FILES:
        document_name = request.POST.get('document_name')
        document_type = request.POST.get('document_type')
        candidate_name = request.POST.get('candidate_name', '')
        candidate_id = request.POST.get('candidate_id', '')
        notes = request.POST.get('notes', '')
        document_file = request.FILES.get('document_file')
        
        if document_name and document_file:
            doc = ScannedDocument.objects.create(
                document_name=document_name,
                document_type=document_type,
                candidate_name=candidate_name,
                candidate_id=candidate_id,
                notes=notes,
                document_file=document_file,
                file_size=document_file.size,
                uploaded_by=request.user
            )
            messages.success(request, f'Document "{document_name}" uploaded successfully!')
            return redirect('manager:scan_documents')
        else:
            messages.error(request, 'Please provide document name and file.')
            
    context = {
        'documents': documents,
        'page_title': 'Document Scanner & Gallery',
    }
    return render(request, 'canstud/scan_documents.html', context)

@login_required
@user_passes_test(is_manager)
@require_POST
def images_to_pdf(request):
    """
    Receives multiple images via AJAX and converts them to a single multi-page PDF.
    """
    try:
        images = request.FILES.getlist('images[]')
        document_name = request.POST.get('document_name', 'Scanned_Document')
        document_type = request.POST.get('document_type', 'other')
        candidate_name = request.POST.get('candidate_name', '')
        candidate_id = request.POST.get('candidate_id', '')
        notes = request.POST.get('notes', '')
        
        if not images:
            return JsonResponse({'success': False, 'error': 'No images provided.'})
            
        pil_images = []
        for img_file in images:
            img = Image.open(img_file)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            pil_images.append(img)
            
        if not pil_images:
            return JsonResponse({'success': False, 'error': 'Failed to process images.'})
            
        # Convert first image to PDF and append the rest
        pdf_bytes = BytesIO()
        first_image = pil_images[0]
        rest_images = pil_images[1:]
        
        first_image.save(
            pdf_bytes, "PDF", resolution=100.0, save_all=True, append_images=rest_images
        )
        pdf_bytes.seek(0)
        
        # Save as ScannedDocument
        pdf_filename = f"{uuid.uuid4().hex[:10]}.pdf"
        
        doc = ScannedDocument(
            document_name=document_name,
            document_type=document_type,
            candidate_name=candidate_name,
            candidate_id=candidate_id,
            notes=notes,
            page_count=len(pil_images),
            uploaded_by=request.user
        )
        
        doc.document_file.save(pdf_filename, ContentFile(pdf_bytes.read()), save=False)
        doc.file_size = doc.document_file.size
        doc.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully created PDF with {len(pil_images)} pages.',
            'redirect_url': '/manager/scan-documents/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_manager)
def download_document(request, doc_id):
    document = get_object_or_404(ScannedDocument, pk=doc_id)
    if document.document_file:
        response = HttpResponse(document.document_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.document_file.name)}"'
        return response
    return redirect('manager:scan_documents')

@login_required
@user_passes_test(is_manager)
def delete_scanned_document(request, doc_id):
    document = get_object_or_404(ScannedDocument, pk=doc_id)
    doc_name = document.document_name
    if document.document_file:
        document.document_file.delete(save=False)
    document.delete()
    messages.success(request, f'Document "{doc_name}" deleted successfully.')
    return redirect('manager:scan_documents')
