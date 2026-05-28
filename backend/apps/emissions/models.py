from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant
from apps.ingestion.models import RawIngestion


class EmissionRecord(models.Model):
    """
    A single normalised emission data row.
    Carries both the raw and normalised values for full auditability.
    """
    SCOPE_CHOICES = [
        (1, 'Scope 1'),
        (2, 'Scope 2'),
        (3, 'Scope 3'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged'),
    ]

    # ---- Multi-tenancy ----
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='emission_records')

    # ---- Source-of-truth tracking ----
    source_ingestion = models.ForeignKey(RawIngestion, on_delete=models.CASCADE, related_name='records')
    source_row_index = models.IntegerField(help_text='Row index in the original file')
    source_row_raw = models.JSONField(help_text='Exact raw dict before normalisation')

    # ---- Normalised values ----
    activity_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=100, help_text='e.g. stationary_combustion, electricity, air_travel')
    subcategory = models.CharField(max_length=100, blank=True)

    # ---- Dual quantities (raw + normalised) ----
    quantity_raw = models.DecimalField(max_digits=18, decimal_places=6)
    unit_raw = models.CharField(max_length=50)
    quantity_normalised = models.DecimalField(max_digits=18, decimal_places=6)
    unit_normalised = models.CharField(max_length=50, help_text='Always kWh or tCO2e')

    # ---- Emission factor ----
    emission_factor = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    emission_factor_source = models.CharField(max_length=100, blank=True, help_text='e.g. DEFRA 2023, IPCC AR6')
    co2e_kg = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)

    # ---- Source-specific metadata ----
    metadata = models.JSONField(default=dict, blank=True, help_text='plant_code, meter_id, route, etc.')

    # ---- Review state ----
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_records'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)

    # ---- Anomaly detection ----
    is_anomaly = models.BooleanField(default=False)
    anomaly_reason = models.CharField(max_length=255, blank=True)

    # ---- Edit trail ----
    last_edited_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='edited_records'
    )
    last_edited_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False, help_text='True after approval + audit sign-off')

    # ---- Timestamps ----
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-activity_date', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'scope']),
            models.Index(fields=['tenant', 'activity_date']),
        ]

    def __str__(self):
        return f"[Scope {self.scope}] {self.category} — {self.quantity_normalised} {self.unit_normalised} ({self.status})"
