#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI app with Google API Gateway extensions.

This script:
1. Extracts the OpenAPI spec from the FastAPI app
2. Adds Google-specific extensions for API Gateway
3. Adds rate limiting configuration
4. Converts OpenAPI 3.1.0 to 3.0.3 for better compatibility
5. Outputs as YAML

Usage:
    uv run python scripts/generate_openapi.py [--rate-limit REQUESTS_PER_HOUR]

Examples:
    uv run python scripts/generate_openapi.py                # Default: 100/hour
    uv run python scripts/generate_openapi.py --rate-limit 50
    uv run python scripts/generate_openapi.py --rate-limit 1000
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app


def generate_openapi_spec(rate_limit: int = 100) -> dict:
    """Generate OpenAPI spec with Google API Gateway extensions."""
    # Get the base OpenAPI spec from FastAPI
    spec = app.openapi()

    # Convert OpenAPI 3.1.0 to 3.0.3 for better compatibility with API Gateway
    spec["openapi"] = "3.0.3"

    # Update info section
    spec["info"]["version"] = "1.0.0"
    spec["info"]["description"] = (
        "Public API for forex trade weighted index (TWI) data. "
        "Data sourced from Frankfurter API and processed with dbt in BigQuery."
    )

    # Add Google-specific backend configuration
    # The backend_url will be templated by Terraform
    spec["x-google-backend"] = {
        "address": "${backend_url}",
        "protocol": "h2",
    }

    # Add rate limiting configuration
    spec["x-google-management"] = {
        "metrics": [
            {
                "name": "read-requests",
                "valueType": "INT64",
                "metricKind": "DELTA",
            }
        ],
        "quota": {
            "limits": [
                {
                    "name": "read-limit",
                    "metric": "read-requests",
                    "unit": "1/h/{project}",
                    "values": {"STANDARD": rate_limit},
                }
            ]
        },
    }

    # Add quota to each endpoint
    for path_data in spec.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "operationId" in operation:
                operation["x-google-quota"] = {
                    "metricCosts": {"read-requests": 1}
                }

    return spec


def main():
    """Generate and save the OpenAPI spec."""
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI spec with Google API Gateway extensions"
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=100,
        help="Rate limit in requests per hour (default: 100)",
    )
    args = parser.parse_args()

    spec = generate_openapi_spec(rate_limit=args.rate_limit)

    # Write as YAML
    output_path = Path(__file__).parent.parent / "openapi.yaml"
    with open(output_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✓ Generated OpenAPI spec at {output_path}")
    print(f"  - OpenAPI version: {spec['openapi']}")
    print(f"  - API version: {spec['info']['version']}")
    print(f"  - Endpoints: {len(spec['paths'])}")
    print(f"  - Rate limit: {args.rate_limit} requests/hour per project")


if __name__ == "__main__":
    main()
