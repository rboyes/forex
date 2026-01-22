# AGENTS.md

Project: Forex rates downloader that stores historical data in BigQuery.

## Quick Start
- Install deps: `uv sync`
- Run downloader: `uv run python scripts/downloader.py`
- Run dbt: `uv run dbt run --project-dir dbt --profiles-dir dbt`

## Configuration
- Base currency is fixed to `EUR`.
- ISO codes are passed as a comma-separated string via `--iso-codes`.
- Downloader loads directly into BigQuery `staging.rates` using dlt.

## Data Storage
- BigQuery datasets: `staging`, `presentation`
- Staging table: `staging.rates`
- Presentation tables: `presentation.rates`, `presentation.twi`
- Columns: `base_iso`, `to_iso`, `date`, `rate`, `created_at`, `updated_at`

## Notes
- Data is downloaded from the Frankfurter API historical endpoint.
- The downloader fetches from the watermark date through yesterday (UTC).
