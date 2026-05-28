from django.contrib import admin
from .models import RawIngestion


@admin.register(RawIngestion)
class RawIngestionAdmin(admin.ModelAdmin):
    list_display = ('filename', 'source_type', 'tenant', 'status', 'row_count', 'uploaded_at')
    list_filter = ('source_type', 'status', 'tenant')
    search_fields = ('filename',)
    readonly_fields = ('uploaded_at',)
