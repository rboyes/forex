import argparse
import datetime as dt
from typing import Any

import duckdb
import requests


BASE_ISO = "EUR"
DEFAULT_START_DATE = dt.date(2026, 1, 2)
FOREX_URL = "https://api.frankfurter.dev/v1"


def download_rates(
    base_iso: str,
    iso_codes: str,
    date: dt.date,
) -> dict[str, Any]:
    symbols_param = iso_codes
    url = f"{FOREX_URL}/{date.isoformat()}"
    params = {
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
    return payload


def write_rates(conn: duckdb.DuckDBPyConnection, payload: dict[str, Any]) -> int:
    base_iso = payload["base"]
    rows: list[tuple[str, str, dt.date, float, dt.datetime]] = []
    updated_at = dt.datetime.now(dt.timezone.utc)
    date_value = dt.date.fromisoformat(payload["date"])
    seen: set[tuple[str, str, dt.date]] = set()
    for to_iso, rate in payload["rates"].items():
        key = (base_iso, to_iso, date_value)
        if key in seen:
            continue
        seen.add(key)
        rows.append((base_iso, to_iso, date_value, float(rate), updated_at))

    if not rows:
        return 0

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
        """
        MERGE INTO staging.rates AS target
        USING (
            SELECT
                ? AS base_iso,
                ? AS to_iso,
                ? AS date,
                ? AS rate,
                ? AS updated_at
        ) AS source
        ON target.base_iso = source.base_iso
            AND target.to_iso = source.to_iso
            AND target.date = source.date
        WHEN MATCHED THEN
            UPDATE SET
                rate = source.rate,
                updated_at = source.updated_at
        WHEN NOT MATCHED THEN
            INSERT (base_iso, to_iso, date, rate, updated_at)
            VALUES (source.base_iso, source.to_iso, source.date, source.rate, source.updated_at)
        """,
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

    iso_codes = args.iso_codes
    base_iso = BASE_ISO

    end_date = dt.date.today() - dt.timedelta(days=1)
    total_inserted = 0
    with duckdb.connect(args.db_path) as conn:
        current_date = get_watermark(conn, base_iso)
        while current_date <= end_date:
            payload = download_rates(base_iso, iso_codes, current_date)
            total_inserted += write_rates(conn, payload)
            current_date += dt.timedelta(days=1)

    if total_inserted:
        print(f"Inserted {total_inserted} rows into raw.rates.")
    else:
        print("No new rates inserted.")


if __name__ == "__main__":
    main()
