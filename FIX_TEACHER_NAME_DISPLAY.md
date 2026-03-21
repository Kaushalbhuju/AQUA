# 🧪 Troubleshooting: Teacher Name Not Showing

## Problem: Template shows literal code instead of teacher name

If you're seeing this on the page:
```
note.teacher.get_full_name|default:note.teacher.username|default:"Unknown Teacher"
```

Instead of the actual teacher name like "John Smith", here's how to fix it:

---

## 🔍 Step-by-Step Diagnosis

### Step 1: Check Browser Cache

**Symptom:** Browser showing old cached version of page

**Fix:**
1. Press **Ctrl + Shift + R** (hard refresh)
2. Or press **Ctrl + F5**
3. Clear browser cache completely if needed

---

### Step 2: Restart Django Server

**Symptom:** Server hasn't reloaded template changes

**Fix:**
```bash
# Stop server (Ctrl+C in terminal)
# Then restart:
python manage.py runserver
```

---

### Step 3: Check if Note Has Teacher Assigned

**Symptom:** Notes exist but teacher field is NULL

**Run this in Django shell:**
```bash
python manage.py shell
```

Then type:
```python
from dashboard.models import StudentDailyNote

# Get all notes
notes = StudentDailyNote.objects.all()

# Check each note's teacher
for note in notes:
    print(f"Note ID: {note.id}")
    print(f"  Student: {note.student.full_name}")
    print(f"  Teacher: {note.teacher}")
    print(f"  Teacher Full Name: {note.teacher.get_full_name() if note.teacher else 'NULL'}")
    print(f"  Teacher Username: {note.teacher.username if note.teacher else 'NULL'}")
    print("---")
```

**Expected output:**
```
Note ID: 1
  Student: John Doe
  Teacher: john.smith
  Teacher Full Name: John Smith
  Teacher Username: john.smith
---
```

**If you see `Teacher: None`:**
The note doesn't have a teacher assigned! See Step 6 below.

---

### Step 4: Verify Template Syntax

Check the template file has correct syntax:

**Open:** `templates/dashboards/student_records.html`

**Find line ~368:**
```django
{{ item.today_note.teacher.get_full_name|default:item.today_note.teacher.username|default:'Unknown' }}
```

**Should look exactly like this:**
- ✅ Double curly braces: `{{ ... }}`
- ✅ Pipe symbols: `|`
- ✅ Single quotes around 'Unknown'
- ✅ No extra spaces in variable names

**Common mistakes:**
- ❌ Missing closing braces: `{{ ... }`
- ❌ Wrong quotes: `"Unknown"` instead of `'Unknown'`
- ❌ Extra spaces: `item. today_note`
- ❌ HTML entities: `&quot;` instead of actual quotes

---

### Step 5: Check Django Template Settings

**Symptom:** Django not processing templates correctly

**Check:** `rm_system/settings.py`

Look for:
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [...],
        'APP_DIRS': True,  # ← Should be True
        'OPTIONS': {
            'context_processors': [...],
        },
    },
]
```

Make sure `APP_DIRS` is `True`.

---

### Step 6: Fix Notes Without Teachers

**If notes exist but have no teacher:**

Run in Django shell:
```python
from dashboard.models import StudentDailyNote
from accounts.models import User

# Find notes without teacher
null_teacher_notes = StudentDailyNote.objects.filter(teacher__isnull=True)
print(f"Found {null_teacher_notes.count()} notes without teacher")

# Option A: Assign to first available teacher
if null_teacher_notes.exists():
    # Get first teacher user
    teacher = User.objects.filter(role='teacher').first()
    
    if teacher:
        # Assign this teacher to all null notes
        null_teacher_notes.update(teacher=teacher)
        print(f"Assigned {teacher.username} to {null_teacher_notes.count()} notes")
    else:
        print("No teacher users found in database!")

# Option B: Delete notes without teacher (if test data)
# null_teacher_notes.delete()
```

---

### Step 7: Test with Fresh Note

**Create a brand new note to test:**

1. Login as teacher user
2. Go to Student Records page
3. Click Edit on any student
4. Enter Japanese name and note content
5. Click Save
6. Check if teacher name appears

**If it works for new notes but not old ones:**
- Old notes were created before teacher field existed
- Use Step 6 to assign teachers to old notes

---

### Step 8: Check Template Rendering Order

**Issue:** `{% if %}` block might not be executing

**Add debug output temporarily:**

In `student_records.html`, add this right after line 366:

```django
{% if item.today_note %}
<!-- DEBUG: Note exists for {{ item.student.full_name }} -->
<!-- DEBUG: Teacher = {{ item.today_note.teacher }} -->
<!-- DEBUG: Teacher username = {{ item.today_note.teacher.username }} -->

<div class="text-muted" style="font-size: 0.75rem; margin-top: 4px;">
  <i class="fas fa-user-edit"></i> {{ item.today_note.teacher.get_full_name|default:item.today_note.teacher.username|default:'Unknown' }}
</div>
{% else %}
<!-- DEBUG: No note exists for this student -->
{% endif %}
```

**Reload page and view page source (Ctrl+U):**
- Look for `<!-- DEBUG: ... -->` comments
- They'll tell you which condition is failing

---

## 🎯 Quick Fixes to Try NOW

### Fix A: Hard Refresh
Press **Ctrl + Shift + Delete** → Clear cache → Hard refresh

### Fix B: Restart Server
```bash
# Terminal
Ctrl+C
python manage.py runserver
```

### Fix C: Check Database
```bash
python manage.py shell
```
```python
from dashboard.models import StudentDailyNote
note = StudentDailyNote.objects.first()
if note:
    print(f"First note teacher: {note.teacher}")
    print(f"Full name: {note.teacher.get_full_name() if note.teacher else 'None'}")
else:
    print("No notes in database yet")
```

---

## 📊 Expected vs Actual

### What You SHOULD See:

**On web page:**
```
Student attended class today.
👤 John Smith
```

**In page HTML (view source):**
```html
<div class="text-muted" style="font-size: 0.75rem; margin-top: 4px;">
  <i class="fas fa-user-edit"></i> John Smith
</div>
```

### What You're Seeing (PROBLEM):

**On web page:**
```
Student attended class today.
👤 {{ item.today_note.teacher.get_full_name|default:item.today_note.teacher.username|default:'Unknown' }}
```

**This means Django template is NOT being processed!**

---

## 🚨 Most Likely Causes

### Cause 1: Browser Cache (90% of cases)
**Fix:** Ctrl + Shift + R (hard refresh)

### Cause 2: Server Not Restarted
**Fix:** Stop and restart Django server

### Cause 3: Template File Not Saved
**Fix:** Make sure you saved the file after editing

### Cause 4: Wrong Template Being Used
**Fix:** Check which template file Django is actually using

### Cause 5: Notes Created Before Teacher Field Existed
**Fix:** Update old notes with teacher (Step 6)

---

## 💡 Ultimate Test

**Delete all notes and create fresh one:**

```python
# In Django shell
from dashboard.models import StudentDailyNote
StudentDailyNote.objects.all().delete()
print("All notes deleted")
```

Then:
1. Create new note through web interface
2. Save it
3. Check if teacher name appears

**If YES:** Old notes had NULL teacher field  
**If NO:** Template or server issue

---

## 📞 What to Report Back

After trying fixes above, tell me:

1. **Did hard refresh help?** [YES/NO]
2. **Did server restart help?** [YES/NO]
3. **What does shell say about teacher field?**
   ```
   python manage.py shell
   >>> from dashboard.models import StudentDailyNote
   >>> note = StudentDailyNote.objects.first()
   >>> print(note.teacher)  # What does this show?
   ```
4. **Screenshot of what you see on the page**

---

**Try these steps NOW and let me know which one works!**
