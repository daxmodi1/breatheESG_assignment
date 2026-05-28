from rest_framework import viewsets, permissions
from apps.tenants.models import TenantUser
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            profile = TenantUser.objects.get(user=self.request.user)
            return AuditLog.objects.filter(tenant=profile.tenant).select_related('actor')
        except TenantUser.DoesNotExist:
            return AuditLog.objects.none()
