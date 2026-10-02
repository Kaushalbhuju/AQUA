import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('manager', '0011_staffattendance_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffactivitylog',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='activity_logs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
