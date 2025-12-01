from django.shortcuts import render

# Create your views here.


def staff_ssw_working_visa(request):
    return render(request, 'canstud/staffssw.html')

def staff_student_visa(request):
    return render(request, 'canstud/staff_stud.html')
