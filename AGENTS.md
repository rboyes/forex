# AGENTS.md

Project: Forex rates downloader that stores historical data in DuckDB.

## Quick Start
- Install deps: `uv sync`
- Run downloader: `uv run python downloader.py --db-path forex.duckdb`

## Configuration
- API key is read from `API_KEY` in the environment or `.env.local`.
- Base currency is fixed to `EUR`.
- ISO codes are passed as a comma-separated string via `--iso-codes`.

## Data Storage
- DuckDB schema: `staging`
- Table: `staging.rates`
- Columns: `base_iso`, `to_iso`, `date`, `rate`, `updated_at`

## Notes
- Data is downloaded from the Fixer API historical endpoint.
- The downloader fetches from the watermark date through yesterday (UTC).
