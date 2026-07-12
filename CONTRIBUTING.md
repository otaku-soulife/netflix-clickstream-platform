# Contributing

This repo uses a trunk-based flow: `main` is always deployable, and all changes
land through reviewed pull requests with passing CI.

## Workflow

1. **Sync main**
   ```bash
   git checkout main && git pull
   ```
2. **Branch** - short-lived, prefixed by type:
   ```bash
   git checkout -b feat/bronze-ingest
   ```
   Prefixes: `feat/`, `fix/`, `infra/`, `pipeline/`, `ml/`, `docs/`, `chore/`.
3. **Commit** using Conventional Commits:
   ```
   feat: stream Event Hubs into bronze delta
   fix: dedup silver on event_id
   infra: add key vault secret for producer
   ```
4. **Open a PR** into `main`. Fill in the PR template and link the issue
   (`Closes #12`). Keep PRs small and single-purpose.
5. **CI must pass** - `terraform` (fmt/validate/plan) and `lint` (ruff) run
   automatically. Review the `terraform plan` in the PR for unexpected deletes.
6. **Review** - at least one approval, Code Owner review required.
7. **Squash-merge**. Delete the branch. Merges to `main` trigger deploy.

## Branch protection (enforced on `main`)

- PR required; no direct pushes or force-pushes
- Required checks: `terraform`, `lint`
- Branch up to date before merge
- Code Owner approval (`.github/CODEOWNERS`)

## Local checks before pushing

```bash
# Terraform
cd infra && terraform fmt -recursive && terraform validate

# Python
ruff check . && ruff format --check .
```

## Rules

- **Never commit secrets.** Tokens, connection strings, `*.tfvars`, and `.env`
  are gitignored - keep it that way. Secrets live in Azure Key Vault (runtime)
  and GitHub OIDC / Actions secrets (CI).
- Update docs when behavior changes.
- One logical change per PR.

See `docs/SETUP-GITHUB.md` for repo creation, OIDC federation, and remote state.
