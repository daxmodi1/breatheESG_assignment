from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True, default='system')

    class Meta:
        model = AuditLog
        fields = ('id', 'tenant', 'actor', 'actor_name', 'action', 'target_type',
                  'target_id', 'detail', 'timestamp')
        read_only_fields = fields
