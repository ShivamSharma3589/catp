BLUEPRINTS = [
    {
        'key': 'search-brand', 'platform': 'google', 'name': 'Search - Brand',
        'funnel_stage': 'lower', 'product_category': 'Brand', 'primary_kpi': 'cpl',
        'campaign_type': 'SEARCH', 'objective': 'leads', 'ad_format': 'Text',
        'spend_28d': 15300, 'cpc': 0.21, 'ctr': 0.025, 'cvr': 0.040,
    },
    {
        'key': 'search-generic', 'platform': 'google', 'name': 'Search - Generic',
        'funnel_stage': 'lower', 'product_category': 'Mini Excavators', 'primary_kpi': 'cpl',
        'campaign_type': 'SEARCH', 'objective': 'leads', 'ad_format': 'Text',
        'spend_28d': 27100, 'cpc': 0.32, 'ctr': 0.021, 'cvr': 0.050,
    },
    {
        'key': 'performance-max', 'platform': 'google', 'name': 'Performance Max',
        'funnel_stage': 'full', 'product_category': 'Multi-Product', 'primary_kpi': 'cpl',
        'campaign_type': 'PERFORMANCE_MAX', 'objective': 'leads',
        'ad_format': 'Text, Display, Video',
        'spend_28d': 47700, 'cpc': 0.28, 'ctr': 0.018, 'cvr': 0.050,
    },
    {
        'key': 'demand-gen-traffic', 'platform': 'google', 'name': 'Demand Gen - Traffic',
        'funnel_stage': 'mid', 'product_category': 'Compact Wheel Loaders',
        'primary_kpi': 'clicks',
        'campaign_type': 'DEMAND_GEN', 'objective': 'traffic', 'ad_format': 'Display, Video',
        'spend_28d': 19600, 'cpc': 0.205, 'ctr': 0.012, 'cvr': 0.010,
    },
    {
        'key': 'demand-gen-conv', 'platform': 'google', 'name': 'Demand Gen - Conv.',
        'funnel_stage': 'lower', 'product_category': 'Mini Excavators', 'primary_kpi': 'cpl',
        'campaign_type': 'DEMAND_GEN', 'objective': 'leads', 'ad_format': 'Display, Video',
        'spend_28d': 20700, 'cpc': 0.225, 'ctr': 0.013, 'cvr': 0.040,
    },
    {
        'key': 'masthead', 'platform': 'youtube', 'name': 'Masthead',
        'funnel_stage': 'upper', 'product_category': 'Brand', 'primary_kpi': 'reach',
        'campaign_type': 'VIDEO', 'objective': 'awareness', 'ad_format': 'Homepage Takeover',
        'spend_28d': 82200, 'cpc': 1.60, 'ctr': 0.0022, 'cvr': 0.004,
    },
    {
        'key': 'video-views', 'platform': 'youtube', 'name': 'Video Views',
        'funnel_stage': 'lower', 'product_category': 'Mini Excavators', 'primary_kpi': 'views',
        'campaign_type': 'VIDEO', 'objective': 'views', 'ad_format': 'In-Stream (Skippable)',
        'spend_28d': 27000, 'cpc': 0.30, 'ctr': 0.009, 'cvr': 0.012,
    },
    {
        'key': 'awareness-bumper', 'platform': 'youtube', 'name': 'Awareness - Bumper',
        'funnel_stage': 'upper', 'product_category': 'Compact Wheel Loaders',
        'primary_kpi': 'impressions',
        'campaign_type': 'VIDEO', 'objective': 'awareness', 'ad_format': '6s Unskippable',
        'spend_28d': 28600, 'cpc': 1.10, 'ctr': 0.0042, 'cvr': 0.003,
    },
    {
        'key': 'youtube-shorts', 'platform': 'youtube', 'name': 'YouTube Shorts',
        'funnel_stage': 'mid', 'product_category': 'Compact Wheel Loaders',
        'primary_kpi': 'impressions',
        'campaign_type': 'VIDEO', 'objective': 'awareness', 'ad_format': 'Vertical Video',
        'spend_28d': 9000, 'cpc': 0.52, 'ctr': 0.0088, 'cvr': 0.004,
    },
    {
        'key': 'awareness-reels', 'platform': 'meta', 'name': 'Awareness - Reels',
        'funnel_stage': 'upper', 'product_category': 'Mini Excavators', 'primary_kpi': 'cpm',
        'campaign_type': 'OUTCOME_AWARENESS', 'objective': 'awareness',
        'ad_format': 'Vertical Video',
        'spend_28d': 24500, 'cpc': 0.34, 'ctr': 0.0144, 'cvr': 0.006,
    },
    {
        'key': 'lead-gen-forms', 'platform': 'meta', 'name': 'Lead Gen - Forms',
        'funnel_stage': 'lower', 'product_category': 'Mini Excavators', 'primary_kpi': 'cpl',
        'campaign_type': 'OUTCOME_LEADS', 'objective': 'leads', 'ad_format': 'Image / Carousel',
        'spend_28d': 30900, 'cpc': 0.37, 'ctr': 0.016, 'cvr': 0.0625,
    },
    {
        'key': 'moments-brand', 'platform': 'meta', 'name': 'Moments - Brand',
        'funnel_stage': 'upper', 'product_category': 'Brand', 'primary_kpi': 'reach',
        'campaign_type': 'OUTCOME_AWARENESS', 'objective': 'awareness', 'ad_format': 'Video',
        'spend_28d': 18700, 'cpc': 0.42, 'ctr': 0.0105, 'cvr': 0.005,
    },
    {
        'key': 'thought-leader-ads', 'platform': 'linkedin', 'name': 'Thought Leader Ads',
        'funnel_stage': 'mid', 'product_category': 'Brand', 'primary_kpi': 'clicks',
        'campaign_type': 'SPONSORED_UPDATES', 'objective': 'engagement',
        'ad_format': 'Sponsored Post',
        'spend_28d': 18200, 'cpc': 0.207, 'ctr': 0.0095, 'cvr': 0.008,
    },
    {
        'key': 'lead-gen-document', 'platform': 'linkedin', 'name': 'Lead Gen - Document',
        'funnel_stage': 'lower', 'product_category': 'Mini Excavators', 'primary_kpi': 'cpl',
        'campaign_type': 'SPONSORED_UPDATES', 'objective': 'leads',
        'ad_format': 'Document Ad (PDF/PPT)',
        'spend_28d': 25500, 'cpc': 0.46, 'ctr': 0.0068, 'cvr': 0.0775,
    },
    {
        'key': 'video-brand', 'platform': 'linkedin', 'name': 'Video - Brand',
        'funnel_stage': 'upper', 'product_category': 'Compact Wheel Loaders',
        'primary_kpi': 'cpv',
        'campaign_type': 'SPONSORED_UPDATES', 'objective': 'awareness', 'ad_format': 'Single Video',
        'spend_28d': 30700, 'cpc': 0.85, 'ctr': 0.0055, 'cvr': 0.006,
    },
    {
        'key': 'lead-gen-form', 'platform': 'linkedin', 'name': 'Lead Gen Form',
        'funnel_stage': 'lower', 'product_category': 'Multi-Product', 'primary_kpi': 'cpl',
        'campaign_type': 'SPONSORED_UPDATES', 'objective': 'leads', 'ad_format': 'Image / Carousel',
        'spend_28d': 28400, 'cpc': 0.49, 'ctr': 0.0062, 'cvr': 0.0835,
    },
]

MARKETS = ('IT', 'FR', 'UK', 'DE')

MARKET_CURRENCY = {'IT': 'EUR', 'FR': 'EUR', 'DE': 'EUR', 'UK': 'GBP'}

MARKET_SPEND_INDEX = {'IT': 1.00, 'FR': 0.92, 'UK': 0.78, 'DE': 1.08}

AT_RISK = {
    ('DE', 'awareness-bumper'),
    ('DE', 'youtube-shorts'),
    ('UK', 'demand-gen-traffic'),
}

OFF_TRACK = {
    ('IT', 'awareness-bumper'),
    ('IT', 'youtube-shorts'),
    ('IT', 'moments-brand'),
    ('FR', 'awareness-bumper'),
    ('FR', 'youtube-shorts'),
    ('FR', 'moments-brand'),
    ('UK', 'video-views'),
    ('UK', 'awareness-bumper'),
    ('UK', 'youtube-shorts'),
    ('UK', 'moments-brand'),
}

MARKET_ACCOUNT_SUFFIX = {'IT': '390', 'FR': '331', 'UK': '441', 'DE': '490'}


def ad_account_id(platform, market):
    suffix = MARKET_ACCOUNT_SUFFIX[market]
    if platform == 'linkedin':
        return f'urn:li:sponsoredAccount:5094{suffix}21'
    if platform == 'meta':
        return f'act_18{suffix}04477'
    return f'742-915-{suffix}'


def native_campaign_id(platform, market, index):
    base = f'{MARKET_ACCOUNT_SUFFIX[market]}{index:03d}'
    if platform == 'linkedin':
        return f'urn:li:sponsoredCampaign:{base}'
    if platform == 'meta':
        return f'23851{base}0477'
    return f'2{base}9174'


def tracking_status(market, blueprint_key):
    if (market, blueprint_key) in OFF_TRACK:
        return 'off_track'
    if (market, blueprint_key) in AT_RISK:
        return 'at_risk'
    return 'on_track'


def iter_campaigns():
    index = 0
    for market in MARKETS:
        for blueprint in BLUEPRINTS:
            index += 1
            yield {
                'market': market,
                'blueprint': blueprint,
                'campaign_id': native_campaign_id(blueprint['platform'], market, index),
                'ad_account_id': ad_account_id(blueprint['platform'], market),
                'expected_status': tracking_status(market, blueprint['key']),
            }
