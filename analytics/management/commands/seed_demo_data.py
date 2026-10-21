import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analytics.metrics import KPI_DIRECTION, compute_kpi, evaluate_status, target_for_status
from analytics.seed import build_all
from campaigns.models import CampaignTarget

TABLES = ('campaigns', 'campaign_performance_daily', 'campaign_creatives')


class Command(BaseCommand):
    help = 'Generate demo analytics data, write it as NDJSON, and create matching KPI targets.'

    def add_arguments(self, parser):
        parser.add_argument('--as-of', default=None)
        parser.add_argument('--days', type=int, default=180)
        parser.add_argument('--window', type=int, default=28)
        parser.add_argument('--out', default='seed_data')
        parser.add_argument('--load-bq', action='store_true')
        parser.add_argument('--skip-targets', action='store_true')

    def handle(self, *args, **options):
        as_of = date.fromisoformat(options['as_of']) if options['as_of'] else date.today()
        data = build_all(as_of=as_of, days=options['days'])

        out_dir = Path(options['out'])
        out_dir.mkdir(parents=True, exist_ok=True)
        for table in TABLES:
            path = out_dir / f'{table}.ndjson'
            with path.open('w', encoding='utf8') as handle:
                for row in data[table]:
                    handle.write(json.dumps(row, ensure_ascii=False) + '\n')
            self.stdout.write(self.style.SUCCESS(f'{path} ({len(data[table])} rows)'))

        if not options['skip_targets']:
            created = self.write_targets(data, as_of, options['window'])
            self.stdout.write(self.style.SUCCESS(f'targets written to postgres: {created}'))

        if options['load_bq']:
            self.load_bigquery(data)

    def write_targets(self, data, as_of, window):
        start = as_of - timedelta(days=window - 1)
        totals = defaultdict(lambda: defaultdict(float))
        for row in data['campaign_performance_daily']:
            if date.fromisoformat(row['date']) < start:
                continue
            bucket = totals[row['campaign_id']]
            for field in ('impressions', 'clicks', 'reach', 'video_views', 'conversions', 'spend'):
                bucket[field] += row[field] or 0

        from analytics.catalogue import iter_campaigns

        expected = {e['campaign_id']: e for e in iter_campaigns()}
        rows = []
        for campaign in data['campaigns']:
            entry = expected[campaign['campaign_id']]
            kpi = campaign['primary_kpi']
            value = compute_kpi(kpi, totals[campaign['campaign_id']])
            target = target_for_status(kpi, value, entry['expected_status'])
            if target is None:
                continue
            rows.append(CampaignTarget(
                platform=campaign['platform'],
                campaign_id=campaign['campaign_id'],
                kpi=kpi,
                target_value=Decimal(str(round(target, 4))),
                currency=campaign['currency'],
                direction=KPI_DIRECTION[kpi],
                is_primary=True,
            ))

        with transaction.atomic():
            CampaignTarget.objects.filter(is_primary=True).delete()
            CampaignTarget.objects.bulk_create(rows)

        statuses = defaultdict(int)
        for target in rows:
            value = compute_kpi(target.kpi, totals[target.campaign_id])
            statuses[evaluate_status(target.kpi, value, float(target.target_value))] += 1
        self.stdout.write(f'  status distribution: {dict(statuses)}')
        return len(rows)

    def load_bigquery(self, data):
        conf = settings.BIGQUERY
        if not conf.get('PROJECT') or not conf.get('DATASET'):
            raise CommandError('BIGQUERY_PROJECT and BIGQUERY_DATASET must be set.')

        from google.cloud import bigquery

        from core.bigquery import get_client

        client = get_client()
        for table in TABLES:
            table_id = f"{conf['PROJECT']}.{conf['DATASET']}.{table}"
            job = client.load_table_from_json(
                data[table],
                table_id,
                job_config=bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                ),
            )
            job.result()
            self.stdout.write(self.style.SUCCESS(f'loaded {table_id} ({len(data[table])} rows)'))
