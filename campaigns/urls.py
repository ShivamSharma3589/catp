from django.urls import path

from .views import (
    CampaignDetailView,
    CampaignExportView,
    CampaignListView,
    FilterOptionsView,
    FlagDetailView,
    FlagListCreateView,
    NoteDetailView,
    NoteListCreateView,
    OverviewView,
    TargetView,
)

scoped = 'campaigns/<str:platform>/<str:campaign_id>'

urlpatterns = [
    path('overview/', OverviewView.as_view(), name='overview'),
    path('filters/', FilterOptionsView.as_view(), name='filter-options'),
    path('campaigns/', CampaignListView.as_view(), name='campaign-list'),
    path('campaigns/export/', CampaignExportView.as_view(), name='campaign-export'),
    path(f'{scoped}/', CampaignDetailView.as_view(), name='campaign-detail'),
    path(f'{scoped}/notes/', NoteListCreateView.as_view(), name='campaign-notes'),
    path(f'{scoped}/notes/<int:pk>/', NoteDetailView.as_view(), name='campaign-note-detail'),
    path(f'{scoped}/flags/', FlagListCreateView.as_view(), name='campaign-flags'),
    path(f'{scoped}/flags/<int:pk>/', FlagDetailView.as_view(), name='campaign-flag-detail'),
    path(f'{scoped}/target/', TargetView.as_view(), name='campaign-target'),
]
