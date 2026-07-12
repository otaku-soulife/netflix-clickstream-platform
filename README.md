# Netflix Clickstream Platform

An enterprise-style, real-time lakehouse on **Azure + Databricks**, built from
synthetic clickstream data. Every phase ships as its own branch and pull
request, exercised by CI, so the repo doubles as a portfolio of the data /ML
engineering workflow end to end.

Producer -> Event Hubs (Kafka) -> Databricks streaming -> Delta medallion -> ML.

## Architecture

```
generate_events (Mockingbird, containerized)
        |  Kafka protocol
        v
Azure Event Hubs  -- streaming bus (decouples producers/consumers)
        |
        v
Databricks Structured Streaming ---> Bronze (raw Delta)
        |
        v  Delta Live Tables (clean, dedup on event_id, quality checks)
   Silver ---> Gold (features / aggregates)
        |
        v
MLflow: features -> train -> registry -> batch scoring -> monitoring
```

Governance: Unity Catalog. Secrets: Azure Key Vault. IaC: Terraform +
Databricks Asset Bundles. CI/CD: GitHub Actions with OIDC (no stored passwords).

## Repo layout

```
infra/        Terraform - Azure resources (RG, ADLS, Event Hubs, KV, Databricks)
producer/     Containerized event generator            (Phase 2)
databricks/   Notebooks, DLT pipelines, Asset Bundle    (Phase 3-5)
ml/           Feature, training, scoring, monitoring    (Phase 6)
.github/      CI workflows, PR template, CODEOWNERS
docs/         Setup and runbooks
```

## How work flows (branch -> PR -> CI -> main)

Each phase is a branch, a PR, and a green CI run before it merges. See
`CONTRIBUTING.md` for the full workflow and `docs/SETUP-GITHUB.md` for repo,
branch-protection, OIDC, and remote-state setup.

| Phase | Deliverable                                   | Branch                  | CI that gates it     |
|-------|-----------------------------------------------|-------------------------|----------------------|
| 0     | Local tooling + `az login`                    | (local, no PR)          | -                    |
| 1     | Azure infra via Terraform                     | `infra/foundation`      | `terraform`          |
| GH    | Repo, branch protection, OIDC, remote state   | `chore/github-setup`    | `terraform`, `lint`  |
| 2     | Containerized producer -> Event Hubs (ACI)    | `feat/producer`         | `lint`               |
| 3     | Bronze streaming ingest                       | `pipeline/bronze`       | `lint`               |
| 4     | Silver/Gold DLT + data-quality expectations   | `pipeline/silver-gold`  | `lint`               |
| 5     | Databricks Asset Bundle + deploy workflow     | `infra/asset-bundle`    | `terraform`, `lint`  |
| 6     | ML loop: features -> MLflow -> scoring -> mon. | `ml/clickstream-model`  | `lint`               |

Merges to `main` trigger the deploy steps (Terraform apply / bundle deploy),
optionally gated by a protected `production` Environment.

## Quickstart

```powershell
# Phase 0 - tooling
winget install Microsoft.AzureCLI Hashicorp.Terraform GitHub.cli
az login
gh auth login

# Get the code into GitHub (see docs/SETUP-GITHUB.md for details)
git init -b main && git add . && git commit -m "chore: scaffold platform"
gh repo create netflix-clickstream-platform --private --source=. --push

# Phase 1 - provision infra (ideally via a PR so CI runs the plan)
cd infra && terraform init && terraform plan
```

## Cost guardrails ($200 free credit)

- Set a budget alert: Azure Portal -> Cost Management -> Budgets ($50 / $150).
- Keep Databricks compute small/serverless with auto-terminate; the workspace
  is free to exist and billed only while compute runs.
- Stop **all** billing when idle: `cd infra && terraform destroy`.

## Docs

- `CONTRIBUTING.md` - branch/PR/commit workflow and local checks
- `docs/SETUP-GITHUB.md` - repo, branch protection, OIDC federation, remote state
