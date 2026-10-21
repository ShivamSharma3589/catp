from collections import defaultdict
from datetime import date

from campaigns.constants import KPI_UNIT, Kpi, KpiDirection, TrackingStatus

from .metrics import KPI_DIRECTION, compute_kpi, evaluate_status

SUMMABLE = (
    'impressions', 'reach', 'clicks', 'video_views', 'video_completions',
    'conversions', 'conversion_value', 'spend',
)

SECONDARY_KPIS = {
    Kpi.CPL: (Kpi.CVR, Kpi.CTR, Kpi.CPC),
    Kpi.CPC: (Kpi.CTR, Kpi.CPM, Kpi.CLICKS),
    Kpi.CPM: (Kpi.IMPRESSIONS, Kpi.REACH, Kpi.CTR),
    Kpi.CPV: (Kpi.VIEWS, Kpi.CTR, Kpi.CPM),
    Kpi.CLICKS: (Kpi.CTR, Kpi.CPC, Kpi.IMPRESSIONS),
    Kpi.IMPRESSIONS: (Kpi.REACH, Kpi.CPM, Kpi.CLICKS),
    Kpi.REACH: (Kpi.IMPRESSIONS, Kpi.CPM, Kpi.CLICKS),
    Kpi.VIEWS: (Kpi.CPV, Kpi.CTR, Kpi.IMPRESSIONS),
    Kpi.LEADS: (Kpi.CPL, Kpi.CVR, Kpi.CTR),
}

DEFAULT_SECONDARY = (Kpi.CTR, Kpi.CPC, Kpi.CPM)


def _as_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def totals(rows):
    out = {field: 0 for field in SUMMABLE}
    out['days'] = 0
    for row in rows:
        out['days'] += 1
        for field in SUMMABLE:
            value = row.get(field)
            if value is not None:
                out[field] += float(value)
    return out


def group_performance(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['campaign_id']].append(row)
    return grouped


def change_pct(current, previous):
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous * 100


def is_improvement(kpi, current, previous):
    delta = change_pct(current, previous)
    if delta is None or delta == 0:
        return None
    if KPI_DIRECTION[kpi] == KpiDirection.LOWER_IS_BETTER:
        return delta < 0
    return delta > 0


def kpi_block(kpi, current_totals, prior_totals, currency=None, target=None):
    value = compute_kpi(kpi, current_totals)
    previous = compute_kpi(kpi, prior_totals) if prior_totals is not None else None
    unit = KPI_UNIT.get(kpi, 'count')
    block = {
        'key': kpi,
        'label': Kpi(kpi).label,
        'unit': unit,
        'direction': KPI_DIRECTION[kpi],
        'value': round(value, 6) if value is not None else None,
        'previous_value': round(previous, 6) if previous is not None else None,
        'change_pct': _round(change_pct(value, previous)),
        'is_improvement': is_improvement(kpi, value, previous),
        'currency': currency if unit == 'currency' else None,
    }
    if target is not None:
        block['target'] = float(target)
        block['target_attainment_pct'] = _round(
            (float(target) / value * 100) if KPI_DIRECTION[kpi] == KpiDirection.LOWER_IS_BETTER
            and value else (value / float(target) * 100) if value and target else None
        )
    return block


def _round(value, places=4):
    return round(value, places) if value is not None else None


def resolve_status(kpi, value, target, override):
    if override is not None:
        return override.status, 'override'
    if target is None:
        return None, 'no_target'
    status = evaluate_status(
        kpi, value, float(target.target_value),
        target.at_risk_threshold_pct, target.off_track_threshold_pct,
    )
    return status, 'computed'


def daily_series(kpi, rows):
    series = []
    for row in sorted(rows, key=lambda r: str(r['date'])):
        value = compute_kpi(kpi, totals([row]))
        series.append({'date': _as_date(row['date']).isoformat(), 'value': _round(value, 6)})
    return series


def weekly_series(kpi, rows, weeks):
    buckets = {start: [] for start, _ in weeks}
    for row in rows:
        day = _as_date(row['date'])
        for start, end in weeks:
            if start <= day <= end:
                buckets[start].append(row)
                break
    series = []
    for index, (start, end) in enumerate(weeks, start=1):
        bucket = buckets[start]
        series.append({
            'label': f'W{index}',
            'week_start': start.isoformat(),
            'week_end': end.isoformat(),
            'value': _round(compute_kpi(kpi, totals(bucket)), 6) if bucket else None,
        })
    return series


def build_campaign_row(campaign, current_rows, prior_rows, target, override, open_flags,
                       creatives, include_series=True):
    kpi = campaign['primary_kpi']
    current = totals(current_rows)
    prior = totals(prior_rows)
    currency = campaign.get('currency')
    value = compute_kpi(kpi, current)
    status, status_source = resolve_status(kpi, value, target, override)

    secondary = SECONDARY_KPIS.get(kpi, DEFAULT_SECONDARY)
    payload = {
        'platform': campaign['platform'],
        'market': campaign['market'],
        'campaign_id': campaign['campaign_id'],
        'campaign_name': campaign['campaign_name'],
        'campaign_type': campaign.get('campaign_type'),
        'objective': campaign.get('objective'),
        'funnel_stage': campaign.get('funnel_stage'),
        'product_category': campaign.get('product_category'),
        'ad_format': campaign.get('ad_format'),
        'currency': currency,
        'spend': _round(current['spend'], 2),
        'previous_spend': _round(prior['spend'], 2),
        'spend_change_pct': _round(change_pct(current['spend'], prior['spend'])),
        'status': status,
        'status_source': status_source,
        'status_label': TrackingStatus(status).label if status else None,
        'primary_kpi': kpi_block(
            kpi, current, prior, currency,
            target.target_value if target else None,
        ),
        'secondary_kpis': [kpi_block(k, current, prior, currency) for k in secondary],
        'open_flags': open_flags,
        'creative_count': len(creatives),
        'creative': creatives[0] if creatives else None,
    }
    if include_series:
        payload['trend'] = daily_series(kpi, current_rows)
    return payload
