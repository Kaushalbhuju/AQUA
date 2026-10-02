from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0012_preserve_staff_activity_on_user_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffregistration',
            name='role',
            field=models.CharField(
                choices=[
                    ('teacher', 'Teacher'),
                    ('receptionist', 'Receptionist'),
                    ('manager', 'Manager'),
                    ('office_helper', 'Office Helper'),
                    ('chairman', 'Chairman'),
                ],
                default='teacher',
                max_length=20,
            ),
        ),
    ]
