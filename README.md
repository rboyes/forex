# Foreign exchange DBT project in Google Cloud/BigQuery
[![daily pipeline](https://img.shields.io/github/actions/workflow/status/rboyes/forex/daily-pipeline.yml?style=flat-square&label=daily%20pipeline&logo=github)](https://github.com/rboyes/forex/actions/workflows/daily-pipeline.yml) [![dbt docs](https://img.shields.io/github/actions/workflow/status/rboyes/forex/dbt-docs.yml?style=flat-square&label=dbt%20docs&logo=github)](https://github.com/rboyes/forex/actions/workflows/dbt-docs.yml)

Daily pipeline that pulls historical FX rates from Frankfurter, loads them into
BigQuery staging, and builds presentation models (rates + TWI = trade weighted index) with dbt. 
Runs via GitHub Actions and keeps incremental history by date.

```mermaid
flowchart LR
  A[Frankfurter API] --> B[Downloader dlt]
  B --> C[BigQuery staging.rates]
  C --> D[dbt models]
  S[dbt twi seeds] --> D
  D --> E[BigQuery presentation.rates]
  D --> F[BigQuery presentation.twi]
  F --> G[Cloud Run API]
```

DBT documents are located at [dbt docs](https://rboyes.github.io/forex).

## Google cloud setup

- Google cloud project created - call it forex-20260115
  ```bash
  gcloud projects create forex-20260115 --name="forex"
  ```
- Install terraform
- Google cloud admin service account created for project deployment - call it terraform-runner
  ```bash
  # Create service account
  gcloud iam service-accounts create terraform-runner \
    --project forex-20260115 \
    --display-name "Terraform runner"

  # Grant full project permissions (broad)
  gcloud projects add-iam-policy-binding forex-20260115 \
    --member "serviceAccount:terraform-runner@forex-20260115.iam.gserviceaccount.com" \
    --role "roles/owner"

  # Storage bucket to maintain state
  gcloud storage buckets create gs://forex-20260115-tfstate \
    --project=forex-20260115 \
    --location=europe-west2 \
    --uniform-bucket-level-access

  # Enable versioning on the bucket
  gcloud storage buckets update gs://forex-20260115-tfstate --versioning

  # Enable the resource manager API
  gcloud services enable cloudresourcemanager.googleapis.com --project=forex-20260115
  ```
- Create a local key for the terraform storage account, if you want to deploy locally
  ```
  gcloud iam service-accounts keys create ./terraform-runner.json \
    --iam-account "terraform-runner@forex-20260115.iam.gserviceaccount.com"
  chmod 600 terraform-runner.json
  export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/terraform-runner.json
  cd infra/terraform
  terraform init
  terraform apply
  ```

## GitHub Actions (Terraform via Workload Identity)

The Terraform workflow is manual-only. Configure Workload Identity and set GitHub secrets:

```bash
PROJECT_ID=forex-20260115
POOL_ID=github-pool
PROVIDER_ID=github-provider

gcloud iam workload-identity-pools create $POOL_ID \
  --project $PROJECT_ID \
  --location global \
  --display-name "GitHub Actions pool"

gcloud iam workload-identity-pools providers create-oidc $PROVIDER_ID \
  --project $PROJECT_ID \
  --location global \
  --workload-identity-pool $POOL_ID \
  --display-name "GitHub Actions provider" \
  --issuer-uri "https://token.actions.githubusercontent.com" \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition "assertion.repository=='rboyes/forex'"
```
Add GitHub repo secrets:
- `GCP_WIF_PROVIDER`: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID`
- `GCP_WIF_SERVICE_ACCOUNT`: `terraform-runner@forex-20260115.iam.gserviceaccount.com`
- `GCP_DBT_WIF_SERVICE_ACCOUNT`: `dbt-runner@forex-20260115.iam.gserviceaccount.com`

## Running DBT locally

```bash
# Create a local key so you can execute as the dbt service account
gcloud iam service-accounts keys create ./dbt/dbt-runner.json \
  --iam-account "dbt-runner@forex-20260115.iam.gserviceaccount.com"
chmod 600 dbt/dbt-runner.json
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/dbt/dbt-runner.json
```

```bash
cd dbt
uv sync
uv run scripts/downloader.py
uv run dbt run --project-dir . --profiles-dir .
```

## API

FastAPI service that serves TWI data from BigQuery.
Defaults to dataset `presentation` and table `twi`, and uses `BQ_PROJECT_ID` if set.

```bash
cd api
uv sync
gcloud auth application-default login
uv run uvicorn src.main:app --reload --port 8000
```

Example requests:

```bash
curl "http://localhost:8000/twi/latest"
curl "http://localhost:8000/twi?date=2026-01-20"
curl "http://localhost:8000/twi?start=2026-01-18&end=2026-01-22"
```

Production (Cloud Run, private):

```bash
URL=$(gcloud run services describe forex-api --region europe-west2 --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token --audiences="$URL" \
  --impersonate-service-account=api-invoker@forex-20260115.iam.gserviceaccount.com)
curl -H "Authorization: Bearer $TOKEN" "$URL/twi/latest"
```


## Developer tooling - linting, formatting and type checking

```bash
cd api
uv run ruff check .
uv run ruff format .
uv run ty check .
```
