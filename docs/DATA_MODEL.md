# CAT Dealer Snapshot — Data Model

How the data is split, what each table holds, and which part of the UI reads it.

---

## 1. Where data lives

| Store | Holds | Written by |
|---|---|---|
| **BigQuery** | Campaign metadata, daily performance facts, creatives | The ingestion jobs that will call the Google Ads, Meta and LinkedIn APIs |
| **PostgreSQL** | Users, KPI targets, notes, flags, status overrides | The dashboard itself, through the API |

The rule: **BigQuery is what the ad platforms tell us, Postgres is what our users tell us.** Nothing the user types ever goes to BigQuery, and no API sync ever writes to Postgres.

A campaign is identified everywhere by the pair **`(platform, campaign_id)`**, where `campaign_id` is the platform's own native id (numeric for Google/Meta, a `urn:li:sponsoredCampaign:…` for LinkedIn). Postgres rows reference campaigns by that pair rather than a foreign key, because the campaign row itself lives in BigQuery.

---

## 2. BigQuery tables

Dataset: `BIGQUERY_PROJECT.BIGQUERY_DATASET`. DDL lives in `analytics/schema/*.sql` and is applied with `manage.py bq_init`.

### 2.1 `campaigns` — one row per campaign

Clustered by `platform, market, campaign_id`.

| Column | Type | Notes |
|---|---|---|
| `platform` | STRING | `google` / `youtube` / `meta` / `linkedin` |
| `market` | STRING | `IT` / `FR` / `UK` / `DE` |
| `ad_account_id` | STRING | Native account id or URN |
| `campaign_id` | STRING | Native id, always text — never cast to a number |
| `campaign_name` | STRING | Shown as the card and table title |
| `campaign_type` / `campaign_type_raw` | STRING | Normalised type and the untouched platform value |
| `objective` / `objective_raw` | STRING | Same pattern |
| `funnel_stage` | STRING | `upper` / `mid` / `lower` / `full` |
| `product_category` | STRING | Brand, Mini Excavators, Compact Wheel Loaders, Multi-Product |
| `ad_format` | STRING | Display label under the campaign name ("Display, Video") |
| `primary_kpi` | STRING | Which KPI this campaign is judged on |
| `platform_status` / `platform_status_raw` | STRING | Serving state from the platform — **not** the On/At Risk/Off Track badge |
| `effective_status` | STRING | Platform eligibility, where provided |
| `start_date` / `end_date` | DATE | Campaign schedule |
| `budget_amount` / `budget_period` | NUMERIC / STRING | Daily or lifetime |
| `currency` | STRING | ISO code, from the account |
| `source_updated_at` | TIMESTAMP | Platform's own last-modified |
| `synced_at` | TIMESTAMP | When we fetched it — drives the freshness indicator |

### 2.2 `campaign_performance_daily` — one row per campaign per day

Partitioned by `date`, clustered by `platform, market, campaign_id`. **This is the only table that should ever be aggregated**, and every number on the dashboard ultimately comes from it.

| Column | Type | Notes |
|---|---|---|
| `platform`, `market`, `campaign_id` | STRING | Join keys back to `campaigns` |
| `date` | DATE | Partition key; report date in the account timezone |
| `impressions`, `reach`, `clicks` | INT64 | `reach` is not available on every platform |
| `video_views`, `video_completions` | INT64 | NULL for non-video formats |
| `conversions`, `conversion_value` | NUMERIC | "Leads" in the UI |
| `spend` | NUMERIC | Decimal currency units, never micros |
| `currency` | STRING | Per row, because markets differ |
| `attribution_setting` | STRING | Window the platform applied |
| `raw_metrics` | JSON | Platform-specific extras, kept for auditing |
| `synced_at` | TIMESTAMP | Fetch time |

Daily granularity is deliberate: it lets any date range, any prior-period comparison, and the weekly charts come from one table.

**A missing metric is NULL, never 0.** Zero means "it genuinely happened zero times"; NULL means unsupported, unrequested or permission-restricted.

### 2.3 `campaign_creatives` — one row per creative

Clustered the same way. A campaign usually has several, which is what the card's `1 / 2` carousel pages through.

| Column | Type | Notes |
|---|---|---|
| `platform`, `market`, `campaign_id` | STRING | Join keys |
| `ad_id`, `creative_id` | STRING | Native ids; LinkedIn uses URNs |
| `creative_name` | STRING | Caption under the preview ("Finance Offer v1") |
| `format` | STRING | Text, Vertical Video, Document Ad, … |
| `position` | INT64 | Carousel order, 1-based |
| `headline`, `primary_text`, `description`, `call_to_action` | STRING | Ad copy; localised per market |
| `display_url`, `landing_page_url` | STRING | Shown and clicked respectively |
| `image_url`, `video_id`, `thumbnail_url` | STRING | Nullable — media URLs expire, so store the reference too |
| `creative_reference` | STRING | Underlying post/share URN |
| `is_serving`, `effective_status` | BOOL / STRING | Serving state |
| `creative_fetched_at` | TIMESTAMP | Fetch time |

---

## 3. PostgreSQL tables

Django models in `campaigns/models.py`, migration `campaigns/migrations/0001_initial.py`.

### 3.1 `campaign_targets`
The target line on the modal chart and the input to the status badge.

`platform`, `campaign_id`, `kpi`, `target_value`, `currency`, `direction`, `at_risk_threshold_pct` (default 10), `off_track_threshold_pct` (default 25), `is_primary`, `updated_by`, timestamps.
Unique on `(platform, campaign_id, kpi)`.

`direction` says whether lower or higher is better — CPL wants to go down, Clicks want to go up — and the thresholds are per campaign so one noisy campaign can be given more room without changing everything.

### 3.2 `campaign_notes`
`platform`, `campaign_id`, `author`, `body`, timestamps. Backs the **Notes** tab in the modal.

### 3.3 `campaign_flags`
`platform`, `campaign_id`, `reason`, `detail`, `status` (`open` / `resolved`), `raised_by`, `resolved_by`, `created_at`, `resolved_at`. Backs **Flag an issue**, the red flag marker on cards, and the **Show flagged** filter.

### 3.4 `campaign_status_overrides`
`platform`, `campaign_id`, `status`, `note`, `set_by`. Lets a human pin a status when the computed one is wrong. One row per campaign, and it wins over the computed value.

### 3.5 `users`
Email + `google_sub`, no password. See `accounts/models.py`.

---

## 4. Derived metrics

Nothing below is stored. Each is computed at query time from summed daily rows, so it is correct for any date range. Implemented in `analytics/metrics.py`.

| KPI | Formula | Direction |
|---|---|---|
| CPL | `spend / conversions` | lower is better |
| CPC | `spend / clicks` | lower is better |
| CPM | `spend / impressions * 1000` | lower is better |
| CPV | `spend / video_views` | lower is better |
| CTR | `clicks / impressions` | higher is better |
| CVR | `conversions / clicks` | higher is better |
| Clicks, Impressions, Reach, Views, Leads, Spend | summed directly | higher is better |

**Ratios are computed on summed totals, never averaged from daily ratios** — the average of daily CPLs is not the period CPL.

### Status badge

```
ratio = target / value     (lower-is-better KPIs)
ratio = value / target     (higher-is-better KPIs)
shortfall = (1 - ratio) * 100

shortfall >= off_track_threshold_pct  -> Off Track
shortfall >= at_risk_threshold_pct    -> At Risk
otherwise                             -> On Track
```

A `campaign_status_overrides` row replaces the result. No target means no badge — not "On Track".

### vs prior

The arrow under every KPI compares the selected window against the window of equal length immediately before it. For a lower-is-better KPI a fall is an improvement, so the arrow direction and its colour are independent: direction comes from the sign, colour from `direction`.

---

## 5. UI → data map

### Overview
| Element | Source |
|---|---|
| Total Spend | `SUM(spend)` over the window |
| Upper / Lower Funnel tiles | Same, filtered by `campaigns.funnel_stage`, with share of total |
| Avg CPL | `SUM(spend) / SUM(conversions)` across campaigns whose `primary_kpi = 'cpl'` |
| On Track `51/64` | Count of computed statuses |
| Funnel Stage Performance | Group by `funnel_stage`; the metric switcher changes only the aggregate, not the grouping |
| Spend by Platform / by Product Category | Group by `platform` / `product_category` |
| Spend & Conversions | Per campaign: bar = `SUM(spend)` coloured by platform, line = `SUM(conversions)` |
| Weekly Spend by Platform | Group by ISO week × platform; the TODAY marker is the current partial week |

### Cards and Table
Both read the same per-campaign aggregate — the Table is the Cards list with more columns, so one endpoint serves both.

| Element | Source |
|---|---|
| Platform / Funnel / Category badges | `campaigns` |
| Title, format line | `campaign_name`, `ad_format` |
| Creative preview + `1 / 2` | `campaign_creatives`, ordered by `position` |
| Primary KPI label and value | `campaigns.primary_kpi` + computed value |
| vs prior | Prior-window comparison |
| Sparkline | Daily primary-KPI series across the window |
| Campaign Spend | `SUM(spend)` |
| Status badge | Computed, per section 4 |
| Flag marker | Open rows in `campaign_flags` |
| Secondary KPIs | The remaining computed metrics |

### Campaign modal
| Element | Source |
|---|---|
| Creative carousel | `campaign_creatives` |
| Primary KPI vs TARGET | Computed value + `campaign_targets.target_value` |
| Campaign Spend, Format | `campaign_performance_daily`, `campaigns` |
| Weekly KPI trend + target line | Primary KPI per ISO week + the flat target |
| Secondary KPI tiles | Computed |
| Notes tab | `campaign_notes` |
| Flag an issue | `campaign_flags` |

### Sidebar filters
Market, Platform, Status, Funnel Stage, Category, Primary KPI. All but Status are columns on `campaigns` and filter in BigQuery; **Status is computed from Postgres targets, so it is applied after aggregation**, in the API.

---

## 6. Currency

`spend` carries its own `currency`, because UK campaigns bill in GBP and IT/FR/DE in EUR. The mockups show a single `€1.5M` total across both, which is only correct if a reporting currency with FX conversion is defined.

Until then: the API returns the per-row currency, and totals are only summed within one currency. When FX arrives, the normalised amount, the rate and the rate date get stored alongside the original — the original is never overwritten.

---

## 7. Commands

| Command | Does |
|---|---|
| `manage.py bq_init` | Creates the dataset and the three tables (`--dry-run` prints the DDL) |
| `manage.py seed_demo_data` | Generates 64 campaigns × 180 days + creatives as NDJSON in `seed_data/`, and writes matching KPI targets to Postgres |
| `manage.py seed_demo_data --load-bq` | Same, and loads it into BigQuery |

The generator in `analytics/catalogue.py` and `analytics/seed.py` reproduces the mockups: 64 campaigns across 4 markets (Google 20, YouTube 16, LinkedIn 16, Meta 12), ~€1.55M of 28-day spend, and a 51 / 3 / 10 status split. It is deterministic — the same `--as-of` always gives the same numbers.

---

## 8. When the real APIs arrive

The ingestion jobs write to the same three tables; nothing above changes.

| Platform | Campaigns | Performance | Creatives |
|---|---|---|---|
| Google / YouTube | GAQL `campaign` via `googleAds:searchStream` | Same query with `segments.date` | `ad_group_ad` |
| Meta | `act_{id}/campaigns` | `/insights` with `time_increment=1` | `adcreatives` |
| LinkedIn | `adAccounts/{id}/adCampaigns` | `adAnalytics?q=statistics&pivots=List(CAMPAIGN)&timeGranularity=DAILY` | `adAccounts/{id}/creatives` |

Points to hold to when wiring them up:

- Request **daily** granularity everywhere, so the fact table stays per-day.
- Google returns `cost_micros` — divide by 1,000,000 before storing.
- Meta returns `actions` as a typed array; map one defined action to `conversions` and keep the rest in `raw_metrics`.
- LinkedIn's analytics finder has no pagination — split long date ranges instead.
- Re-syncing a day must replace that day's rows, not append. Partitioning by `date` makes that a partition overwrite.
- Keep `synced_at` current; the UI's freshness indicator reads it.

---

## 9. Open questions for the team

Everything below was assumed in order to keep building. Each one has a note on what we did and what changes if the answer differs.

### Blocking — these change where columns live

**9.1 Where do `funnel_stage`, `product_category`, `market` and `primary_kpi` come from?**
None of these exist in the Google, Meta or LinkedIn APIs, but the dashboard filters and groups by all four. They are currently columns on the `campaigns` table, as if they arrive with the data.
Candidates: parsed from a campaign naming convention, supplied as a mapping sheet by the client, derived from the ad account, or set by hand in our own UI.
If they are set by hand or come from a mapping sheet, they belong in Postgres, not BigQuery — a mapping table keyed on `(platform, campaign_id)`.

**9.2 Is there a single reporting currency?**
UK campaigns bill in GBP, IT/FR/DE in EUR, but the mockups show one `€1.5M` total across both, and Avg CPL appears as `€7` on Cards and `$7` on Overview.
Currently spend carries its own currency per row and nothing is converted. If a single reporting currency is required we need: which one, the FX source, and whether the rate is daily or fixed per period.

**9.3 What counts as a conversion, per platform?**
The dashboard shows "Leads" and CPL across all four platforms as if they were comparable. Google conversions depend on the account's conversion setup, Meta returns a typed `actions` array with no universal "conversion", LinkedIn differs again.
We need the canonical definition per platform, otherwise CPL is not comparable across a row of the table.

### Needed before the numbers are trustworthy

**9.4 Who sets KPI targets, and at what level?**
Targets are per campaign per KPI in Postgres right now. Are they set per campaign, or inherited from a market/funnel-level goal? Where do they live today — a spreadsheet? Should they be editable in the dashboard, and by whom?

**9.5 Is a target tied to a period?**
A target of 55 means nothing without a window. The current model treats it as a flat line compared against whatever range the user selects. If targets are monthly, selecting "Last 7 days" compares against a monthly figure and will read wrong.

**9.6 Are the 10% / 25% status bands right?**
At Risk at 10% off target and Off Track at 25% are our defaults, stored per campaign so they can be tuned. Has the client defined these?

**9.7 Which timezone defines a "day"?**
Each ad account reports in its own timezone. Four markets means four possible day boundaries. We need one reporting timezone for comparisons, or the totals will not reconcile with each platform's own UI.

**9.8 What is the attribution window?**
Stored per row as `attribution_setting` but not yet normalised. Platforms default differently, which affects every conversion number.

### Operational

**9.9 Who runs the ingestion into BigQuery — their team or us?**
This decides whether we build the sync jobs or just read tables someone else populates.

**9.10 How often does the data refresh, and what does "Live — BigQuery" promise?**
Drives caching, and whether the indicator means "synced within N hours" or just "connected".

**9.11 How much history is needed?**
Affects partition retention and how far back "vs prior" can go.

**9.12 Creative media — who hosts the images and video thumbnails?**
Platform media URLs expire and are often permission-gated. We store the native reference as well as the URL, but if the dashboard must show previews reliably, the assets need copying to our own storage.

**9.13 Does every user see all 64 campaigns?**
There is no per-market or per-role access control at the moment. If a dealer or market lead should only see their own market, that changes the auth model.

**9.14 Is the EN language toggle frontend-only?**
Assumed yes — the API returns raw values and the frontend renders the labels. Creative copy is already localised in the data itself.

**9.15 Can notes and flags attach to anything other than a campaign?**
Currently campaign-level only. No assignment, notification or workflow beyond open/resolved.
