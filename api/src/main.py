import datetime as dt
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from google.cloud import bigquery
from google.cloud.bigquery.table import Row

app = FastAPI(title="Forex TWI API")

PROJECT_ID = "forex-20260115"
TABLE = f"{PROJECT_ID}.presentation.twi"

_bq_client = bigquery.Client(project=PROJECT_ID)


def _serialize_row(row: Row) -> dict[str, Any]:
    
    serialized_row = {}
    for key, value in dict(row).items():
        if hasattr(value, "isoformat") and callable(value.isoformat):
            serialized_row[key] = value.isoformat()
        else:
            serialized_row[key] = value
    return serialized_row

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/twi/latest")
def twi_latest(base_iso: str = "EUR") -> dict[str, Any]:
    sql = f"""
        select base_iso, date, rate
        from `{TABLE}`
        where base_iso = @base_iso
        order by date desc
        limit 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
        ]
    )
    rows = list(_bq_client.query(sql, job_config=job_config).result())
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
    if date and (start or end):
        raise HTTPException(
            status_code=400, detail="date cannot be combined with start or end"
        )
    if start and end:
        sql = f"""
            select base_iso, date, rate
            from `{TABLE}`
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
    elif date:
        sql = f"""
            select base_iso, date, rate
            from `{TABLE}`
            where base_iso = @base_iso and date = @date
            limit 1
        """
        params = [
            bigquery.ScalarQueryParameter("base_iso", "STRING", base_iso),
            bigquery.ScalarQueryParameter("date", "DATE", date),
        ]
    else:
        raise HTTPException(status_code=400, detail="invalid parameters")

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    rows = _bq_client.query(sql, job_config=job_config).result()
    return [_serialize_row(row) for row in rows]
