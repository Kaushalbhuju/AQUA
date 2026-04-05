import os

replacements = {
    # Global
    '>Logout<': '>{% trans "Logout" %}<',
    '>Photo<': '>{% trans "Photo" %}<',
    '>Name<': '>{% trans "Name" %}<',
    '>Japanese Name<': '>{% trans "Japanese Name" %}<',
    '>Gender<': '>{% trans "Gender" %}<',
    '>Age<': '>{% trans "Age" %}<',
    '>Actions<': '>{% trans "Actions" %}<',
    '>Action<': '>{% trans "Action" %}<',
    '>Export PDF<': '>{% trans "Export PDF" %}<',

    # class_list.html
    '>Classes - Aqua Group<': '>{% trans "Classes - Aqua Group" %}<',
    '>Select a class to view and mark attendance, or manage the class students.<': '>{% trans "Select a class to view and mark attendance, or manage the class students." %}<',
    '>Student(s)<': '>{% trans "Student(s)" %}<',
    '>Attendance<': '>{% trans "Attendance" %}<',
    '>Students<': '>{% trans "Students" %}<',
    '>No classes found. They will be created automatically.<': '>{% trans "No classes found. They will be created automatically." %}<',
    '<h2><i class="fas fa-chalkboard"></i> Classes</h2>': '<h2><i class="fas fa-chalkboard"></i> {% trans "Classes" %}</h2>',

    # student_attendance.html
    '>Instructions: Enter Japanese names for each student and check the dates they attended.<': '>{% trans "Instructions: Enter Japanese names for each student and check the dates they attended." %}<',
    '>Attendance Dates<': '>{% trans "Attendance Dates" %}<',
    '>Attendance %<': '>{% trans "Attendance %" %}<',
    '>No students found<': '>{% trans "No students found" %}<',
    '>Attendance Actions<': '>{% trans "Attendance Actions" %}<',
    '>Enable Edit Mode for All<': '>{% trans "Enable Edit Mode for All" %}<',
    '>Save All Records<': '>{% trans "Save All Records" %}<',
    '>Reset All<': '>{% trans "Reset All" %}<',
    '>Click \'Enable Edit Mode\' to unlock all fields, then click \'Save All Records\' when done<': '>{% trans "Click \'Enable Edit Mode\' to unlock all fields, then click \'Save All Records\' when done" %}<',

    # student_records.html
    '>Student Profile<': '>{% trans "Student Profile" %}<',
    '>Age:<': '>{% trans "Age:" %}<',
    '>Gender:<': '>{% trans "Gender:" %}<',
    '>Total Present:<': '>{% trans "Total Present:" %}<',
    '>Total Classes:<': '>{% trans "Total Classes:" %}<',
    '>Attendance Rate:<': '>{% trans "Attendance Rate:" %}<',
    '>Detailed Daily Records<': '>{% trans "Detailed Daily Records" %}<',
    '>Filter by Month<': '>{% trans "Filter by Month" %}<',
    '>(All Months)<': '>{% trans "(All Months)" %}<',
    '>View Note History<': '>{% trans "View Note History" %}<',
    '>Locked (> 24hrs)<': '>{% trans "Locked (> 24hrs)" %}<',
    '>Date<': '>{% trans "Date" %}<',
    '>Status<': '>{% trans "Status" %}<',
    '>Daily Note<': '>{% trans "Daily Note" %}<',
    '>Note Added By<': '>{% trans "Note Added By" %}<',
    '>No records found for this selection.<': '>{% trans "No records found for this selection." %}<',
    'title="Edit row"': 'title="{% trans \'Edit row\' %}"',
    'title="Save changes"': 'title="{% trans \'Save changes\' %}"',
    'title="Cancel"': 'title="{% trans \'Cancel\' %}"',
    'title="View Note History"': 'title="{% trans \'View Note History\' %}"',

    # teacher_report.html
    '>Monthly Report<': '>{% trans "Monthly Report" %}<',
    '>Export Excel<': '>{% trans "Export Excel" %}<',
    '>Classroom<': '>{% trans "Classroom" %}<',
    '>Month<': '>{% trans "Month" %}<',
    '>Year<': '>{% trans "Year" %}<',
    '>Apply Filter<': '>{% trans "Apply Filter" %}<',
    '>No data available for this selection<': '>{% trans "No data available for this selection" %}<',
    '>#<': '>{% trans "#" %}<',
    '>Student<': '>{% trans "Student" %}<',
    '>Monthly Notes<': '>{% trans "Monthly Notes" %}<',
    '>No notes this month<': '>{% trans "No notes this month" %}<',
    '>January<': '>{% trans "January" %}<',
    '>February<': '>{% trans "February" %}<',
    '>March<': '>{% trans "March" %}<',
    '>April<': '>{% trans "April" %}<',
    '>May<': '>{% trans "May" %}<',
    '>June<': '>{% trans "June" %}<',
    '>July<': '>{% trans "July" %}<',
    '>August<': '>{% trans "August" %}<',
    '>September<': '>{% trans "September" %}<',
    '>October<': '>{% trans "October" %}<',
    '>November<': '>{% trans "November" %}<',
    '>December<': '>{% trans "December" %}<',
}

files = [
    'templates/dashboards/teacher_dashboard.html',
    'templates/dashboards/class_list.html',
    'templates/dashboards/student_attendance.html',
    'templates/dashboards/student_records.html',
    'templates/dashboards/teacher_report.html',
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply substitutions
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    # Extra blocktrans for attendance
    content = content.replace(
        '<h2 class="mb-4">Student Attendance List - {{ now|date:"F Y" }}</h2>',
        '<h2 class="mb-4">{% blocktrans with my=now|date:"F Y" %}Student Attendance List - {{ my }}{% endblocktrans %}</h2>'
    )

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Injected trans tags into HTML templates.")

# Append to django.po map
translations = {
    "Logout": "ログアウト",
    "Photo": "写真",
    "Name": "名前",
    "Japanese Name": "日本語の名前",
    "Gender": "性別",
    "Age": "年齢",
    "Actions": "アクション",
    "Action": "アクション",
    "Export PDF": "PDFをエクスポート",
    "Classes - Aqua Group": "クラス - Aqua Group",
    "Select a class to view and mark attendance, or manage the class students.": "クラスを選択して出欠を確認・記録するか、生徒を管理します。",
    "Student(s)": "生徒",
    "Attendance": "出席",
    "Students": "生徒",
    "No classes found. They will be created automatically.": "クラスが見つかりません。自動的に作成されます。",
    "Classes": "クラス",
    "Instructions: Enter Japanese names for each student and check the dates they attended.": "指示：各生徒の日本語名を入力し、出席した日付をチェックしてください。",
    "Attendance Dates": "出席日",
    "Attendance %": "出席率",
    "No students found": "生徒が見つかりません",
    "Attendance Actions": "出席管理",
    "Enable Edit Mode for All": "すべての編集モードを有効にする",
    "Save All Records": "すべての記録を保存",
    "Reset All": "すべてリセット",
    "Click 'Enable Edit Mode' to unlock all fields, then click 'Save All Records' when done": "「編集モードを有効にする」をクリックしてすべてのフィールドのロックを解除し、終了したら「すべての記録を保存」をクリックしてください。",
    "Student Profile": "生徒プロフィール",
    "Age:": "年齢：",
    "Gender:": "性別：",
    "Total Present:": "出席合計：",
    "Total Classes:": "合計クラス数：",
    "Attendance Rate:": "出席率：",
    "Detailed Daily Records": "詳細な日次記録",
    "Filter by Month": "月で絞り込み",
    "(All Months)": "（すべての月）",
    "View Note History": "履歴を見る",
    "Locked (> 24hrs)": "ロック済（>24時間）",
    "Date": "日付",
    "Status": "ステータス",
    "Daily Note": "日次ノート",
    "Note Added By": "追加した人",
    "No records found for this selection.": "この条件に対する記録はありません。",
    "Edit row": "編集",
    "Save changes": "保存",
    "Cancel": "キャンセル",
    "Monthly Report": "月次レポート",
    "Export Excel": "Excelをエクスポート",
    "Classroom": "教室",
    "Month": "月",
    "Year": "年",
    "Apply Filter": "フィルターを適用",
    "No data available for this selection": "データがありません",
    "#": "#",
    "Student": "生徒",
    "Monthly Notes": "月次ノート",
    "No notes this month": "今月のノートはありません",
    "January": "1月",
    "February": "2月",
    "March": "3月",
    "April": "4月",
    "May": "5月",
    "June": "6月",
    "July": "7月",
    "August": "8月",
    "September": "9月",
    "October": "10月",
    "November": "11月",
    "December": "12月",
    "Student Attendance List - %(my)s": "生徒出欠リスト - %(my)s",
}

po_file = 'locale/ja/LC_MESSAGES/django.po'

with open(po_file, 'a', encoding='utf-8') as f:
    for eng, jap in translations.items():
        f.write(f'\\nmsgid "{eng}"\\n')
        f.write(f'msgstr "{jap}"\\n\\n')

print("Appended translations to django.po")
