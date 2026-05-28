from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant


class AuditLog(models.Model):
    """
    Append-only audit trail. One row per action. Never deleted.
    """
    ACTION_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EDITED', 'Edited'),
        ('FLAGGED', 'Flagged'),
        ('LOCKED', 'Locked'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, help_text='Model name: EmissionRecord, RawIngestion')
    target_id = models.IntegerField()
    detail = models.JSONField(default=dict, blank=True, help_text='Before/after for edits')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"[{self.action}] {self.target_type}#{self.target_id} by {self.actor} @ {self.timestamp:%Y-%m-%d %H:%M}"
