from rest_framework import serializers
from .models import EmissionRecord


class EmissionRecordSerializer(serializers.ModelSerializer):
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, default='')
    source_filename = serializers.CharField(source='source_ingestion.filename', read_only=True, default='')

    class Meta:
        model = EmissionRecord
        fields = '__all__'
        read_only_fields = (
            'tenant', 'source_ingestion', 'source_row_index', 'source_row_raw',
            'created_at', 'updated_at',
        )


class EmissionRecordReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['APPROVED', 'REJECTED', 'FLAGGED', 'PENDING'])
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class DashboardSummarySerializer(serializers.Serializer):
    total_records = serializers.IntegerField()
    by_status = serializers.DictField()
    by_scope = serializers.DictField()
    by_source = serializers.DictField()
    total_co2e_kg = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
