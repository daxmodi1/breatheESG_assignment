from rest_framework import serializers
from .models import RawIngestion


class RawIngestionSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, default='')

    class Meta:
        model = RawIngestion
        fields = (
            'id', 'tenant', 'source_type', 'uploaded_by', 'uploaded_by_name',
            'uploaded_at', 'filename', 'row_count', 'parse_errors', 'status',
        )
        read_only_fields = ('tenant', 'uploaded_by', 'uploaded_at', 'row_count', 'parse_errors', 'status')


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    source_type = serializers.ChoiceField(choices=['SAP', 'UTILITY', 'TRAVEL'])
