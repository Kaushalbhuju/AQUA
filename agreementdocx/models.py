from django.db import models

class Agreement(models.Model):
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='agreements/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
