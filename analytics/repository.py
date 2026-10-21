import json
from datetime import date
from functools import lru_cache

from django.conf import settings

CAMPAIGN_FIELDS = (
    'platform', 'market', 'ad_account_id', 'campaign_id', 'campaign_name', 'campaign_type',
    'objective', 'funnel_stage', 'product_category', 'ad_format', 'primary_kpi',
    'platform_status', 'effective_status', 'start_date', 'end_date', 'budget_amount',
    'budget_period', 'currency', 'synced_at',
)

PERFORMANCE_FIELDS = (
    'platform', 'market', 'campaign_id', 'date', 'impressions', 'reach', 'clicks',
    'video_views', 'video_completions', 'conversions', 'conversion_value', 'spend', 'currency',
)

CREATIVE_FIELDS = (
    'platform', 'market', 'campaign_id', 'ad_id', 'creative_id', 'creative_name', 'format',
    'position', 'headline', 'primary_text', 'description', 'call_to_action', 'display_url',
    'landing_page_url', 'image_url', 'video_id', 'thumbnail_url', 'creative_reference',
    'is_serving', 'effective_status',
)


def _as_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class LocalRepository:
    def _load(self, table):
        path = settings.SEED_DATA_DIR / f'{table}.ndjson'
        if not path.exists():
            return []
        return _read_ndjson(str(path), path.stat().st_mtime_ns)

    def campaigns(self):
        return self._load('campaigns')

    def creatives(self, campaign_ids=None):
        rows = self._load('campaign_creatives')
        if campaign_ids is None:
            return rows
        wanted = set(campaign_ids)
        return [r for r in rows if r['campaign_id'] in wanted]

    def performance(self, start, end, campaign_ids=None):
        wanted = set(campaign_ids) if campaign_ids is not None else None
        rows = []
        for row in self._load('campaign_performance_daily'):
            day = _as_date(row['date'])
            if day < start or day > end:
                continue
            if wanted is not None and row['campaign_id'] not in wanted:
                continue
            rows.append(row)
        return rows

    def data_end_date(self):
        rows = self._load('campaign_performance_daily')
        if not rows:
            return None
        return max(_as_date(r['date']) for r in rows)


class BigQueryRepository:
    def _table(self, name):
        from core.bigquery import table

        return table(name)

    def campaigns(self):
        from core.bigquery import run_query

        columns = ', '.join(CAMPAIGN_FIELDS)
        return run_query(f'SELECT {columns} FROM {self._table("campaigns")}')

    def creatives(self, campaign_ids=None):
        from core.bigquery import run_query

        columns = ', '.join(CREATIVE_FIELDS)
        sql = f'SELECT {columns} FROM {self._table("campaign_creatives")}'
        params = {}
        if campaign_ids is not None:
            sql += ' WHERE campaign_id IN UNNEST(@campaign_ids)'
            params['campaign_ids'] = list(campaign_ids)
        sql += ' ORDER BY campaign_id, position'
        return run_query(sql, params)

    def performance(self, start, end, campaign_ids=None):
        from core.bigquery import run_query

        columns = ', '.join(PERFORMANCE_FIELDS)
        sql = (
            f'SELECT {columns} FROM {self._table("campaign_performance_daily")} '
            'WHERE date BETWEEN @start AND @end'
        )
        params = {'start': start, 'end': end}
        if campaign_ids is not None:
            sql += ' AND campaign_id IN UNNEST(@campaign_ids)'
            params['campaign_ids'] = list(campaign_ids)
        return run_query(sql, params)

    def data_end_date(self):
        from core.bigquery import run_query

        rows = run_query(
            f'SELECT MAX(date) AS max_date FROM {self._table("campaign_performance_daily")}'
        )
        value = rows[0]['max_date'] if rows else None
        return _as_date(value) if value else None


@lru_cache(maxsize=8)
def _read_ndjson(path, _mtime):
    with open(path, encoding='utf8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def get_repository():
    if settings.ANALYTICS_BACKEND == 'bigquery':
        return BigQueryRepository()
    return LocalRepository()
