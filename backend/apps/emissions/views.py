from django.utils import timezone
from django.db.models import Count, Sum, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response

from apps.tenants.models import TenantUser
from apps.review.models import AuditLog
from .models import EmissionRecord
from .serializers import EmissionRecordSerializer, EmissionRecordReviewSerializer


class EmissionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = EmissionRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            profile = TenantUser.objects.get(user=self.request.user)
        except TenantUser.DoesNotExist:
            return EmissionRecord.objects.none()

        qs = EmissionRecord.objects.filter(tenant=profile.tenant).select_related(
            'source_ingestion', 'reviewed_by'
        )

        # Filters
        s = self.request.query_params.get('status')
        if s:
            qs = qs.filter(status=s.upper())
        scope = self.request.query_params.get('scope')
        if scope:
            qs = qs.filter(scope=int(scope))
        source = self.request.query_params.get('source_type')
        if source:
            qs = qs.filter(source_ingestion__source_type=source.upper())
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(activity_date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(activity_date__lte=date_to)
        ingestion_id = self.request.query_params.get('ingestion_id')
        if ingestion_id:
            qs = qs.filter(source_ingestion_id=ingestion_id)
        anomaly = self.request.query_params.get('anomaly')
        if anomaly:
            qs = qs.filter(is_anomaly=(anomaly.lower() == 'true'))

        return qs

    @action(detail=True, methods=['patch'], url_path='review')
    def review_record(self, request, pk=None):
        record = self.get_object()
        if record.is_locked:
            return Response({'error': 'Record is locked'}, status=status.HTTP_400_BAD_REQUEST)

        ser = EmissionRecordReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        old_status = record.status
        record.status = ser.validated_data['action']
        record.review_comment = ser.validated_data.get('comment', '')
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.save()

        try:
            profile = TenantUser.objects.get(user=request.user)
            AuditLog.objects.create(
                tenant=profile.tenant, actor=request.user,
                action=ser.validated_data['action'],
                target_type='EmissionRecord', target_id=record.id,
                detail={'old_status': old_status, 'new_status': record.status,
                        'comment': record.review_comment},
            )
        except TenantUser.DoesNotExist:
            pass

        return Response(EmissionRecordSerializer(record).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    try:
        profile = TenantUser.objects.get(user=request.user)
    except TenantUser.DoesNotExist:
        return Response({'error': 'No tenant'}, status=status.HTTP_400_BAD_REQUEST)

    qs = EmissionRecord.objects.filter(tenant=profile.tenant)

    by_status = dict(qs.values_list('status').annotate(c=Count('id')).values_list('status', 'c'))
    by_scope = dict(qs.values_list('scope').annotate(c=Count('id')).values_list('scope', 'c'))
    by_source = dict(
        qs.values_list('source_ingestion__source_type')
        .annotate(c=Count('id'))
        .values_list('source_ingestion__source_type', 'c')
    )
    total_co2e = qs.aggregate(total=Sum('co2e_kg'))['total']

    scope_co2e = {}
    for s in [1, 2, 3]:
        val = qs.filter(scope=s).aggregate(total=Sum('co2e_kg'))['total']
        scope_co2e[f'scope_{s}'] = float(val) if val else 0.0

    return Response({
        'total_records': qs.count(),
        'by_status': by_status,
        'by_scope': by_scope,
        'by_source': by_source,
        'total_co2e_kg': total_co2e,
        'scope_co2e': scope_co2e,
    })
