import argparse
import datetime as dt
import json
from typing import Any

import requests
from google.cloud import bigquery
from google.cloud import storage


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


def build_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_iso = payload["base"]
    rows: list[dict[str, Any]] = []
    updated_at = dt.datetime.now(dt.timezone.utc)
    updated_at_value = updated_at.isoformat(timespec="seconds").replace("+00:00", "Z")
    date_value = dt.date.fromisoformat(payload["date"])
    seen: set[tuple[str, str, dt.date]] = set()
    for to_iso, rate in payload["rates"].items():
        key = (base_iso, to_iso, date_value)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "base_iso": base_iso,
                "to_iso": to_iso,
                "date": date_value.isoformat(),
                "rate": float(rate),
                "updated_at": updated_at_value,
            }
        )

    return rows


def write_json_to_gcs(
    client: storage.Client,
    bucket_name: str,
    prefix: str,
    date_value: dt.date,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0
    normalized_prefix = prefix.rstrip("/")
    object_name = f"{normalized_prefix}/{date_value.isoformat()}.json"
    payload = "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n"
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(payload, content_type="application/x-ndjson")
    return len(rows)


def get_watermark(
    client: bigquery.Client,
    project_id: str,
    table_id: str,
    base_iso: str,
) -> dt.date:
    query = f"select max(date) as max_date from `{project_id}.{table_id}` where base_iso = @base_iso"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
        ]
    )
    try:
        result = client.query(query, job_config=job_config).result()
    except Exception:
        return DEFAULT_START_DATE
    row = next(iter(result), None)
    if row and row.max_date:
        return row.max_date + dt.timedelta(days=1)
    return DEFAULT_START_DATE


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download forex rates into GCS as newline-delimited JSON for EUR.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--iso-codes",
        default="GBP,USD,NZD,CAD,AUD,JPY",
        help="Comma-separated ISO currency codes",
    )
    parser.add_argument(
        "--bucket-name",
        default="forex-20260115",
        help="GCS bucket name for JSON output.",
    )
    parser.add_argument(
        "--prefix",
        default="json/incoming",
        help="GCS prefix for JSON output.",
    )
    parser.add_argument(
        "--bq-project",
        default="forex-20260115",
        help="BigQuery project id that holds presentation.rates.",
    )
    parser.add_argument(
        "--bq-watermark-table",
        default="presentation.rates",
        help="BigQuery table (dataset.table) used for watermarking.",
    )
    args = parser.parse_args()

    iso_codes = args.iso_codes
    base_iso = BASE_ISO

    now_utc = dt.datetime.now(dt.timezone.utc)
    if now_utc.time() >= dt.time(16, 0):
        end_date = now_utc.date()
    else:
        end_date = now_utc.date() - dt.timedelta(days=1)
    total_inserted = 0
    storage_client = storage.Client()
    bq_client = bigquery.Client(project=args.bq_project)
    current_date = get_watermark(bq_client, args.bq_project, args.bq_watermark_table, base_iso)
    while current_date <= end_date:
        payload = download_rates(base_iso, iso_codes, current_date)
        rows = build_rows(payload)
        total_inserted += write_json_to_gcs(
            storage_client,
            args.bucket_name,
            args.prefix,
            current_date,
            rows,
        )
        current_date += dt.timedelta(days=1)

    if total_inserted:
        print(f"Uploaded {total_inserted} rows to gs://{args.bucket_name}/{args.prefix}.")
    else:
        print("No new rates inserted.")


if __name__ == "__main__":
    main()
