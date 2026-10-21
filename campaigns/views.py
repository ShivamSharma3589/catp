import csv

from django.http import Http404, StreamingHttpResponse
from rest_framework import status as http_status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import CampaignFlag, CampaignNote, CampaignTarget
from .serializers import CampaignFlagSerializer, CampaignNoteSerializer, CampaignTargetSerializer

EXPORT_COLUMNS = (
    'platform', 'market', 'campaign_name', 'funnel_stage', 'product_category',
    'primary_kpi', 'value', 'vs_prior_pct', 'spend', 'currency', 'status',
)


class OverviewView(APIView):
    def get(self, request):
        return Response(services.overview(request.query_params))


class FilterOptionsView(APIView):
    def get(self, request):
        return Response(services.filter_options(request.query_params))


class CampaignListView(APIView):
    def get(self, request):
        return Response(services.campaign_list(request.query_params))


class CampaignDetailView(APIView):
    def get(self, request, platform, campaign_id):
        payload = services.campaign_detail(platform, campaign_id, request.query_params)
        if payload is None:
            raise Http404('Campaign not found.')
        return Response(payload)


class CampaignExportView(APIView):
    def get(self, request):
        data = services.campaign_list(request.query_params)
        response = StreamingHttpResponse(
            self._rows(data['results']), content_type='text/csv'
        )
        response['Content-Disposition'] = 'attachment; filename="campaigns.csv"'
        return response

    def _rows(self, results):
        writer = csv.writer(Echo())
        yield writer.writerow(EXPORT_COLUMNS)
        for row in results:
            yield writer.writerow([
                row['platform'],
                row['market'],
                row['campaign_name'],
                row['funnel_stage'],
                row['product_category'],
                row['primary_kpi']['label'],
                row['primary_kpi']['value'],
                row['primary_kpi']['change_pct'],
                row['spend'],
                row['currency'],
                row['status'],
            ])


class Echo:
    def write(self, value):
        return value


class CampaignScopedMixin:
    def scope(self):
        return self.kwargs['platform'], self.kwargs['campaign_id']


class NoteListCreateView(CampaignScopedMixin, ListCreateAPIView):
    serializer_class = CampaignNoteSerializer

    def get_queryset(self):
        platform, campaign_id = self.scope()
        return CampaignNote.objects.filter(
            platform=platform, campaign_id=campaign_id
        ).select_related('author')

    def perform_create(self, serializer):
        platform, campaign_id = self.scope()
        serializer.save(platform=platform, campaign_id=campaign_id, author=self.request.user)


class NoteDetailView(CampaignScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = CampaignNoteSerializer

    def get_queryset(self):
        platform, campaign_id = self.scope()
        return CampaignNote.objects.filter(platform=platform, campaign_id=campaign_id)


class FlagListCreateView(CampaignScopedMixin, ListCreateAPIView):
    serializer_class = CampaignFlagSerializer

    def get_queryset(self):
        platform, campaign_id = self.scope()
        queryset = CampaignFlag.objects.filter(
            platform=platform, campaign_id=campaign_id
        ).select_related('raised_by', 'resolved_by')
        state = self.request.query_params.get('status')
        return queryset.filter(status=state) if state else queryset

    def perform_create(self, serializer):
        platform, campaign_id = self.scope()
        serializer.save(platform=platform, campaign_id=campaign_id, raised_by=self.request.user)


class FlagDetailView(CampaignScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = CampaignFlagSerializer

    def get_queryset(self):
        platform, campaign_id = self.scope()
        return CampaignFlag.objects.filter(platform=platform, campaign_id=campaign_id)

    def perform_update(self, serializer):
        from django.utils import timezone

        instance = serializer.instance
        becoming_resolved = (
            serializer.validated_data.get('status') == CampaignFlag.Status.RESOLVED
            and instance.status != CampaignFlag.Status.RESOLVED
        )
        if becoming_resolved:
            serializer.save(resolved_by=self.request.user, resolved_at=timezone.now())
        else:
            serializer.save()


class TargetView(CampaignScopedMixin, APIView):
    def get(self, request, platform, campaign_id):
        target = CampaignTarget.objects.filter(
            platform=platform, campaign_id=campaign_id, is_primary=True
        ).first()
        if target is None:
            raise Http404('No target set for this campaign.')
        return Response(CampaignTargetSerializer(target).data)

    def put(self, request, platform, campaign_id):
        target = CampaignTarget.objects.filter(
            platform=platform, campaign_id=campaign_id, is_primary=True
        ).first()
        serializer = CampaignTargetSerializer(target, data=request.data, partial=target is not None)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            platform=platform, campaign_id=campaign_id, is_primary=True,
            updated_by=request.user,
        )
        return Response(
            serializer.data,
            status=http_status.HTTP_200_OK if target else http_status.HTTP_201_CREATED,
        )
