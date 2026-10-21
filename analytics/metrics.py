from campaigns.constants import Kpi, KpiDirection, TrackingStatus

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


def _divide(numerator, denominator):
    if not denominator:
        return None
    return numerator / denominator


def compute_kpi(kpi, totals):
    spend = totals.get('spend') or 0
    impressions = totals.get('impressions') or 0
    clicks = totals.get('clicks') or 0
    conversions = totals.get('conversions') or 0
    reach = totals.get('reach') or 0
    video_views = totals.get('video_views') or 0

    if kpi == Kpi.CPL:
        return _divide(spend, conversions)
    if kpi == Kpi.CPC:
        return _divide(spend, clicks)
    if kpi == Kpi.CPM:
        return _divide(spend * 1000, impressions)
    if kpi == Kpi.CPV:
        return _divide(spend, video_views)
    if kpi == Kpi.CTR:
        return _divide(clicks, impressions)
    if kpi == Kpi.CVR:
        return _divide(conversions, clicks)
    if kpi == Kpi.CLICKS:
        return clicks
    if kpi == Kpi.IMPRESSIONS:
        return impressions
    if kpi == Kpi.REACH:
        return reach
    if kpi == Kpi.VIEWS:
        return video_views
    if kpi == Kpi.LEADS:
        return conversions
    if kpi == Kpi.SPEND:
        return spend
    return None


def performance_ratio(kpi, value, target):
    if value is None or not target:
        return None
    if KPI_DIRECTION[kpi] == KpiDirection.LOWER_IS_BETTER:
        return target / value if value else None
    return value / target


def evaluate_status(kpi, value, target, at_risk_pct=10, off_track_pct=25):
    ratio = performance_ratio(kpi, value, target)
    if ratio is None:
        return None
    shortfall_pct = (1 - ratio) * 100
    if shortfall_pct >= float(off_track_pct):
        return TrackingStatus.OFF_TRACK
    if shortfall_pct >= float(at_risk_pct):
        return TrackingStatus.AT_RISK
    return TrackingStatus.ON_TRACK


def target_for_status(kpi, value, status):
    if value is None:
        return None
    factor = {
        TrackingStatus.ON_TRACK: 1.12,
        TrackingStatus.AT_RISK: 0.85,
        TrackingStatus.OFF_TRACK: 0.68,
    }[status]
    if KPI_DIRECTION[kpi] == KpiDirection.LOWER_IS_BETTER:
        return value * factor
    return value / factor
