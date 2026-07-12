# Enterprise GitHub setup

How this project uses GitHub the way a data platform team would: one repo,
trunk-based flow with protected `main`, PR review, CI on every PR, and
password-less deploys to Azure via OIDC.

## 1. Repo layout (monorepo)

```
netflix-clickstream-platform/
  infra/         Terraform (Azure resources)
  producer/      containerized event generator        (Phase 2)
  databricks/    notebooks, DLT, Asset Bundle          (Phase 3-5)
  ml/            features, training, scoring           (Phase 6)
  .github/       workflows, PR template, CODEOWNERS
  docs/
```

## 2. Create the repo and push

```powershell
cd netflix-clickstream-platform
git init -b main
git add .
git commit -m "chore: scaffold platform (infra + ci)"
gh repo create netflix-clickstream-platform --private --source=. --push
```

(Install GitHub CLI first: `winget install GitHub.cli`, then `gh auth login`.)

## 3. Branching model (trunk-based)

- `main` is always deployable and protected - no direct pushes.
- Work on short-lived branches: `feat/bronze-ingest`, `fix/dedup-key`.
- Open a PR -> CI runs -> review -> squash-merge to `main`.
- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.

## 4. Branch protection (Settings -> Branches -> Add rule for `main`)

- Require a pull request before merging (1 approval).
- Require status checks to pass: `terraform`, `lint`.
- Require branches to be up to date before merging.
- Require review from Code Owners (uses `.github/CODEOWNERS`).
- Do not allow bypassing / force-pushes.

## 5. Password-less Azure deploy (OIDC federation) - the enterprise standard

Instead of storing an Azure secret in GitHub, create an Entra app that GitHub
trusts via OIDC. Run in PowerShell/bash after `az login`:

```bash
appId=$(az ad app create --display-name "gh-netflix-clickstream" --query appId -o tsv)
az ad sp create --id $appId
subId=$(az account show --query id -o tsv)
tenId=$(az account show --query tenantId -o tsv)

# Least-privilege-ish: Contributor on the subscription (tighten to RG later)
az role assignment create --assignee $appId --role Contributor --scope /subscriptions/$subId

# Federated credentials: one for main pushes, one for PRs
az ad app federated-credential create --id $appId --parameters '{
  "name":"gh-main","issuer":"https://token.actions.githubusercontent.com",
  "subject":"repo:<OWNER>/<REPO>:ref:refs/heads/main",
  "audiences":["api://AzureADTokenExchange"]}'

az ad app federated-credential create --id $appId --parameters '{
  "name":"gh-pr","issuer":"https://token.actions.githubusercontent.com",
  "subject":"repo:<OWNER>/<REPO>:pull_request",
  "audiences":["api://AzureADTokenExchange"]}'

echo "AZURE_CLIENT_ID=$appId"
echo "AZURE_TENANT_ID=$tenId"
echo "AZURE_SUBSCRIPTION_ID=$subId"
```

Add those three as GitHub **repository secrets**
(Settings -> Secrets and variables -> Actions):
`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
No client secret is ever stored - GitHub exchanges a short-lived OIDC token.

## 6. Remote Terraform state (bootstrap once)

Local `.tfstate` doesn't work for a team or for CI. Create a dedicated state
store one time:

```bash
az group create -n rg-tfstate -l eastus
az storage account create -n sttfstate$RANDOM -g rg-tfstate -l eastus --sku Standard_LRS
# use the created name below and in infra/backend.tf
az storage container create -n tfstate --account-name <that-name>
```

Then rename `infra/backend.tf.example` -> `infra/backend.tf`, fill in the
storage account name, and run `terraform init -migrate-state`.

## 7. Environments (optional, for realism)

Create a `production` Environment (Settings -> Environments) with a required
reviewer. Gate the Terraform `Apply` and the Databricks deploy on it so merges
to `main` still need a human click before touching cloud resources.
