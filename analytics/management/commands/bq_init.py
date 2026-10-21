from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

SCHEMA_DIR = Path(__file__).resolve().parents[2] / 'schema'

TABLES = ('campaigns', 'campaign_performance_daily', 'campaign_creatives')


class Command(BaseCommand):
    help = 'Create the BigQuery dataset and analytics tables.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        conf = settings.BIGQUERY
        if not options['dry_run'] and (not conf.get('PROJECT') or not conf.get('DATASET')):
            raise CommandError('BIGQUERY_PROJECT and BIGQUERY_DATASET must be set.')

        project = conf.get('PROJECT') or 'PROJECT'
        dataset_name = conf.get('DATASET') or 'DATASET'
        dataset = f'{project}.{dataset_name}'
        statements = []
        for table in TABLES:
            sql = (SCHEMA_DIR / f'{table}.sql').read_text()
            statements.append((table, sql.format(dataset=dataset)))

        if options['dry_run']:
            for table, sql in statements:
                self.stdout.write(self.style.MIGRATE_HEADING(table))
                self.stdout.write(sql)
            return

        from google.cloud import bigquery

        from core.bigquery import get_client

        client = get_client()
        client.create_dataset(
            bigquery.Dataset(f"{conf['PROJECT']}.{conf['DATASET']}"), exists_ok=True
        )
        self.stdout.write(self.style.SUCCESS(f"dataset ready: {conf['DATASET']}"))

        for table, sql in statements:
            client.query(sql).result()
            self.stdout.write(self.style.SUCCESS(f'table ready: {table}'))
