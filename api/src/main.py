import datetime as dt
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from google.cloud import bigquery
from google.cloud.bigquery.table import Row

app = FastAPI(title="Forex TWI API")


def _project_id() -> str | None:
    return os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv(
        "GCP_PROJECT"
    )


def _table_ref() -> str:
    dataset = os.getenv("BQ_DATASET", "presentation")
    table = os.getenv("BQ_TWI_TABLE", "twi")
    project = _project_id()
    if project:
        return f"{project}.{dataset}.{table}"
    return f"{dataset}.{table}"


def _client() -> bigquery.Client:
    return bigquery.Client(project=_project_id())


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _serialize_row(row: Row) -> dict[str, Any]:
    return {key: _serialize_value(value) for key, value in dict(row).items()}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/twi/latest")
def twi_latest(base_iso: str = "EUR") -> dict[str, Any]:
    table_ref = _table_ref()
    sql = f"""
        select base_iso, date, rate
        from `{table_ref}`
        where base_iso = @base_iso
        order by date desc
        limit 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
        ]
    )
    rows = list(_client().query(sql, job_config=job_config).result())
    if not rows:
        raise HTTPException(status_code=404, detail="No data found")
    return _serialize_row(rows[0])


@app.get("/twi")
def twi(
    base_iso: str = "EUR",
    date: dt.date | None = None,
    start: dt.date | None = None,
    end: dt.date | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    table_ref = _table_ref()
    if date:
        if start or end:
            raise HTTPException(
                status_code=400, detail="date cannot be combined with start or end"
            )
        sql = f"""
            select base_iso, date, rate
            from `{table_ref}`
            where base_iso = @base_iso and date = @date
            limit 1
        """
        params = [
            bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
            bigquery.ScalarQueryParameter("date", "DATE", date),
        ]
    else:
        if start and end:
            sql = f"""
                select base_iso, date, rate
                from `{table_ref}`
                where base_iso = @base_iso and date between @start and @end
                order by date
                limit @limit
            """
            params = [
                bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
                bigquery.ScalarQueryParameter("start", "DATE", start),
                bigquery.ScalarQueryParameter("end", "DATE", end),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]
        elif start or end:
            raise HTTPException(
                status_code=400, detail="start and end must be provided together"
            )
        else:
            sql = f"""
                select base_iso, date, rate
                from `{table_ref}`
                where base_iso = @base_iso
                order by date desc
                limit @limit
            """
            params = [
                bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    rows = _client().query(sql, job_config=job_config).result()
    return [_serialize_row(row) for row in rows]
