# AGENTS.md

Project: Forex rates downloader that stores historical data in BigQuery via GCS.

## Quick Start
- Install deps: `uv sync`
- Run downloader: `uv run python downloader.py`
- Run dbt: `uv run dbt run`
- Move incoming JSON after processing: `gcloud storage mv "gs://forex-20260115/json/incoming/*.json" gs://forex-20260115/json/processed/`

## Configuration
- Base currency is fixed to `EUR`.
- ISO codes are passed as a comma-separated string via `--iso-codes`.
- Downloader writes newline-delimited JSON to `gs://forex-20260115/json/incoming/`.
- Watermark comes from `presentation.rates` via `--bq-watermark-table` (default `presentation.rates`).

## Data Storage
- BigQuery datasets: `raw`, `staging`, `presentation`
- External table: `raw.rates` (points at GCS JSON in `json/incoming`)
- Staging table: `staging.rates`
- Presentation tables: `presentation.rates`, `presentation.twi`
- Columns: `base_iso`, `to_iso`, `date`, `rate`, `updated_at`

## Notes
- Data is downloaded from the Frankfurter API historical endpoint.
- The downloader fetches from the watermark date through yesterday (UTC).
