import numpy as np
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.tenants.models import TenantUser
from apps.emissions.models import EmissionRecord
from apps.review.models import AuditLog
from .models import RawIngestion
from .serializers import RawIngestionSerializer, FileUploadSerializer
from .parsers.sap import parse_sap_file
from .parsers.utility import parse_utility_file
from .parsers.travel import parse_travel_file


PARSER_MAP = {
    'SAP': parse_sap_file,
    'UTILITY': parse_utility_file,
    'TRAVEL': parse_travel_file,
}


def _detect_anomalies(records, tenant):
    """Flag records whose quantity is > 3 standard deviations from the mean for their category."""
    existing = EmissionRecord.objects.filter(tenant=tenant).values_list('quantity_normalised', 'category')
    cat_values = {}
    for val, cat in existing:
        cat_values.setdefault(cat, []).append(float(val))
    for rec in records:
        cat = rec.get('category', '')
        vals = cat_values.get(cat, [])
        if len(vals) >= 5:
            arr = np.array(vals)
            mean, std = arr.mean(), arr.std()
            if std > 0 and abs(float(rec['quantity_normalised']) - mean) > 3 * std:
                rec['is_anomaly'] = True
                rec['anomaly_reason'] = f'z-score > 3 (mean={mean:.2f}, std={std:.2f})'
    return records


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_file(request):
    """Upload and parse a data file (SAP / Utility / Travel)."""
    serializer = FileUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uploaded_file = serializer.validated_data['file']
    source_type = serializer.validated_data['source_type']

    try:
        profile = TenantUser.objects.select_related('tenant').get(user=request.user)
        tenant = profile.tenant
    except TenantUser.DoesNotExist:
        return Response({'error': 'User has no tenant assigned'}, status=status.HTTP_400_BAD_REQUEST)

    ingestion = RawIngestion.objects.create(
        tenant=tenant, source_type=source_type,
        uploaded_by=request.user, filename=uploaded_file.name,
        raw_file=uploaded_file,
    )

    try:
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        parser = PARSER_MAP.get(source_type)
        if not parser:
            ingestion.status = 'FAILED'
            ingestion.parse_errors = [{'row': 0, 'error': f'Unknown source type: {source_type}'}]
            ingestion.save()
            return Response({'error': f'Unknown source type: {source_type}'}, status=status.HTTP_400_BAD_REQUEST)

        result = parser(file_content, uploaded_file.name)
        parsed_records = result['records']
        parse_errors = result['errors']

        parsed_records = _detect_anomalies(parsed_records, tenant)

        emission_records = []
        for rec in parsed_records:
            emission_records.append(EmissionRecord(
                tenant=tenant, source_ingestion=ingestion,
                source_row_index=rec['source_row_index'], source_row_raw=rec['source_row_raw'],
                activity_date=rec['activity_date'], period_start=rec['period_start'],
                period_end=rec['period_end'], scope=rec['scope'],
                category=rec['category'], subcategory=rec.get('subcategory', ''),
                quantity_raw=rec['quantity_raw'], unit_raw=rec['unit_raw'],
                quantity_normalised=rec['quantity_normalised'], unit_normalised=rec['unit_normalised'],
                emission_factor=rec.get('emission_factor'),
                emission_factor_source=rec.get('emission_factor_source', ''),
                co2e_kg=rec.get('co2e_kg'),
                metadata=rec.get('metadata', {}),
                is_anomaly=rec.get('is_anomaly', False),
                anomaly_reason=rec.get('anomaly_reason', ''),
                status='FLAGGED' if rec.get('is_anomaly') else 'PENDING',
            ))

        EmissionRecord.objects.bulk_create(emission_records)

        ingestion.row_count = len(emission_records)
        ingestion.parse_errors = parse_errors
        ingestion.status = 'DONE'
        ingestion.save()

        AuditLog.objects.create(
            tenant=tenant, actor=request.user, action='UPLOADED',
            target_type='RawIngestion', target_id=ingestion.id,
            detail={'filename': uploaded_file.name, 'source_type': source_type,
                    'rows_parsed': len(emission_records), 'errors': len(parse_errors)},
        )

        return Response({
            'ingestion_id': ingestion.id, 'status': 'DONE',
            'rows_parsed': len(emission_records),
            'rows_flagged': sum(1 for r in emission_records if r.is_anomaly),
            'parse_errors': parse_errors,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        ingestion.status = 'FAILED'
        ingestion.parse_errors = [{'row': 0, 'error': str(e)}]
        ingestion.save()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RawIngestionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RawIngestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        try:
            profile = TenantUser.objects.get(user=self.request.user)
            return RawIngestion.objects.filter(tenant=profile.tenant)
        except TenantUser.DoesNotExist:
            return RawIngestion.objects.none()
