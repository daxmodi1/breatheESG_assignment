from django.db import models
from django.contrib.auth.models import User


class Tenant(models.Model):
    """Organisation / company — the multi-tenancy anchor."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TenantUser(models.Model):
    """Maps a Django User to exactly one Tenant + role."""
    ROLE_CHOICES = [
        ('analyst', 'Analyst'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username} @ {self.tenant.slug} ({self.role})"
