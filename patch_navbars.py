import os

NAVBAR_FORM = """            <ul class="navbar-nav ms-auto">
                <li class="nav-item">
                <form action="{% url 'set_language' %}" method="post" class="d-flex align-items-center mb-0 px-2" style="background: white; border-radius: 4px;">
                    {% csrf_token %}
                    <input name="next" type="hidden" value="{{ request.get_full_path }}">
                    <select name="language" onchange="this.form.submit()" class="form-select form-select-sm" style="border: none;">
                    {% get_current_language as LANGUAGE_CODE %}
                    {% get_available_languages as LANGUAGES %}
                    {% get_language_info_list for LANGUAGES as languages %}
                    {% for language in languages %}
                        <option value="{{ language.code }}" {% if language.code == LANGUAGE_CODE %}selected{% endif %}>
                        {{ language.name_local }} ({{ language.code }})
                        </option>
                    {% endfor %}
                    </select>
                </form>
                </li>
            </ul>"""

files_to_patch = [
    'templates/dashboards/student_attendance.html',
    'templates/dashboards/teacher_report.html',
    'templates/dashboards/student_records.html'
]

for file in files_to_patch:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply switcher to student_attendance
    if 'student_attendance' in file:
        content = content.replace(
            '<div class="collapse navbar-collapse" id="navbarNav">\n        <ul class="navbar-nav ms-auto">\n        </ul>\n      </div>',
            f'<div class="collapse navbar-collapse" id="navbarNav">\n{NAVBAR_FORM}\n      </div>'
        )
        content = content.replace(
            '<div class="collapse navbar-collapse" id="navbarNav">\r\n        <ul class="navbar-nav ms-auto">\r\n        </ul>\r\n      </div>',
            f'<div class="collapse navbar-collapse" id="navbarNav">\n{NAVBAR_FORM}\n      </div>'
        )
        content = content.replace('Back to Dashboard', '{% trans "Back to Dashboard" %}')
        content = content.replace('<h4>{{ page_title }}</h4>', '<h4>{% trans "{{ page_title }}" %}</h4>')

    if 'teacher_report.html' in file:
        content = content.replace('<div class="collapse navbar-collapse" id="navbarNav"></div>', f'<div class="collapse navbar-collapse" id="navbarNav">\n{NAVBAR_FORM}\n</div>')
        content = content.replace('<h4>TEACHER REPORT</h4>', '<h4>{% trans "TEACHER REPORT" %}</h4>')
        content = content.replace('Back to Dashboard', '{% trans "Back to Dashboard" %}')

    if 'student_records.html' in file:
        # Switcher was already applied by the multi_replace tool!
        content = content.replace('Back to Dashboard', '{% trans "Back to Dashboard" %}')

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patching complete.")
