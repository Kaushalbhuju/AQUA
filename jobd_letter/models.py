from django.conf import settings
from django.db import models

class JobDemandLetter(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to='job_demand_letters/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_letters"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Job Demand Letter"
        verbose_name_plural = "Job Demand Letters"

    def __str__(self):
        return self.title