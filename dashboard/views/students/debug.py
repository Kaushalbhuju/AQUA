"""
Debug/test views - REMOVE IN PRODUCTION
"""
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages

from dashboard.models import Student, Agent
from dashboard.forms import StudentForm

from .utils import save_student_form


def test_form_submission(request):
    """Debug view to test form submission - REMOVE IN PRODUCTION"""
    if request.method == 'POST':
        agent = Agent.objects.first()
        response_text = ["="*50, "TEST FORM SUBMISSION", "="*50]
        response_text.append(f"POST data: {dict(request.POST)}")
        response_text.append(f"FILES: {dict(request.FILES)}")
        if agent:
            form = StudentForm(request.POST, request.FILES, agent=agent)
            if form.is_valid():
                student = save_student_form(form, request)
                response_text.append(f"✓ Student saved: {student.student_id}" if student else "✗ Error saving")
            else:
                response_text.append(f"✗ Form is INVALID\nErrors: {form.errors}")
        else:
            response_text.append("✗ No agent found!")
        response_text.append("="*50)
        return HttpResponse("<br>".join(response_text))

    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Test Form</title></head>
    <body>
        <h1>Test Form Submission</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="csrfmiddlewaretoken" value="TEST_TOKEN">
            <p>Full Name: <input type="text" name="full_name" value="Test Student"></p>
            <p>Email: <input type="email" name="email" value="test@example.com"></p>
            <p>Phone: <input type="text" name="phone" value="1234567890"></p>
            <p>Gender:
                <select name="gender">
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                </select>
            </p>
            <p>Date of Birth: <input type="date" name="date_of_birth" value="2000-01-01"></p>
            <p>Permanent Address: <textarea name="permanent_address">Test Address</textarea></p>
            <p>Marital Status:
                <select name="marital_status">
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                </select>
            </p>
            <p>TB Status:
                <input type="radio" name="tb_status" value="positive" id="tbPositive">
                <label for="tbPositive">Positive</label>
                <input type="radio" name="tb_status" value="negative" id="tbNegative" checked>
                <label for="tbNegative">Negative</label>
            </p>
            <button type="submit">Test Submit</button>
        </form>
    </body>
    </html>
    """)