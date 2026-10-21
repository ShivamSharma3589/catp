# CAT Dealer Snapshot — API Reference

Base URL: `http://127.0.0.1:8000/api/`

All endpoints except the auth ones require `Authorization: Bearer <access token>`.
Responses are JSON only; there is no browsable API.

---

## 1. Auth

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/auth/google/` | `{"credential": "<Google ID token>"}` | `{user, tokens: {access, refresh}, created}` |
| POST | `/auth/refresh/` | `{"refresh": "..."}` | `{access, refresh}` (refresh rotates) |
| POST | `/auth/logout/` | `{"refresh": "..."}` | `204`, refresh token blacklisted |
| GET | `/auth/me/` | — | The current user |
| POST | `/auth/dev-token/` | `{"email": "you@example.com"}` | Same shape as Google login |

`credential` is the string React gets from Google Identity Services, verified server-side against `GOOGLE_OAUTH_CLIENT_ID`.

**`/auth/dev-token/` is for local testing only.** It issues a real JWT for any email, creating the user if needed, and returns `404` unless `DEBUG=True` **and** `ALLOW_DEV_TOKEN=True`. Use it to work in Postman without a Google token; never enable it anywhere deployed.

Errors: `401` invalid/expired credential, `503` `GOOGLE_OAUTH_CLIENT_ID` not configured, `403` account disabled.

---

## 2. Shared query parameters

Every reporting endpoint takes these.

| Parameter | Values | Default |
|---|---|---|
| `range` | `last_7_days`, `last_14_days`, `last_28_days`, `last_30_days`, `last_90_days` | `last_28_days` |
| `date_from` + `date_to` | `YYYY-MM-DD`, both required together, overrides `range` | — |
| `market` | `IT`, `FR`, `UK`, `DE` | all |
| `platform` | `google`, `youtube`, `meta`, `linkedin` | all |
| `funnel_stage` | `upper`, `mid`, `lower`, `full` | all |
| `category` | `Brand`, `Mini Excavators`, `Compact Wheel Loaders`, `Multi-Product` | all |
| `primary_kpi` | `cpl`, `clicks`, `impressions`, `reach`, `views`, `cpm`, `cpv` | all |

Any filter accepts repeats or a comma list: `?platform=google&platform=meta` or `?platform=google,meta`.

The window ends at the **latest date present in the data**, not today, so a seeded dataset never shows empty trailing days. `comparison_period` in every response is the window of equal length immediately before it — that is what every `change_pct` compares against.

---

## 3. `GET /overview/`

Drives the Overview screen.

```jsonc
{
  "period": {"start": "2026-09-23", "end": "2026-10-20", "days": 28},
  "comparison_period": {"start": "2026-08-26", "end": "2026-09-22", "days": 28},
  "currencies": ["EUR", "GBP"],
  "tiles": {
    "active_campaigns": 64,
    "total_spend": {"value": 1551740.58, "previous_value": 1595297.74, "change_pct": -2.73},
    "upper_funnel_spend": {"value": 654009.58, "share_pct": 42.15},
    "lower_funnel_spend": {"value": 576100.25, "share_pct": 37.13},
    "avg_cpl": {"key": "cpl", "value": 4.71, "change_pct": -9.09, "is_improvement": true},
    "performance": {"on_track": 51, "at_risk": 3, "off_track": 10, "total": 64}
  },
  "funnel_stage_performance": [
    {"dimension": "funnel_stage", "key": "upper", "spend": 654009.58, "share_pct": 42.15,
     "impressions": 0, "reach": 0, "clicks": 0, "conversions": 0, "cpl": 0,
     "campaign_count": 16, "on_track": 13, "at_risk": 2, "off_track": 1}
  ],
  "spend_by_platform":  [ /* same shape, key = platform */ ],
  "spend_by_category":  [ /* same shape, key = product_category */ ],
  "spend_and_conversions": [
    {"platform": "youtube", "market": "DE", "campaign_id": "...",
     "campaign_name": "Masthead", "spend": 77913.03, "conversions": 239.79}
  ],
  "weekly_spend_by_platform": [
    {"label": "W1", "week_start": "2026-09-07", "week_end": "2026-09-13",
     "is_current": false, "total": 397881.65,
     "google": 110234.1, "youtube": 140112.4, "meta": 66190.2, "linkedin": 81344.9}
  ]
}
```

Each `funnel_stage_performance` row carries every metric the chart's switcher offers (Spend / On Track / CPL / Impressions / Reach / Clicks), so switching metric needs **no new request**.

`is_current: true` marks the partial week — that is where the TODAY line goes, and why its total is lower.

---

## 4. `GET /campaigns/`

Drives both Cards and Table — they are the same payload.

Extra parameters:

| Parameter | Values |
|---|---|
| `status` | `on_track`, `at_risk`, `off_track` (computed, applied after aggregation) |
| `flagged` | `true` — only campaigns with an open flag |
| `search` | Case-insensitive match on campaign name |
| `ordering` | `name`, `spend`, `value`, `change`, `status`, `platform`, `market`; prefix `-` to reverse |

```jsonc
{
  "period": {...}, "comparison_period": {...}, "count": 64,
  "results": [{
    "platform": "youtube", "market": "IT",
    "campaign_id": "23900069174", "campaign_name": "Awareness - Bumper",
    "campaign_type": "VIDEO", "objective": "awareness",
    "funnel_stage": "upper", "product_category": "Compact Wheel Loaders",
    "ad_format": "6s Unskippable", "currency": "EUR",
    "spend": 34383.12, "previous_spend": 33990.4, "spend_change_pct": 1.16,
    "status": "off_track", "status_label": "Off Track", "status_source": "computed",
    "primary_kpi": {
      "key": "impressions", "label": "Impressions", "unit": "count",
      "direction": "higher", "value": 5975663.0, "previous_value": 5889883.0,
      "change_pct": 1.46, "is_improvement": true, "currency": null,
      "target": 8787739.71, "target_attainment_pct": 68.0
    },
    "secondary_kpis": [ /* three more blocks, same shape, no target */ ],
    "trend": [{"date": "2026-09-23", "value": 210134.0}, "... one per day"],
    "creative": { /* first creative, for the card preview */ },
    "creative_count": 2,
    "open_flags": 0
  }]
}
```

Reading a KPI block:

- `unit` tells the frontend how to render: `currency` (with `currency`), `percent` (value is a fraction — `0.025` is 2.5%), or `count`.
- `direction` is whether lower or higher is better. **`change_pct` is the raw signed change; `is_improvement` is whether that change is good.** CPL falling 90% is `change_pct: -90.3, is_improvement: true` — colour from `is_improvement`, arrow from the sign.
- `status_source` is `computed`, `override` (a human pinned it) or `no_target`. With `no_target`, `status` is `null` — render no badge rather than assuming On Track.

`GET /campaigns/export/` takes the same parameters and streams the filtered rows as `text/csv` (`Content-Disposition: attachment`), for the Export All CSV button.

---

## 5. `GET /campaigns/{platform}/{campaign_id}/`

The modal. Everything from a list row, plus:

| Field | Use |
|---|---|
| `creatives[]` | Full carousel, ordered by `position` |
| `weekly_trend[]` | `{label: "W1", week_start, week_end, value}` — the modal's weekly chart. Length from `REPORTING_WEEKS_IN_TREND` (7) |
| `daily_trend[]` | Per-day series across the window |
| `ad_account_id`, `start_date`, `end_date`, `budget_amount`, `budget_period`, `platform_status`, `synced_at` | Campaign metadata |

The flat target line comes from `primary_kpi.target`.

LinkedIn ids are URNs (`urn:li:sponsoredCampaign:390014`). They work raw or percent-encoded in the path — both tested.

---

## 6. `GET /filters/`

Sidebar counts. Returns `markets`, `platforms`, `funnel_stages`, `categories`, `primary_kpis` as `{key, count}`, and `statuses` as `{key, label, count}`.

---

## 7. Notes, flags, targets

Campaign-scoped, stored in Postgres. All list responses are paginated: `{count, next, previous, results}`.

| Method | Path | Notes |
|---|---|---|
| GET / POST | `/campaigns/{platform}/{id}/notes/` | POST body `{"body": "..."}`; author is the caller |
| GET / PATCH / DELETE | `/campaigns/{platform}/{id}/notes/{note_id}/` | |
| GET / POST | `/campaigns/{platform}/{id}/flags/` | POST body `{"reason": "performance", "detail": "..."}`. `?status=open` filters |
| PATCH | `/campaigns/{platform}/{id}/flags/{flag_id}/` | `{"status": "resolved"}` stamps `resolved_by` and `resolved_at` |
| GET / PUT | `/campaigns/{platform}/{id}/target/` | PUT upserts: `{"kpi": "cpl", "target_value": "55.00", "currency": "EUR", "direction": "lower"}` |

`reason` is one of `performance`, `creative`, `tracking`, `budget`, `other`.

Changing a target changes the status badge on the next request — the badge is computed, never stored.

---

## 8. Running it

```
manage.py seed_demo_data --as-of 2026-10-20
manage.py runserver
```

`ANALYTICS_BACKEND=local` (the default) serves everything from the NDJSON in `seed_data/`, so the whole API works with no BigQuery access. Set `ANALYTICS_BACKEND=bigquery` with the `BIGQUERY_*` variables filled to read the real dataset instead — **no response shape changes**.

`docs/postman_collection.json` imports straight into Postman. Set the `baseUrl` variable, run **Dev token**, and the collection stores the JWT for every other request automatically.

### A note on how queries run

BigQuery filters by date and campaign, and the rollup (grouping, derived metrics, status) happens in Python. At 64 campaigns that is one small scan per request and keeps a single code path for both backends. If the campaign count grows by an order of magnitude, push the `GROUP BY` into SQL — the response shapes will not need to change.
