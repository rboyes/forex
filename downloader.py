import argparse
import datetime as dt
import os
from typing import Any

import duckdb
import requests
from dotenv import load_dotenv


BASE_ISO = "EUR"
DEFAULT_START_DATE = dt.date(2026, 1, 15)
FIXER_URL = "https://data.fixer.io/api"


def download_rates(
    base_iso: str,
    iso_codes: str,
    date: dt.date,
    api_key: str,
) -> dict[str, Any]:
    symbols_param = iso_codes
    url = f"{FIXER_URL}/{date.isoformat()}"
    params = {
        "access_key": api_key,
        "base": base_iso,
        "symbols": symbols_param,
    }
    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success", False):
        raise RuntimeError(f"Fixer API error for base {base_iso}: {payload}")
    return payload


def write_rates(db_path: str, payload: dict[str, Any]) -> int:
    base_iso = payload["base"]
    rows: list[tuple[str, str, dt.date, float, dt.datetime]] = []
    updated_at = dt.datetime.now(dt.timezone.utc)
    date_value = dt.date.fromisoformat(payload["date"])
    for to_iso, rate in payload["rates"].items():
        rows.append((base_iso, to_iso, date_value, float(rate), updated_at))

    if not rows:
        return 0

    with duckdb.connect(db_path) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS staging")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS staging.rates (
                base_iso TEXT,
                to_iso TEXT,
                date DATE,
                rate DOUBLE,
                updated_at TIMESTAMP
            )
            """
        )
        conn.executemany(
            "INSERT INTO staging.rates (base_iso, to_iso, date, rate, updated_at) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
    return len(rows)


def get_watermark(
    conn: duckdb.DuckDBPyConnection,
    base_iso: str,
) -> dt.date:
    try:
        result = conn.execute(
            "SELECT MAX(date) FROM staging.rates WHERE base_iso = ?",
            [base_iso],
        ).fetchone()
    except duckdb.CatalogException:
        return DEFAULT_START_DATE
    if result and result[0]:
        return result[0] + dt.timedelta(days=1)
    return DEFAULT_START_DATE


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download forex rates into DuckDB for EUR.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--iso-codes",
        default="GBP,USD,NZD,CAD,AUD,JPY",
        help="Comma-separated ISO currency codes",
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to the DuckDB database file.",
    )
    args = parser.parse_args()

    api_key = os.getenv("API_KEY")
    if not api_key:
        load_dotenv(".env.local")
        api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY not found in environment or .env.local.")

    iso_codes = args.iso_codes
    base_iso = BASE_ISO

    end_date = dt.date.today() - dt.timedelta(days=1)
    total_inserted = 0
    with duckdb.connect(args.db_path) as conn:
        start_date = get_watermark(conn, base_iso)
        if start_date <= end_date:
            current_date = start_date
            while current_date <= end_date:
                payload = download_rates(base_iso, iso_codes, current_date, api_key)
                total_inserted += write_rates(args.db_path, payload)
                current_date += dt.timedelta(days=1)

    if total_inserted:
        print(f"Inserted {total_inserted} rows into raw.rates.")
    else:
        print("No new rates inserted.")


if __name__ == "__main__":
    main()
