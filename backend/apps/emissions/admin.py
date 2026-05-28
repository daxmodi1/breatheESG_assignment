from django.contrib import admin
from .models import EmissionRecord


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tenant', 'scope', 'category', 'status',
        'quantity_normalised', 'unit_normalised', 'co2e_kg',
        'activity_date', 'is_anomaly',
    )
    list_filter = ('scope', 'status', 'is_anomaly', 'tenant', 'category')
    search_fields = ('category', 'subcategory', 'review_comment')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'activity_date'
