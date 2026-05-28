from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Tenant, TenantUser
from .serializers import TenantSerializer, TenantUserSerializer, UserSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Return the current user + their tenant info."""
    user = request.user
    try:
        profile = TenantUser.objects.select_related('tenant').get(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'tenant': TenantSerializer(profile.tenant).data,
            'role': profile.role,
        })
    except TenantUser.DoesNotExist:
        return Response({
            'user': UserSerializer(user).data,
            'tenant': None,
            'role': None,
        })


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tenant.objects.all()
