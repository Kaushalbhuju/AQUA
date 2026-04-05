from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.CharField(help_text='e.g. BK-ENG-001', max_length=30, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('total_stock', models.PositiveIntegerField(default=1)),
                ('issued_count', models.PositiveIntegerField(default=0)),
                ('current_holder', models.CharField(blank=True, help_text='Name of last assigned student/person', max_length=255, null=True)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='qr_codes/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Book',
                'verbose_name_plural': 'Books',
                'ordering': ['id'],
            },
        ),
    ]
