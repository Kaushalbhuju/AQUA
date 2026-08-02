"""
Student PDF generation views - heavy HTML moved to template
"""
import os
import base64
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from weasyprint import HTML

from dashboard.models import Student


def _generate_student_pdf_internal(request, student_id):
    """Internal function to generate PDF using template"""
    try:
        student = get_object_or_404(
            Student.objects.select_related('agent').prefetch_related(
                'education_history', 'work_experience'
            ),
            id=student_id
        )

        # Photo as base64
        photo_html = '<div class="photo-placeholder">PHOTO</div>'
        if student.photo:
            try:
                photo_path = student.photo.path
                if os.path.exists(photo_path):
                    with open(photo_path, "rb") as f:
                        photo_data = base64.b64encode(f.read()).decode()
                    ext = os.path.splitext(photo_path)[1].lower()
                    mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                    photo_html = f'<img src="data:{mime_type};base64,{photo_data}" style="width:100%;height:100%;object-fit:cover;display:block;">'
            except Exception:
                pass

        def fmt_date(d):
            return d.strftime('%Y-%m-%d') if d else ''

        edu_list = list(student.education_history.all())
        edu_defaults = [
            "Primary School", "Junior H. School", "Higher S. School",
            "College / University", "Graduate University", "Graduate University", "Other School"
        ]
        education_rows = []
        for i in range(7):
            e = edu_list[i] if i < len(edu_list) else None
            education_rows.append({
                'pass_level': e.pass_level if e else edu_defaults[i],
                'school_name': e.school_name if e else '',
                'admission_year': e.admission_year if e else '',
                'admission_month': e.admission_month if e else '',
                'graduation_year': e.graduation_year if e else '',
                'graduation_month': e.graduation_month if e else '',
                'enrolled_years': e.enrolled_years if e and e.enrolled_years else '',
            })

        work_list = list(student.work_experience.all())[:3]
        work_rows = []
        for i in range(3):
            w = work_list[i] if i < len(work_list) else None
            work_rows.append({
                'work_type': w.work_type if w else '',
                'company_name': w.company_name if w else '',
                'join_date': w.join_date if w else '',
                'resign_date': w.resign_date if w else '',
                'working_years': w.working_years if w and w.working_years else '',
            })

        context = {
            'student': student,
            'photo_html': photo_html,
            'dob': fmt_date(student.date_of_birth),
            'passport_issue': fmt_date(student.passport_issue_date),
            'passport_expiry': fmt_date(student.passport_expiry_date),
            'a_code': student.agent.agent_code if student.agent else "",
            'education_rows': education_rows,
            'work_rows': work_rows,
        }

        html_content = render_to_string('dashboards/student_pdf.html', context, request=request)
        pdf = HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="Admission_Form_{student.student_id}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


@login_required
def generate_student_pdf(request, student_id):
    """Generate PDF for student - accessible by logged-in users"""
    return _generate_student_pdf_internal(request, student_id)


def generate_student_pdf_portal(request, student_id):
    """Generate PDF for student - accessible by portal users via session"""
    portal_agent_id = request.session.get('portal_agent_id')
    if not portal_agent_id:
        from django.contrib.auth.decorators import login_required
        return login_required(lambda r, sid: _generate_student_pdf_internal(r, sid))(request, student_id)
    return _generate_student_pdf_internal(request, student_id)


def _generate_admission_fee_pdf_internal(request, student_id):
    """Internal function to generate Admission Fee Invoice PDF"""
    try:
        student = get_object_or_404(Student, id=student_id)

        logo_base64 = ""
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_base64 = base64.b64encode(f.read()).decode()
            except Exception:
                pass

        bg_base64 = ""
        bg_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'admission_fee_invoice_bg.jpg')
        if os.path.exists(bg_path):
            try:
                with open(bg_path, "rb") as f:
                    bg_base64 = base64.b64encode(f.read()).decode()
            except Exception:
                pass

        context = {
            'student': student,
            'current_date': student.created_at if student.created_at else timezone.now(),
            'logo_base64': logo_base64,
            'bg_base64': bg_base64,
        }

        html_string = render_to_string('dashboards/admission_fee_invoice_pdf.html', context, request=request)
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="Admission_Fee_Invoice_{student.student_id}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def generate_admission_fee_pdf(request, student_id):
    """Generate Admission Fee Invoice PDF - accessible by logged-in users"""
    return _generate_admission_fee_pdf_internal(request, student_id)


def generate_admission_fee_pdf_portal(request, student_id):
    """Generate Admission Fee Invoice PDF - accessible by portal users via session"""
    portal_agent_id = request.session.get('portal_agent_id')
    if not portal_agent_id:
        from django.contrib.auth.decorators import login_required
        return login_required(lambda r, sid: _generate_admission_fee_pdf_internal(r, sid))(request, student_id)

    return _generate_admission_fee_pdf_internal(request, student_id)