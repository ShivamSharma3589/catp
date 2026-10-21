from django.conf import settings
from django.db import models

from .constants import Kpi, KpiDirection, Platform, TrackingStatus


class CampaignScopedModel(models.Model):
    platform = models.CharField(max_length=20, choices=Platform.choices)
    campaign_id = models.CharField(max_length=128)

    class Meta:
        abstract = True


class CampaignTarget(CampaignScopedModel):
    kpi = models.CharField(max_length=20, choices=Kpi.choices)
    target_value = models.DecimalField(max_digits=16, decimal_places=4)
    currency = models.CharField(max_length=3, blank=True)
    direction = models.CharField(
        max_length=10, choices=KpiDirection.choices, default=KpiDirection.LOWER_IS_BETTER
    )
    at_risk_threshold_pct = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    off_track_threshold_pct = models.DecimalField(max_digits=6, decimal_places=2, default=25)
    is_primary = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='updated_targets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_targets'
        constraints = [
            models.UniqueConstraint(
                fields=('platform', 'campaign_id', 'kpi'), name='uniq_target_per_campaign_kpi'
            )
        ]
        indexes = [models.Index(fields=('platform', 'campaign_id'))]

    def __str__(self):
        return f'{self.platform}:{self.campaign_id} {self.kpi}={self.target_value}'


class CampaignNote(CampaignScopedModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='notes'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_notes'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('platform', 'campaign_id', '-created_at'))]

    def __str__(self):
        return f'Note on {self.platform}:{self.campaign_id}'


class CampaignFlag(CampaignScopedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        RESOLVED = 'resolved', 'Resolved'

    class Reason(models.TextChoices):
        PERFORMANCE = 'performance', 'Performance'
        CREATIVE = 'creative', 'Creative'
        TRACKING = 'tracking', 'Tracking'
        BUDGET = 'budget', 'Budget'
        OTHER = 'other', 'Other'

    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    detail = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='raised_flags'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='resolved_flags',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'campaign_flags'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('platform', 'campaign_id')),
            models.Index(fields=('status',)),
        ]

    def __str__(self):
        return f'{self.get_status_display()} flag on {self.platform}:{self.campaign_id}'


class StatusOverride(CampaignScopedModel):
    status = models.CharField(max_length=20, choices=TrackingStatus.choices)
    note = models.CharField(max_length=255, blank=True)
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='status_overrides'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_status_overrides'
        constraints = [
            models.UniqueConstraint(
                fields=('platform', 'campaign_id'), name='uniq_status_override_per_campaign'
            )
        ]

    def __str__(self):
        return f'{self.platform}:{self.campaign_id} -> {self.status}'
