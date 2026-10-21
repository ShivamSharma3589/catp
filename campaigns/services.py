from collections import defaultdict

from django.conf import settings

from analytics.aggregation import (
    build_campaign_row,
    change_pct,
    daily_series,
    group_performance,
    kpi_block,
    totals,
    weekly_series,
    _round,
)
from analytics.metrics import compute_kpi
from analytics.periods import iso_weeks, resolve_period
from analytics.repository import get_repository
from campaigns.constants import Kpi, Platform, TrackingStatus
from campaigns.models import CampaignFlag, CampaignTarget, StatusOverride

TEXT_FILTERS = {
    'market': 'market',
    'platform': 'platform',
    'funnel_stage': 'funnel_stage',
    'category': 'product_category',
    'primary_kpi': 'primary_kpi',
}


def _multi(params, key):
    values = []
    for raw in params.getlist(key) if hasattr(params, 'getlist') else [params.get(key)]:
        if raw:
            values.extend(v.strip() for v in str(raw).split(',') if v.strip())
    return values


def _filter_campaigns(campaigns, params):
    rows = list(campaigns)
    for param, field in TEXT_FILTERS.items():
        wanted = _multi(params, param)
        if wanted:
            lowered = {w.lower() for w in wanted}
            rows = [r for r in rows if str(r.get(field, '')).lower() in lowered]
    search = (params.get('search') or '').strip().lower()
    if search:
        rows = [r for r in rows if search in r['campaign_name'].lower()]
    return rows


def _postgres_context(campaign_ids):
    targets = {
        (t.platform, t.campaign_id): t
        for t in CampaignTarget.objects.filter(campaign_id__in=campaign_ids, is_primary=True)
    }
    overrides = {
        (o.platform, o.campaign_id): o
        for o in StatusOverride.objects.filter(campaign_id__in=campaign_ids)
    }
    flags = defaultdict(int)
    for flag in CampaignFlag.objects.filter(
        campaign_id__in=campaign_ids, status=CampaignFlag.Status.OPEN
    ):
        flags[(flag.platform, flag.campaign_id)] += 1
    return targets, overrides, flags


def _creatives_by_campaign(repository, campaign_ids):
    grouped = defaultdict(list)
    for creative in repository.creatives(campaign_ids):
        grouped[creative['campaign_id']].append(creative)
    for rows in grouped.values():
        rows.sort(key=lambda r: r.get('position') or 0)
    return grouped


def _assemble(repository, params, campaigns, include_series=True, include_creatives=True):
    period = resolve_period(params, repository.data_end_date())
    previous = period.previous
    ids = [c['campaign_id'] for c in campaigns]

    current_rows = repository.performance(period.start, period.end, ids)
    prior_rows = repository.performance(previous.start, previous.end, ids)
    current_by_campaign = group_performance(current_rows)
    prior_by_campaign = group_performance(prior_rows)

    targets, overrides, flags = _postgres_context(ids)
    creatives = _creatives_by_campaign(repository, ids) if include_creatives else defaultdict(list)

    rows = []
    for campaign in campaigns:
        key = (campaign['platform'], campaign['campaign_id'])
        rows.append(build_campaign_row(
            campaign,
            current_by_campaign.get(campaign['campaign_id'], []),
            prior_by_campaign.get(campaign['campaign_id'], []),
            targets.get(key),
            overrides.get(key),
            flags.get(key, 0),
            creatives.get(campaign['campaign_id'], []),
            include_series=include_series,
        ))
    return period, previous, rows, current_rows, prior_rows


ORDERING = {
    'name': lambda r: r['campaign_name'],
    'spend': lambda r: -(r['spend'] or 0),
    'value': lambda r: -(r['primary_kpi']['value'] or 0),
    'change': lambda r: -(r['primary_kpi']['change_pct'] or 0),
    'status': lambda r: ('on_track', 'at_risk', 'off_track').index(r['status'])
    if r['status'] else 99,
    'platform': lambda r: r['platform'],
    'market': lambda r: r['market'],
}


def campaign_list(params):
    repository = get_repository()
    campaigns = _filter_campaigns(repository.campaigns(), params)
    period, previous, rows, _, _ = _assemble(repository, params, campaigns)

    statuses = _multi(params, 'status')
    if statuses:
        wanted = {s.lower() for s in statuses}
        rows = [r for r in rows if (r['status'] or '') in wanted]

    if params.get('flagged') in ('true', '1'):
        rows = [r for r in rows if r['open_flags'] > 0]

    ordering = params.get('ordering') or 'name'
    reverse = ordering.startswith('-')
    key = ORDERING.get(ordering.lstrip('-'))
    if key:
        rows.sort(key=key, reverse=reverse)

    return {
        'period': period.as_dict(),
        'comparison_period': previous.as_dict(),
        'count': len(rows),
        'results': rows,
    }


def campaign_detail(platform, campaign_id, params):
    repository = get_repository()
    campaigns = [
        c for c in repository.campaigns()
        if c['campaign_id'] == campaign_id and c['platform'] == platform
    ]
    if not campaigns:
        return None

    period, previous, rows, current_rows, _ = _assemble(repository, params, campaigns)
    payload = rows[0]
    campaign = campaigns[0]
    weeks = iso_weeks(period, settings.REPORTING['WEEKS_IN_TREND'])
    weekly_rows = repository.performance(weeks[0][0], weeks[-1][1], [campaign_id])

    payload['period'] = period.as_dict()
    payload['comparison_period'] = previous.as_dict()
    payload['ad_account_id'] = campaign.get('ad_account_id')
    payload['start_date'] = campaign.get('start_date')
    payload['end_date'] = campaign.get('end_date')
    payload['budget_amount'] = campaign.get('budget_amount')
    payload['budget_period'] = campaign.get('budget_period')
    payload['platform_status'] = campaign.get('platform_status')
    payload['synced_at'] = campaign.get('synced_at')
    payload['creatives'] = _creatives_by_campaign(repository, [campaign_id])[campaign_id]
    payload['weekly_trend'] = weekly_series(campaign['primary_kpi'], weekly_rows, weeks)
    payload['daily_trend'] = daily_series(campaign['primary_kpi'], current_rows)
    return payload


def overview(params):
    repository = get_repository()
    campaigns = _filter_campaigns(repository.campaigns(), params)
    period, previous, rows, current_rows, prior_rows = _assemble(
        repository, params, campaigns, include_series=False, include_creatives=False
    )

    current = totals(current_rows)
    prior = totals(prior_rows)
    by_campaign = {r['campaign_id']: r for r in rows}

    status_counts = {s: 0 for s in TrackingStatus.values}
    for row in rows:
        if row['status']:
            status_counts[row['status']] += 1

    funnel_totals = defaultdict(list)
    platform_totals = defaultdict(list)
    category_totals = defaultdict(list)
    campaign_meta = {c['campaign_id']: c for c in campaigns}
    for row in current_rows:
        meta = campaign_meta[row['campaign_id']]
        funnel_totals[meta['funnel_stage']].append(row)
        platform_totals[meta['platform']].append(row)
        category_totals[meta['product_category']].append(row)

    cpl_rows = [r for r in current_rows if campaign_meta[r['campaign_id']]['primary_kpi'] == Kpi.CPL]
    cpl_prior = [r for r in prior_rows if campaign_meta[r['campaign_id']]['primary_kpi'] == Kpi.CPL]
    cpl_totals = totals(cpl_rows)
    cpl_prior_totals = totals(cpl_prior)

    upper = totals(funnel_totals.get('upper', []))
    lower = totals(funnel_totals.get('lower', []))
    total_spend = current['spend']

    weeks = iso_weeks(period, settings.REPORTING['WEEKS_IN_TREND'])
    weekly_rows = repository.performance(weeks[0][0], weeks[-1][1], list(campaign_meta))
    weekly_by_platform = []
    for index, (start, end) in enumerate(weeks, start=1):
        bucket = [r for r in weekly_rows if start <= _date(r['date']) <= end]
        entry = {
            'label': f'W{index}',
            'week_start': start.isoformat(),
            'week_end': end.isoformat(),
            'is_current': start <= period.end <= end,
            'total': _round(totals(bucket)['spend'], 2),
        }
        for platform in Platform.values:
            platform_rows = [r for r in bucket if r['platform'] == platform]
            entry[platform] = _round(totals(platform_rows)['spend'], 2)
        weekly_by_platform.append(entry)

    return {
        'period': period.as_dict(),
        'comparison_period': previous.as_dict(),
        'currencies': sorted({c['currency'] for c in campaigns if c.get('currency')}),
        'tiles': {
            'active_campaigns': len(campaigns),
            'total_spend': {
                'value': _round(total_spend, 2),
                'previous_value': _round(prior['spend'], 2),
                'change_pct': _round(change_pct(total_spend, prior['spend'])),
            },
            'upper_funnel_spend': {
                'value': _round(upper['spend'], 2),
                'share_pct': _round(upper['spend'] / total_spend * 100 if total_spend else None),
            },
            'lower_funnel_spend': {
                'value': _round(lower['spend'], 2),
                'share_pct': _round(lower['spend'] / total_spend * 100 if total_spend else None),
            },
            'avg_cpl': kpi_block(Kpi.CPL, cpl_totals, cpl_prior_totals),
            'performance': {
                'on_track': status_counts[TrackingStatus.ON_TRACK],
                'at_risk': status_counts[TrackingStatus.AT_RISK],
                'off_track': status_counts[TrackingStatus.OFF_TRACK],
                'total': len(rows),
            },
        },
        'funnel_stage_performance': [
            _breakdown('funnel_stage', stage, stage_rows, campaign_meta, by_campaign, total_spend)
            for stage, stage_rows in sorted(funnel_totals.items())
        ],
        'spend_by_platform': [
            _breakdown('platform', platform, platform_rows, campaign_meta, by_campaign, total_spend)
            for platform, platform_rows in sorted(platform_totals.items())
        ],
        'spend_by_category': [
            _breakdown('product_category', category, category_rows, campaign_meta, by_campaign,
                       total_spend)
            for category, category_rows in sorted(category_totals.items())
        ],
        'spend_and_conversions': sorted(
            [
                {
                    'platform': meta['platform'],
                    'market': meta['market'],
                    'campaign_id': campaign_id,
                    'campaign_name': meta['campaign_name'],
                    'spend': by_campaign[campaign_id]['spend'],
                    'conversions': _round(
                        totals([r for r in current_rows if r['campaign_id'] == campaign_id])
                        ['conversions'], 2
                    ),
                }
                for campaign_id, meta in campaign_meta.items()
            ],
            key=lambda r: -(r['spend'] or 0),
        ),
        'weekly_spend_by_platform': weekly_by_platform,
    }


def _date(value):
    from analytics.aggregation import _as_date

    return _as_date(value)


def _breakdown(dimension, key, rows, campaign_meta, by_campaign, total_spend):
    bucket = totals(rows)
    campaign_ids = {r['campaign_id'] for r in rows}
    statuses = [by_campaign[c]['status'] for c in campaign_ids if by_campaign[c]['status']]
    return {
        'dimension': dimension,
        'key': key,
        'spend': _round(bucket['spend'], 2),
        'share_pct': _round(bucket['spend'] / total_spend * 100 if total_spend else None),
        'impressions': int(bucket['impressions']),
        'reach': int(bucket['reach']),
        'clicks': int(bucket['clicks']),
        'conversions': _round(bucket['conversions'], 2),
        'cpl': _round(compute_kpi(Kpi.CPL, bucket), 4),
        'campaign_count': len(campaign_ids),
        'on_track': statuses.count(TrackingStatus.ON_TRACK),
        'at_risk': statuses.count(TrackingStatus.AT_RISK),
        'off_track': statuses.count(TrackingStatus.OFF_TRACK),
    }


def filter_options(params):
    repository = get_repository()
    campaigns = repository.campaigns()
    period, _, rows, _, _ = _assemble(
        repository, params, campaigns, include_series=False, include_creatives=False
    )
    status_by_id = {r['campaign_id']: r['status'] for r in rows}

    def counts(field):
        bucket = defaultdict(int)
        for campaign in campaigns:
            bucket[campaign[field]] += 1
        return [{'key': k, 'count': v} for k, v in sorted(bucket.items())]

    status_counts = defaultdict(int)
    for status in status_by_id.values():
        if status:
            status_counts[status] += 1

    return {
        'period': period.as_dict(),
        'total': len(campaigns),
        'markets': counts('market'),
        'platforms': counts('platform'),
        'funnel_stages': counts('funnel_stage'),
        'categories': counts('product_category'),
        'primary_kpis': counts('primary_kpi'),
        'statuses': [
            {'key': s, 'label': TrackingStatus(s).label, 'count': status_counts.get(s, 0)}
            for s in TrackingStatus.values
        ],
    }
