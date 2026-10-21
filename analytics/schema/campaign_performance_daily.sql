CREATE TABLE IF NOT EXISTS `{dataset}.campaign_performance_daily` (
  platform STRING NOT NULL,
  market STRING NOT NULL,
  campaign_id STRING NOT NULL,
  date DATE NOT NULL,
  impressions INT64,
  reach INT64,
  clicks INT64,
  video_views INT64,
  video_completions INT64,
  conversions NUMERIC,
  conversion_value NUMERIC,
  spend NUMERIC,
  currency STRING,
  attribution_setting STRING,
  raw_metrics JSON,
  synced_at TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY platform, market, campaign_id;
