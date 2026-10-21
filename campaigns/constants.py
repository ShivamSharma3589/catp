from django.db import models


class Platform(models.TextChoices):
    GOOGLE = 'google', 'Google'
    YOUTUBE = 'youtube', 'YouTube'
    META = 'meta', 'Meta'
    LINKEDIN = 'linkedin', 'LinkedIn'


class FunnelStage(models.TextChoices):
    UPPER = 'upper', 'Upper'
    MID = 'mid', 'Mid'
    LOWER = 'lower', 'Lower'
    FULL = 'full', 'Full'


class Market(models.TextChoices):
    IT = 'IT', 'Italy'
    FR = 'FR', 'France'
    UK = 'UK', 'United Kingdom'
    DE = 'DE', 'Germany'


class Kpi(models.TextChoices):
    CPL = 'cpl', 'CPL'
    CPC = 'cpc', 'CPC'
    CPM = 'cpm', 'CPM'
    CPV = 'cpv', 'CPV'
    CTR = 'ctr', 'CTR'
    CVR = 'cvr', 'CVR'
    CLICKS = 'clicks', 'Clicks'
    IMPRESSIONS = 'impressions', 'Impressions'
    REACH = 'reach', 'Reach'
    VIEWS = 'views', 'Views'
    LEADS = 'leads', 'Leads'
    SPEND = 'spend', 'Spend'


class TrackingStatus(models.TextChoices):
    ON_TRACK = 'on_track', 'On Track'
    AT_RISK = 'at_risk', 'At Risk'
    OFF_TRACK = 'off_track', 'Off Track'


class KpiDirection(models.TextChoices):
    LOWER_IS_BETTER = 'lower', 'Lower is better'
    HIGHER_IS_BETTER = 'higher', 'Higher is better'


KPI_DIRECTION = {
    Kpi.CPL: KpiDirection.LOWER_IS_BETTER,
    Kpi.CPC: KpiDirection.LOWER_IS_BETTER,
    Kpi.CPM: KpiDirection.LOWER_IS_BETTER,
    Kpi.CPV: KpiDirection.LOWER_IS_BETTER,
    Kpi.CTR: KpiDirection.HIGHER_IS_BETTER,
    Kpi.CVR: KpiDirection.HIGHER_IS_BETTER,
    Kpi.CLICKS: KpiDirection.HIGHER_IS_BETTER,
    Kpi.IMPRESSIONS: KpiDirection.HIGHER_IS_BETTER,
    Kpi.REACH: KpiDirection.HIGHER_IS_BETTER,
    Kpi.VIEWS: KpiDirection.HIGHER_IS_BETTER,
    Kpi.LEADS: KpiDirection.HIGHER_IS_BETTER,
    Kpi.SPEND: KpiDirection.HIGHER_IS_BETTER,
}

KPI_UNIT = {
    Kpi.CPL: 'currency',
    Kpi.CPC: 'currency',
    Kpi.CPM: 'currency',
    Kpi.CPV: 'currency',
    Kpi.SPEND: 'currency',
    Kpi.CTR: 'percent',
    Kpi.CVR: 'percent',
    Kpi.CLICKS: 'count',
    Kpi.IMPRESSIONS: 'count',
    Kpi.REACH: 'count',
    Kpi.VIEWS: 'count',
    Kpi.LEADS: 'count',
}

MARKET_CURRENCY = {
    Market.IT: 'EUR',
    Market.FR: 'EUR',
    Market.DE: 'EUR',
    Market.UK: 'GBP',
}
