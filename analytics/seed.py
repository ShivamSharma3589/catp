import random
from datetime import date, datetime, timedelta, timezone

from .catalogue import (
    MARKET_CURRENCY,
    MARKET_SPEND_INDEX,
    iter_campaigns,
)

LANGUAGE = {'IT': 'it', 'FR': 'fr', 'UK': 'en', 'DE': 'de'}

CATEGORY_LABEL = {
    'it': {
        'Brand': 'Cat®', 'Mini Excavators': 'Mini Escavatori',
        'Compact Wheel Loaders': 'Pale Compatte', 'Multi-Product': 'Gamma Completa',
    },
    'fr': {
        'Brand': 'Cat®', 'Mini Excavators': 'Mini Pelles',
        'Compact Wheel Loaders': 'Chargeuses Compactes', 'Multi-Product': 'Gamme Complete',
    },
    'en': {
        'Brand': 'Cat®', 'Mini Excavators': 'Mini Excavators',
        'Compact Wheel Loaders': 'Compact Wheel Loaders', 'Multi-Product': 'Full Product Range',
    },
    'de': {
        'Brand': 'Cat®', 'Mini Excavators': 'Minibagger',
        'Compact Wheel Loaders': 'Kompaktradlader', 'Multi-Product': 'Produktpalette',
    },
}

HEADLINE = {
    'it': '{creative} · {category} Nuovi e Usati - Richiedi una Demo Gratuita',
    'fr': '{creative} · {category} Neuf et Occasion - Demandez une Demo Gratuite',
    'en': '{creative} · New & Used {category} - Request a Free Demo Today',
    'de': '{creative} · Neu- und Gebrauchtmaschinen - Jetzt Demo anfordern',
}

BODY = {
    'it': 'Scopri la gamma {category} Cat®. Soluzioni di finanziamento flessibili e '
          'assistenza esperta in tutta Italia.',
    'fr': 'Decouvrez la gamme {category} Cat®. Financement flexible et service expert '
          'partout en France.',
    'en': 'Discover the Cat® {category} range. Flexible finance options and expert '
          'service across the UK.',
    'de': 'Entdecken Sie das komplette Cat® {category}-Programm. Flexible '
          'Finanzierungsoptionen und Expertenservice.',
}

CTA = {'it': 'Richiedi Demo', 'fr': 'Demander une Demo', 'en': 'Request Demo', 'de': 'Demo anfordern'}

DISPLAY_URL = {
    'it': 'cat.com/macchine/it', 'fr': 'cat.com/materiel/fr',
    'en': 'cat.com/equipment/uk', 'de': 'cat.com/maschinen/de',
}

CREATIVE_NAMES = {
    'search-brand': ('Finance Offer v1', 'Finance Offer v2'),
    'search-generic': ('Generic Broad v1', 'Generic Broad v2'),
    'performance-max': ('Asset Group - Mini Ex', 'Asset Group - Loaders'),
    'demand-gen-traffic': ('Display Banner v1', 'Display Banner v2'),
    'demand-gen-conv': ('Finance Display v1', 'Finance Display v2'),
    'masthead': ('Masthead Takeover', 'Masthead Takeover B'),
    'video-views': ('Mini Ex Walkaround', 'Mini Ex Jobsite'),
    'awareness-bumper': ('Bumper 6s Loader', 'Bumper 6s Brand'),
    'youtube-shorts': ('Shorts Vertical v1', 'Shorts Vertical v2'),
    'awareness-reels': ('Reels Minibagger', 'Reels Jobsite'),
    'lead-gen-forms': ('Instant Form - Finance', 'Instant Form - Demo'),
    'moments-brand': ('Finance Moment v1', 'Finance Moment v2'),
    'thought-leader-ads': ('TL Post - Mini Ex', 'TL Post - Loaders'),
    'lead-gen-document': ('Product Guide 2026 PDF', 'Spec Sheet PDF'),
    'video-brand': ('Cat 920 - Brand Video', 'Cat 920 - Demo Video'),
    'lead-gen-form': ('Finance Image - Mini Ex', 'Finance Image - Range'),
}

VIDEO_FORMATS = (
    'Homepage Takeover', 'In-Stream (Skippable)', '6s Unskippable', 'Vertical Video',
    'Video', 'Single Video',
)

WEEKDAY_FACTOR = (1.08, 1.10, 1.06, 1.02, 0.92, 0.78, 0.74)


def _rng(*parts):
    return random.Random('|'.join(str(p) for p in parts))


def _is_video(blueprint):
    return blueprint['ad_format'] in VIDEO_FORMATS or 'Video' in blueprint['ad_format']


def _trend_factor(status, day_index, total_days):
    progress = day_index / max(total_days - 1, 1)
    if status == 'off_track':
        return 0.82 + 0.46 * progress
    if status == 'at_risk':
        return 0.90 + 0.24 * progress
    return 1.16 - 0.28 * progress


def build_campaign_rows(as_of, synced_at):
    rows = []
    for entry in iter_campaigns():
        blueprint = entry['blueprint']
        market = entry['market']
        rng = _rng(market, blueprint['key'], 'campaign')
        daily_budget = round(blueprint['spend_28d'] * MARKET_SPEND_INDEX[market] / 28 * 1.15, 2)
        rows.append({
            'platform': blueprint['platform'],
            'market': market,
            'ad_account_id': entry['ad_account_id'],
            'campaign_id': entry['campaign_id'],
            'campaign_name': blueprint['name'],
            'campaign_type': blueprint['campaign_type'],
            'campaign_type_raw': blueprint['campaign_type'],
            'objective': blueprint['objective'],
            'objective_raw': blueprint['campaign_type'],
            'funnel_stage': blueprint['funnel_stage'],
            'product_category': blueprint['product_category'],
            'ad_format': blueprint['ad_format'],
            'primary_kpi': blueprint['primary_kpi'],
            'platform_status': 'active',
            'platform_status_raw': 'ENABLED' if blueprint['platform'] in ('google', 'youtube') else 'ACTIVE',
            'effective_status': 'SERVING',
            'start_date': (as_of - timedelta(days=rng.randint(150, 210))).isoformat(),
            'end_date': (as_of + timedelta(days=rng.randint(30, 120))).isoformat(),
            'budget_amount': daily_budget,
            'budget_period': 'daily',
            'currency': MARKET_CURRENCY[market],
            'source_updated_at': (synced_at - timedelta(hours=rng.randint(2, 70))).isoformat(),
            'synced_at': synced_at.isoformat(),
        })
    return rows


def build_performance_rows(as_of, synced_at, days=180):
    rows = []
    for entry in iter_campaigns():
        blueprint = entry['blueprint']
        market = entry['market']
        status = entry['expected_status']
        rng = _rng(market, blueprint['key'], 'performance')
        base_daily_spend = blueprint['spend_28d'] * MARKET_SPEND_INDEX[market] / 28
        video = _is_video(blueprint)

        for day_index in range(days):
            day = as_of - timedelta(days=days - 1 - day_index)
            factor = (
                WEEKDAY_FACTOR[day.weekday()]
                * _trend_factor(status, day_index, days)
                * rng.uniform(0.88, 1.12)
            )
            spend = base_daily_spend * factor
            efficiency = _trend_factor(status, day_index, days)
            clicks = spend / (blueprint['cpc'] * efficiency)
            impressions = clicks / blueprint['ctr']
            conversions = clicks * blueprint['cvr'] / efficiency
            rows.append({
                'platform': blueprint['platform'],
                'market': market,
                'campaign_id': entry['campaign_id'],
                'date': day.isoformat(),
                'impressions': int(impressions),
                'reach': int(impressions * rng.uniform(0.48, 0.62)),
                'clicks': int(clicks),
                'video_views': int(impressions * rng.uniform(0.30, 0.42)) if video else None,
                'video_completions': int(impressions * rng.uniform(0.10, 0.18)) if video else None,
                'conversions': round(conversions, 2),
                'conversion_value': round(conversions * rng.uniform(820, 1450), 2),
                'spend': round(spend, 2),
                'currency': MARKET_CURRENCY[market],
                'attribution_setting': '7d_click_1d_view',
                'synced_at': synced_at.isoformat(),
            })
    return rows


def build_creative_rows(entry_synced_at):
    rows = []
    for entry in iter_campaigns():
        blueprint = entry['blueprint']
        market = entry['market']
        lang = LANGUAGE[market]
        category = CATEGORY_LABEL[lang][blueprint['product_category']]
        video = _is_video(blueprint)
        rng = _rng(market, blueprint['key'], 'creative')

        for position, creative_name in enumerate(CREATIVE_NAMES[blueprint['key']], start=1):
            suffix = f'{market.lower()}-{blueprint["key"]}-{position}'
            rows.append({
                'platform': blueprint['platform'],
                'market': market,
                'campaign_id': entry['campaign_id'],
                'ad_id': f'ad-{suffix}',
                'creative_id': (
                    f'urn:li:sponsoredCreative:{rng.randint(500000, 599999)}'
                    if blueprint['platform'] == 'linkedin'
                    else f'cr-{suffix}'
                ),
                'creative_name': creative_name,
                'format': blueprint['ad_format'],
                'position': position,
                'headline': HEADLINE[lang].format(creative=creative_name, category=category),
                'primary_text': BODY[lang].format(category=category),
                'description': f'{creative_name} - {category}',
                'call_to_action': CTA[lang],
                'display_url': DISPLAY_URL[lang],
                'landing_page_url': f'https://www.{DISPLAY_URL[lang]}/{blueprint["key"]}',
                'image_url': None if video else f'https://cdn.example.com/cat/{suffix}.jpg',
                'video_id': f'yt-{suffix}' if video else None,
                'thumbnail_url': f'https://cdn.example.com/cat/{suffix}-thumb.jpg',
                'creative_reference': (
                    f'urn:li:share:67780455551982{rng.randint(10000, 99999)}'
                    if blueprint['platform'] == 'linkedin'
                    else None
                ),
                'is_serving': True,
                'effective_status': 'ACTIVE',
                'creative_fetched_at': entry_synced_at.isoformat(),
            })
    return rows


def build_all(as_of=None, days=180):
    as_of = as_of or date.today()
    synced_at = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        'campaigns': build_campaign_rows(as_of, synced_at),
        'campaign_performance_daily': build_performance_rows(as_of, synced_at, days),
        'campaign_creatives': build_creative_rows(synced_at),
    }
