from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action', 'target_type', 'target_id', 'tenant')
    list_filter = ('action', 'target_type', 'tenant')
    search_fields = ('actor__username',)
    readonly_fields = ('timestamp',)
