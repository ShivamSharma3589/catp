from functools import lru_cache

from django.conf import settings
from google.cloud import bigquery
from google.oauth2 import service_account


@lru_cache(maxsize=1)
def get_client():
    conf = settings.BIGQUERY
    credentials = None
    if conf.get('CREDENTIALS_FILE'):
        credentials = service_account.Credentials.from_service_account_file(
            conf['CREDENTIALS_FILE'],
            scopes=['https://www.googleapis.com/auth/bigquery.readonly'],
        )
    return bigquery.Client(
        project=conf.get('PROJECT'),
        credentials=credentials,
        location=conf.get('LOCATION'),
    )


def table(name):
    conf = settings.BIGQUERY
    return f"`{conf['PROJECT']}.{conf['DATASET']}.{name}`"


def run_query(sql, params=None, dry_run=False):
    conf = settings.BIGQUERY
    job_config = bigquery.QueryJobConfig(
        query_parameters=_to_query_parameters(params or {}),
        maximum_bytes_billed=conf['MAX_BYTES_BILLED'],
        use_query_cache=True,
        dry_run=dry_run,
    )
    job = get_client().query(sql, job_config=job_config)
    if dry_run:
        return {'bytes_processed': job.total_bytes_processed}
    return [dict(row) for row in job.result()]


_SCALAR_TYPES = {
    bool: 'BOOL',
    int: 'INT64',
    float: 'FLOAT64',
    str: 'STRING',
}


def _to_query_parameters(params):
    out = []
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            element = value[0] if value else ''
            out.append(bigquery.ArrayQueryParameter(key, _bq_type(element), list(value)))
        else:
            out.append(bigquery.ScalarQueryParameter(key, _bq_type(value), value))
    return out


def _bq_type(value):
    from datetime import date, datetime

    if isinstance(value, datetime):
        return 'TIMESTAMP'
    if isinstance(value, date):
        return 'DATE'
    return _SCALAR_TYPES.get(type(value), 'STRING')
