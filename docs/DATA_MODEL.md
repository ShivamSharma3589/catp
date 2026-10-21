# CAT Dealer Snapshot — Data Analysis

What the dashboard displays, where each number comes from, how the data is structured, and what is still unconfirmed.

---

## 1. Scope

A reporting dashboard for CAT dealer advertising across four markets (IT, FR, UK, DE) and four platforms (Google, YouTube, Meta, LinkedIn) — 64 campaigns in total.

It is **read-only**. Campaigns are created and managed in each platform's own tools; this dashboard reports on them and adds a layer of commentary — targets, notes and flagged issues — that the platforms have no concept of.

The analysis below separates every value on screen into three kinds:

| Kind | Meaning |
|---|---|
| **Sourced** | Comes from a platform advertising API |
| **Calculated** | Derived by us from sourced values |
| **Unconfirmed** | Appears on screen, but has no identified source yet |

That distinction drives the whole design, because only sourced data can be synced, only calculated data is guaranteed consistent, and unconfirmed data is project risk.

---

## 2. What the dashboard shows

**Present on every screen**
- Date range selector, language toggle, view switcher
- Summary strip: Active Campaigns, Total Spend, Performance split (On Track / At Risk / Off Track), Avg CPL
- Filter sidebar with live counts: Market, Platform, Status, Funnel Stage, Category, Primary KPI

**Overview** — the aggregate picture
- Five tiles: Total Spend, Upper Funnel spend (value + % of total), Lower Funnel spend, Avg CPL, On Track count
- Funnel Stage Performance — bar chart with a switchable metric (Spend / On Track / CPL / Impressions / Reach / Clicks)
- Spend by Platform and Spend by Product Category — two donuts
- Spend & Conversions — spend bars per campaign with a leads line overlaid
- Weekly Spend by Platform — stacked weekly bars with a marker on the current, partial week

**Cards** — one card per campaign
Platform, funnel and category badges · campaign name and ad format · creative preview with carousel · the campaign's primary KPI with its change vs the previous period · a trend sparkline · secondary KPIs · campaign spend · status badge · flag control.

**Table** — the same campaigns as rows
Platform, Campaign, Funnel, Category, Primary KPI, Value, vs Prior, Spend, Status, Trend. With search, column selection, grouping, sorting, multi-select and CSV export.

**Campaign detail** — opened from a card or row
Creative carousel · primary KPI against its **target** · spend and format · a weekly KPI trend with the target drawn as a line · secondary KPI tiles · a Notes tab · issue flagging.

**One structural point that shapes everything downstream:** the primary KPI is **per campaign, not global**. A lead-generation campaign is judged on CPL, an awareness campaign on Reach or Impressions, a video campaign on Views or CPV. The dashboard must carry each campaign's KPI identity, its unit, and whether higher or lower is better.

---

## 3. Metric glossary

| Term | Meaning | Formula |
|---|---|---|
| Impressions | Times an ad was displayed | counted |
| Reach | Unique people who saw it | counted |
| Clicks | Clicks on the ad | counted |
| Leads / Conversions | Completed actions of value | counted |
| Spend | Media cost | counted |
| **CTR** | Click-Through Rate — % of viewers who clicked | clicks ÷ impressions |
| **CVR** | Conversion Rate — % of clickers who converted | conversions ÷ clicks |
| **CPC** | Cost Per Click | spend ÷ clicks |
| **CPL** | Cost Per Lead | spend ÷ conversions |
| **CPM** | Cost per 1,000 impressions | spend ÷ impressions × 1000 |
| **CPV** | Cost Per View | spend ÷ video views |

**Funnel stage** — which part of the buying journey a campaign targets. *Upper* = awareness, *Mid* = consideration, *Lower* = conversion, *Full* = all three. It is how spend is judged: cheap leads are the goal at the lower funnel, cheap reach at the upper.

---

## 4. Sourced data — what the advertising APIs give us

Three APIs cover the four platforms. **YouTube is not a separate integration** — YouTube campaigns are Google Ads campaigns and come back from the Google Ads API, identified by campaign type.

| Platforms | API | Reporting mechanism |
|---|---|---|
| Google, YouTube | Google Ads API | GAQL queries against the reporting service |
| Meta | Meta Marketing API (Graph) | `campaigns`, `insights` and `adcreatives` edges |
| LinkedIn | LinkedIn Marketing API | `adCampaigns`, `adAnalytics` and `creatives` resources |

Each platform needs **three separate requests**. No API returns campaign details, performance and creative content together.

**4.1 Campaign metadata** — one record per campaign
Campaign ID, name, type, objective, status, start and end dates, budget and basis, account ID, currency.

**4.2 Performance** — requested at daily granularity
Impressions, reach, clicks, video views, conversions, conversion value, spend.

**4.3 Creative content** — one or more per campaign
Ad and creative IDs, headline, body copy, call to action, destination URL, image or video reference.

### Differences that have to be absorbed

These are the practical reasons a shared schema is needed rather than storing each platform's response as-is.

| Issue | Detail |
|---|---|
| Cost units | Google reports cost in micros — one millionth of the account currency. Must be converted on ingest. |
| Conversions | Meta returns a typed array of actions, not a single conversion count. One action type has to be chosen as "lead"; the rest kept for reference. |
| Creative completeness | A creative record often references an underlying post rather than containing the text and image. LinkedIn in particular. Resolving it is a further request. |
| Media URLs | Image and video URLs expire and can be permission-gated. The stable asset reference must be stored alongside the URL. |
| Reach | Not consistently available on every platform. Must be nullable. |
| Pagination | Google streams batches, Meta uses cursors, LinkedIn's analytics endpoint has no pagination at all — long date ranges must be split by the caller. |
| Versioning | Google uses numeric versions, LinkedIn a year-month header, Meta a Graph version. All three deprecate on their own schedule. |

**Access requirements** — a Google Ads developer token plus account-level OAuth; Meta app permissions for reading ads; LinkedIn advertising API approval plus an ad-account role. Read-only access is sufficient throughout. These approvals are typically the longest lead time in the project.

---

## 5. Calculated data — what we derive

Nothing in this section is fetched. All of it is computed from the raw daily counts at the moment a request is made, which is why any date range works without re-syncing.

**5.1 Every ratio KPI** — CTR, CVR, CPC, CPL, CPM, CPV, per the formulas in section 3.

**5.2 Period comparison** — the ± figure under every number compares the selected window against the window of equal length immediately preceding it.

**5.3 Status** — On Track / At Risk / Off Track, by comparing a campaign's primary KPI to its target:

```
within 10% of target     -> On Track
10-25% short of target   -> At Risk
more than 25% short      -> Off Track
```

Direction matters: CPL beating its target means coming in *below* it, Reach means coming in *above* it. Each KPI carries that direction.

**5.4 All aggregates** — total spend, average CPL, funnel splits and their percentages, spend by platform and category, the status counts, weekly buckets.

**5.5 All trend lines** — sparklines and the weekly chart are the same KPI recalculated per day or per week.

### Two rules that protect the numbers

**Ratios are computed on summed totals, never averaged.** The average of 28 daily CPL values is not the 28-day CPL. Averaging ratios weights a quiet Sunday the same as a heavy Monday and produces a number that reconciles with nothing.

**A missing metric is null, never zero.** Zero means it genuinely happened zero times. Null means unsupported by that platform, not requested, or restricted. Collapsing the two silently corrupts every average built on top.

---

## 6. Unconfirmed data — no identified source

Everything here is on the prototype screens but has no confirmed origin. Some may be real requirements; some may be prototype decoration. Each needs a decision.

### Blocking — these change the data model

**Q1. Funnel stage, product category, market, and primary KPI.**
The dashboard filters, groups and judges campaigns by these four. **None of them exist in any advertising API.** Possible sources: parsed from a campaign naming convention, supplied as a mapping by the client, inferred from the ad account, or maintained by hand in this tool.
*Impact:* if they are maintained by hand or supplied separately, they are our data, not platform data, and belong in the operational database rather than the analytics warehouse. This is the single most important question to resolve.

**Q2. Is there one reporting currency?**
UK campaigns bill in GBP, the others in EUR, yet the summary tiles show a single total. A combined total is only meaningful with a defined reporting currency and FX source.
*Impact:* if conversion is required we need the target currency, the rate source, and whether rates are daily or fixed per period.

**Q3. What counts as a lead, per platform?**
CPL is compared across platforms throughout the dashboard. Each platform defines conversions differently, and Meta does not define one at all without choosing an action type.
*Impact:* without a single agreed definition, cross-platform CPL comparison is not valid, however well it renders.

### Needed before the numbers can be trusted

**Q4. Who sets KPI targets, and at what level?** Per campaign, or inherited from a market or funnel goal? Where do they live today?

**Q5. Are targets tied to a period?** A target of 55 is meaningless without a window. If targets are monthly but a user selects a 7-day range, the comparison is wrong. Either targets are rated per period, or the comparison is restricted to matching windows.

**Q6. Are the 10% / 25% status thresholds client-defined,** or placeholders? They are currently assumptions.

**Q7. Which timezone defines a day?** Four markets can mean four day boundaries. One reporting timezone is needed or totals will not reconcile against each platform's own interface.

**Q8. What attribution window applies?** Platforms default differently, and attribution changes every conversion figure.

### Operational

**Q9. Who runs the data ingestion — the client's team or ours?** Determines whether we build the sync layer or read tables someone else populates.

**Q10. How often must data refresh,** and what does the live data indicator promise — freshness within a set period, or just connectivity?

**Q11. How much history is required?** Drives retention and how far back period comparison can reach.

**Q12. Who hosts creative images and video thumbnails?** Platform URLs expire. Reliable previews require copying assets to our own storage.

**Q13. Does every user see all markets?** There is no per-market or per-role access model defined. If a market lead should only see their own market, that is a requirement, not a detail.

**Q14. Is the language toggle translating the interface, the ad copy, or nothing yet?**

**Q15. Can notes and flags attach to anything other than a campaign,** and is there a workflow beyond open and resolved — assignment, notification, audit?

---

## 7. Data structure

### 7.1 Two stores, one rule

| Store | Holds | Written by |
|---|---|---|
| **Analytics warehouse (BigQuery)** | Campaign metadata, daily performance, creatives | The ingestion that reads the advertising APIs |
| **Operational database (PostgreSQL)** | Users, KPI targets, notes, flagged issues, status overrides | The dashboard, from user actions |

**What the platforms tell us is separated from what our users tell us.** User input never enters the warehouse, and a sync never overwrites user input. The two have completely different update patterns: one is bulk-loaded and re-synced wholesale, the other is small, transactional and must never be lost.

A campaign is identified everywhere by **(platform, campaign_id)**, using the platform's own identifier, stored as text. Platform IDs are not all numeric — LinkedIn uses URNs — and they are never arithmetic, so text is correct.

### 7.2 Three analytics tables, not one

A single flat table is tempting and wrong: campaign details change rarely, performance changes daily, creatives change independently of both. Combining them forces re-writing unchanged data and loses the ability to trace a discrepancy to one source. One wide view can always be assembled on top for consumption.

**`campaigns`** — one row per campaign

| Column | Type | Note |
|---|---|---|
| platform, market | STRING | |
| ad_account_id, campaign_id | STRING | Native identifiers |
| campaign_name | STRING | |
| campaign_type, campaign_type_raw | STRING | Normalised value plus the untouched platform value |
| objective, objective_raw | STRING | Same pattern |
| funnel_stage, product_category | STRING | **See Q1 — source unconfirmed** |
| ad_format | STRING | Display label |
| primary_kpi | STRING | **See Q1** |
| platform_status, platform_status_raw, effective_status | STRING | Serving state — *not* the On Track badge |
| start_date, end_date | DATE | |
| budget_amount, budget_period, currency | NUMERIC / STRING | |
| source_updated_at, synced_at | TIMESTAMP | Platform's own timestamp, and ours |

**`campaign_performance_daily`** — one row per campaign per day. Partitioned by date, clustered by platform, market and campaign.

| Column | Type | Note |
|---|---|---|
| platform, market, campaign_id | STRING | Join keys |
| date | DATE | Partition key |
| impressions, reach, clicks | INT64 | Reach nullable |
| video_views, video_completions | INT64 | Null for non-video |
| conversions, conversion_value | NUMERIC | **See Q3** |
| spend, currency | NUMERIC / STRING | Decimal units, never micros |
| attribution_setting | STRING | **See Q8** |
| raw_metrics | JSON | Platform-specific extras, kept for audit |
| synced_at | TIMESTAMP | |

**Daily granularity is the single most important design decision here.** Storing a pre-aggregated period would fix the dashboard to one date range. Daily rows let any range, any comparison period and any weekly bucket be answered from one table, and let a single day be corrected without touching the rest.

**`campaign_creatives`** — one row per creative

| Column | Type | Note |
|---|---|---|
| platform, market, campaign_id | STRING | Join keys |
| ad_id, creative_id | STRING | Native identifiers |
| creative_name, format, position | STRING / INT64 | Position orders the card carousel |
| headline, primary_text, description, call_to_action | STRING | Localised per market |
| display_url, landing_page_url | STRING | |
| image_url, video_id, thumbnail_url | STRING | Nullable — **see Q12** |
| creative_reference | STRING | Stable asset reference, outlives the URL |
| is_serving, effective_status | BOOL / STRING | |
| creative_fetched_at | TIMESTAMP | |

### 7.3 Operational tables

| Table | Holds |
|---|---|
| `campaign_targets` | Target value per campaign and KPI, its direction, and the At Risk / Off Track thresholds |
| `campaign_notes` | Commentary against a campaign, with author and timestamp |
| `campaign_flags` | Raised issues, with reason, author, open/resolved state and who resolved them |
| `campaign_status_overrides` | A manually pinned status, for when the calculated one is wrong |
| `users` | Dashboard users, authenticated by Google sign-in |

**Status is calculated at read time, never stored.** Changing a target instantly corrects every historical view. A stored status would need recalculating across all history on every target change, and would drift the moment that failed.

---

## 8. Principles carried through the design

1. **Keep the raw value next to the normalised one.** Every `_raw` column exists so a discrepancy can be traced back to what the platform actually said.
2. **Store counts, derive ratios.** Counts are facts; ratios are interpretations and depend on the window.
3. **Null is not zero.**
4. **Re-syncing a day replaces that day.** Date partitioning makes a re-sync a partition overwrite rather than a duplicate-prone merge.
5. **Keep the currency with the amount.** Converting on the way in destroys the original. Any conversion keeps the amount, the rate and the rate date separately.
6. **Record sync time on every row.** Freshness is a fact the dashboard displays and support questions depend on.

---

## 9. Risks

| Risk | Why it matters |
|---|---|
| **API access approvals** | Google developer tokens, Meta app review and LinkedIn advertising API approval are external dependencies with their own timelines. Usually the critical path. |
| **Q1 unresolved** | Four fields the dashboard is organised around have no confirmed source. The longer it is open, the more is built on an assumption. |
| **Cross-platform comparability** | Conversions, attribution and video view definitions differ. The dashboard presents them side by side as though they do not. |
| **Reconciliation** | Totals will be checked against each platform's own interface. Timezone, attribution and currency decisions determine whether they match. |
| **Creative assets** | Expiring URLs mean previews degrade over time unless assets are copied to our own storage. |

---

## 10. Recommended next steps

1. Resolve **Q1, Q2 and Q3** with the client — each changes the data model, not just a display.
2. Start the **platform access approvals** immediately; they run in parallel with everything else.
3. Confirm the **target-setting process** (Q4, Q5) — the status badge is the dashboard's main judgement and it rests entirely on this.
4. Validate one market and one platform end to end against the platform's own reporting interface before extending to all four.
5. Agree a **reporting timezone and attribution basis** in writing, since both change every number.
