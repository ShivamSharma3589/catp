CREATE TABLE IF NOT EXISTS `{dataset}.campaign_creatives` (
  platform STRING NOT NULL,
  market STRING NOT NULL,
  campaign_id STRING NOT NULL,
  ad_id STRING,
  creative_id STRING NOT NULL,
  creative_name STRING,
  format STRING,
  position INT64,
  headline STRING,
  primary_text STRING,
  description STRING,
  call_to_action STRING,
  display_url STRING,
  landing_page_url STRING,
  image_url STRING,
  video_id STRING,
  thumbnail_url STRING,
  creative_reference STRING,
  is_serving BOOL,
  effective_status STRING,
  creative_fetched_at TIMESTAMP NOT NULL
)
CLUSTER BY platform, market, campaign_id;
