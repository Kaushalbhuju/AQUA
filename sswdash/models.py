from django.db import models
import os

class Document(models.Model):
    title = models.CharField(max_length=100)
    uploaded_file = models.FileField(upload_to='documents/')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Ensure file is removed from storage when model is deleted
        if self.uploaded_file:
            if os.path.isfile(self.uploaded_file.path):
                os.remove(self.uploaded_file.path)
        super().delete(*args, **kwargs)
