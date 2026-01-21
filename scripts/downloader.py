import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Any, Iterator

import dlt
import requests
from dlt.destinations import bigquery
from google.cloud import bigquery as bq
from google.api_core import exceptions as gcloud_exceptions


BASE_ISO = "EUR"
DEFAULT_START_DATE = dt.date(2026, 1, 2)
FOREX_URL = "https://api.frankfurter.dev/v1"
CUTOFF_TIME = dt.time(16, 0, 0)  # Time before which we don't download today's x rates
WEIGHTS_CSV = (Path(__file__).resolve().parent / ".." / "seeds" / "seed_weights.csv").resolve()
PROJECT_ID = "forex-20260115"
LOCATION = "europe-west2"


def download_rates(
    base_iso: str,
    iso_codes: str,
    date: dt.date,
) -> dict[str, Any]:
    url = f"{FOREX_URL}/{date.isoformat()}"
    params = {
        "base": base_iso,
        "symbols": iso_codes,
    }
    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_rows(payload: dict[str, Any], timestamp: dt.datetime) -> list[dict[str, Any]]:
    base_iso = payload["base"]
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    date_value = dt.date.fromisoformat(payload["date"])
    for to_iso, rate in payload["rates"].items():
        key = (base_iso, to_iso, date_value.isoformat())
        rows[key] = {
            "base_iso": base_iso,
            "to_iso": to_iso,
            "date": date_value,
            "rate": float(rate),
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    return list(rows.values())


def iter_rates(
    base_iso: str,
    iso_codes: str,
    start_date: dt.date,
    end_date: dt.date,
) -> Iterator[dict[str, Any]]:
    current_date = start_date
    while current_date <= end_date:
        payload = download_rates(base_iso, iso_codes, current_date)
        timestamp = dt.datetime.now(dt.timezone.utc)
        for row in build_rows(payload, timestamp):
            yield row
        current_date += dt.timedelta(days=1)


def get_watermark(
    client: bq.Client,
    project_id: str,
    table_id: str,
) -> dt.date:
    query = f"select max(date) as max_date from `{project_id}.{table_id}`"
    try:
        result = client.query(query).result()
    except gcloud_exceptions.NotFound:
        return DEFAULT_START_DATE
    row = next(iter(result), None)
    if row and row.max_date:
        return row.max_date + dt.timedelta(days=1)
    return DEFAULT_START_DATE


def load_iso_codes(weights_path: Path, base_iso: str) -> str:
    if not weights_path.exists():
        raise SystemExit(f"weights csv not found: {weights_path}")
    with weights_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        iso_codes: list[str] = []
        seen: set[str] = set()
        for row in reader:
            if row.get("base_iso") != base_iso:
                continue
            to_iso = row.get("to_iso")
            if not to_iso or to_iso in seen:
                continue
            iso_codes.append(to_iso)
            seen.add(to_iso)
    if not iso_codes:
        raise SystemExit(f"no currencies found for base_iso={base_iso} in {weights_path}")
    return ",".join(iso_codes)


@dlt.resource(
    name="rates",
    primary_key=("base_iso", "to_iso", "date"),
    write_disposition="merge",
)
def rates_resource(
    iso_codes: str,
    start_date: dt.date,
    end_date: dt.date,
    counter: dict[str, int],
) -> Iterator[dict[str, Any]]:
    for row in iter_rates(BASE_ISO, iso_codes, start_date, end_date):
        counter["rows"] += 1
        yield row


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download forex rates into BigQuery staging for EUR.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bq-table",
        default="staging.rates",
        help="BigQuery table (dataset.table) for staging rates.",
    )
    args = parser.parse_args()

    if "." not in args.bq_table:
        raise SystemExit("--bq-table must be in dataset.table format")
    dataset_name, table_name = args.bq_table.split(".", 1)
    if table_name != "rates":
        raise SystemExit("dlt loader currently supports only the rates table name")

    iso_codes = load_iso_codes(WEIGHTS_CSV, BASE_ISO)
    bq_client = bq.Client(project=PROJECT_ID)
    start_date = get_watermark(bq_client, PROJECT_ID, args.bq_table)
    try:
        bq_client.get_table(f"{PROJECT_ID}.{args.bq_table}")
        write_disposition = "merge"
    except gcloud_exceptions.NotFound:
        write_disposition = "append"

    pipeline = dlt.pipeline(
        pipeline_name="forex",
        destination=bigquery(
            location=LOCATION,
            project_id=PROJECT_ID,
        ),
        dataset_name=dataset_name,
    )

    # Only download today if after the cut off time
    now_utc = dt.datetime.now(dt.timezone.utc)
    if now_utc.time() >= CUTOFF_TIME:
        end_date = now_utc.date()
    else:
        end_date = now_utc.date() - dt.timedelta(days=1)

    counter = {"rows": 0}
    pipeline.run(
        rates_resource(iso_codes, start_date, end_date, counter),
        write_disposition=write_disposition,
    )
    print(f"Loaded {counter['rows']} rows into {dataset_name}.rates")


if __name__ == "__main__":
    main()
