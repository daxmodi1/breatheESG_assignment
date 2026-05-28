from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant


class RawIngestion(models.Model):
    """
    Immutable record of exactly what arrived.
    Never modified after creation — the source-of-truth for auditability.
    """
    SOURCE_TYPES = [
        ('SAP', 'SAP'),
        ('UTILITY', 'Utility'),
        ('TRAVEL', 'Travel'),
    ]
    STATUS_CHOICES = [
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ingestions')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    raw_file = models.FileField(upload_to='raw_ingestions/')
    row_count = models.IntegerField(default=0)
    parse_errors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Raw Ingestions'

    def __str__(self):
        return f"[{self.source_type}] {self.filename} ({self.status})"
