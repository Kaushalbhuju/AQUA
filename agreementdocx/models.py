from django.db import models

class Agreement(models.Model):
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='agreements/')
    year = models.IntegerField(default=2026, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
