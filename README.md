# CAT Dealer Snapshot — Backend

Django + DRF API for the CAT Dealer Snapshot dashboard (React + TypeScript frontend).

- Campaign, performance and creative data: **BigQuery**
- Users, KPI targets, notes, flags: **PostgreSQL**
- Auth: **Google ID token only**, exchanged for JWT

Docs: [docs/DATA_MODEL.md](docs/DATA_MODEL.md) · [docs/API.md](docs/API.md) · `docs/postman_collection.json`

## Setup

```
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env`: Postgres credentials, `GOOGLE_OAUTH_CLIENT_ID`, and the `BIGQUERY_*` variables when you have them.

```
python manage.py migrate
python manage.py seed_demo_data --as-of 2026-10-20
python manage.py runserver
```

The API is then on `http://127.0.0.1:8000/api/`.

## Data backends

`ANALYTICS_BACKEND=local` (default) serves the whole API from the generated NDJSON in `seed_data/` — no BigQuery access needed. Switch to `ANALYTICS_BACKEND=bigquery` once credentials are in place; response shapes are identical.

To create the BigQuery tables and load the same data:

```
python manage.py bq_init
python manage.py seed_demo_data --as-of 2026-10-20 --load-bq
```

`bq_init --dry-run` prints the DDL without connecting.

## Testing in Postman

Import `docs/postman_collection.json`, set `baseUrl`, run **Dev token** — the JWT is stored and reused by every other request.

`/api/auth/dev-token/` issues a token for any email without Google. It returns 404 unless `DEBUG=True` **and** `ALLOW_DEV_TOKEN=True`, so keep `ALLOW_DEV_TOKEN=False` anywhere deployed.
