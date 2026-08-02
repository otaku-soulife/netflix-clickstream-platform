# Skills Log

A running record of the engineering skills demonstrated while building this
platform - for interview prep, resume bullets, and the portfolio README.
Each skill has three lenses: technical, plain-English, and why it gets you hired.

Updated through: Phase 2 (event producer).

---

## Foundation & Infrastructure (Phases 0-1)

### Infrastructure as Code (Terraform)
- **Technical:** Declared Azure resources (resource group, ADLS Gen2, Event Hubs,
  Key Vault, Databricks workspace, access connector) in HCL; managed the
  desired-state/plan/apply lifecycle with a remote azurerm backend.
- **Plain:** Wrote the cloud setup as code so it can be reviewed, repeated, and
  torn down identically - no manual clicking.
- **Why it hires you:** IaC is the standard for provisioning ML/data platforms;
  reproducible infra is expected in any serious data or ML engineering role.

### Remote state management
- **Technical:** Stored Terraform state in a locked Azure Storage backend so CI
  and local runs share one source of truth.
- **Plain:** Kept the system's "memory of what exists" in one shared, safe place
  instead of a file on one laptop.
- **Why it hires you:** Shows you understand team-scale infra, not just solo demos.

### Cloud identity, RBAC & secrets (Entra ID, Key Vault)
- **Technical:** Created app registrations/service principals, assigned scoped
  roles (Contributor, User Access Administrator), stored secrets in Key Vault,
  and debugged access-policy vs RBAC boundaries.
- **Plain:** Set up *who* is allowed to do *what*, and kept passwords out of code.
- **Why it hires you:** Identity and secrets handling are table stakes; leaked
  creds and over-broad permissions are top real-world failures.

---

## DevOps & CI/CD

### Trunk-based Git workflow (branch -> PR -> review -> merge)
- **Technical:** Short-lived branches, pull requests, required status checks,
  protected main, squash merges, Conventional Commits.
- **Plain:** Propose changes in a side copy, let robots check them, then fold
  them into the real thing - never edit production directly.
- **Why it hires you:** This is how every software/ML team ships; being fluent
  means productive on day one.

### CI/CD with GitHub Actions
- **Technical:** Workflows run lint + terraform plan on PRs and deploy on merge;
  handled path-filter vs required-check pitfalls.
- **Plain:** An automated assembly line that tests and ships changes for you.
- **Why it hires you:** CI/CD is the backbone of MLOps - the same pattern gates
  data pipelines and model deployments.

### Password-less cloud auth (OIDC federation)
- **Technical:** Federated GitHub Actions to Azure via short-lived OIDC tokens
  bound to the repo - no stored client secret.
- **Plain:** GitHub proves who it is with a temporary badge instead of a
  permanent password.
- **Why it hires you:** The current best practice for CI-to-cloud auth; signals
  security maturity most candidates lack.

### Code quality (ruff lint + format)
- **Technical:** Enforced linting/formatting, tuned via ruff.toml, fixed real
  findings (import order, timezone-naive datetime).
- **Plain:** Ran an automated style/grammar checker on the code and fixed it.
- **Why it hires you:** Teams enforce quality automatically; you can contribute
  without creating friction.

---

## Data Engineering (Phase 2)

### Streaming event producer (Python -> Event Hubs / Kafka)
- **Technical:** Batched JSON publishing to a Kafka-compatible partitioned log
  with graceful SIGTERM shutdown and env-driven config.
- **Plain:** A program that continuously drops realistic "someone watched
  something" events into a high-speed cloud mailbox.
- **Why it hires you:** Production AI is fed by streams; producing to and
  reasoning about a Kafka-style log is core to feeding models.

### Designing bounded, realistic synthetic data
- **Technical:** Modeled a fixed customer dimension with stable attributes and a
  finite catalog so events reference recurring keys (joins/aggregations/history).
- **Plain:** Made the same customers and titles recur so patterns can form.
- **Why it hires you:** The shape of the data determines what ML is possible;
  churn/recs need returning users - systems thinking, not just model calls.

### Reproducible Python environments
- **Technical:** Isolated dependencies in a venv, pinned versions in
  requirements.txt.
- **Plain:** Gave the project its own clean toolbox with exact tool versions.
- **Why it hires you:** Reproducibility is a first-class ML concern and the
  gateway to containerization.

---

## Resume bullets (draft)

- Built a reproducible Azure data platform with Terraform (IaC) and remote
  state, provisioned via CI/CD.
- Implemented password-less GitHub Actions -> Azure deploys using OIDC federation.
- Developed a Python streaming producer publishing synthetic clickstream events
  to Azure Event Hubs (Kafka-compatible).
- Enforced trunk-based development with PR review, automated lint/plan checks,
  and protected branches.
- Managed cloud identity, scoped RBAC roles, and Key Vault secrets across local
  and CI identities.

## Interview talking points

- Why streaming/Event Hubs decouples producers from consumers.
- Why OIDC federation is safer than storing a client secret.
- Why remote Terraform state matters once more than one actor runs apply.
- Why bounded synthetic data (fixed customers) is required for user-level ML.
- The RBAC lesson: "can use a service" != "can read its secrets."

## Coming next (to append)

- Phase 2 (cont.): Docker containerization, Azure Container Instances.
- Phase 3: Spark Structured Streaming -> Bronze Delta.
- Phase 4: Delta Live Tables, medallion architecture, data-quality expectations.
- Phase 5: Databricks Asset Bundles + CI deploy.
- Phase 6: MLflow, feature engineering, model registry, batch scoring, monitoring.

## Containerization & Image Delivery (Phase 2, cont.)

### Containerization (Docker)
- **Technical:** Authored a Dockerfile - pinned Python base, layered dependency
  install for build caching, non-root runtime user, defined entrypoint -
  producing an immutable, host-independent image.
- **Plain:** Packed the app and everything it needs into one sealed shipping
  container that runs the same anywhere.
- **Why it hires you:** Containers are the universal unit of ML deployment
  (training jobs, inference services, data producers). Writing a clean
  Dockerfile is a baseline expectation.

### Private container registry (Azure Container Registry)
- **Technical:** Provisioned ACR as code (Terraform) and published versioned,
  tagged images with identity-based access instead of admin passwords.
- **Plain:** Set up a private, secure, version-labeled warehouse for the
  containers.
- **Why it hires you:** Registries make every deploy traceable to an exact
  build - core to reproducible, auditable ML delivery.

### Build & publish images in CI (GitHub Actions)
- **Technical:** Workflow builds the image on every PR (validates the Dockerfile)
  and builds+pushes a tagged image to ACR on merge to main, authenticating via
  OIDC (no stored credentials).
- **Plain:** A robot assembly line test-builds the container on a proposal and
  files the final version in the warehouse on approval - hands-off.
- **Why it hires you:** This is the heart of MLOps - the same pipeline that
  ships a container ships a packaged model. Employers look for "can automate
  the build/deploy of ML artifacts."

### Troubleshooting a platform constraint
- **Technical:** Hit `TasksOperationsNotAllowed` (ACR Tasks disabled on the free
  tier) and pivoted from cloud-side build to a CI-runner build - same outcome,
  different mechanism.
- **Plain:** A blocked tool didn't stop the work; found an equally good route.
- **Why it hires you:** Real infra is full of quotas and disabled features;
  diagnosing and routing around them is what separates tutorial-followers from
  engineers who ship in messy environments.

### New resume bullets
- Containerized a Python streaming service with Docker (non-root, cache-optimized).
- Automated container image build/publish to Azure Container Registry via GitHub
  Actions with OIDC auth.
- Diagnosed and worked around a free-tier ACR Tasks restriction by moving the
  build to CI runners.

### New interview talking points
- Why containers guarantee "runs the same everywhere."
- Why building images in CI (vs by hand) is central to MLOps.
- The free-tier ACR Tasks limitation and how you routed around it.
