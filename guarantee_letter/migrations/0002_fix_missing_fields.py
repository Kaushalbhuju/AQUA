
# guarantee_letter/migrations/0002_fix_missing_fields.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('guarantee_letter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobguaranteelettertemplate',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='jobguaranteelettertemplate',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='jobguaranteeletter',
            name='job_title',
            field=models.CharField(max_length=200),
        ),
    ]