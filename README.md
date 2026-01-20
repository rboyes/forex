# Foreign exchange DBT project in Google Cloud/BigQuery

Basic API download and DBT transform using BigQuery + GCS.

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

## Run locally

Create a dbt runner key if you plan to run dbt locally:

```bash
gcloud iam service-accounts keys create ./dbt-runner.json \
  --iam-account "dbt-runner@forex-20260115.iam.gserviceaccount.com"
chmod 600 dbt-runner.json
```

Set credentials (use terraform-runner.json for Terraform, dbt-runner.json for dbt/downloader):

```bash
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/dbt-runner.json
```

```bash
uv run python downloader.py
uv run dbt run
```

Move processed JSON files out of incoming:

```bash
gcloud storage mv "gs://forex-20260115/json/incoming/*.json" gs://forex-20260115/json/processed/
```
