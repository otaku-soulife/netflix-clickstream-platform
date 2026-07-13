# Azure Resource Reference

Every resource we created, where to find it in the Azure Portal, and where it's
defined in code. Two buckets: **Terraform-managed** (edit the file + merge a PR)
and **hand-created bootstrap** (made once with `az`, not in any file).

Portal tip: use the top search bar - type any resource name to jump to it.

Two resource groups:
- `rg-netflix-clickstream` - the platform (Terraform)
- `rg-tfstate` - the Terraform state store (hand-created)

VS Code tip: open `infra/main.tf`, press Ctrl+F, search the block name below.

---

## Bucket 1 - Terraform-managed  (lives in `rg-netflix-clickstream`, defined in `infra/main.tf`)

| # | Resource | Name pattern | Find in Portal | Code (search in main.tf) |
|---|----------|--------------|----------------|--------------------------|
| 1 | Resource group | `rg-netflix-clickstream` | Resource groups -> rg-netflix-clickstream | `azurerm_resource_group` "rg" |
| 2 | Storage account (data lake) | `stnetflix...` | RG -> the storage account | `azurerm_storage_account` "lake" |
| 3 | Bronze container | `bronze` | Storage acct -> Data storage -> Containers | `azurerm_storage_container` "bronze" |
| 4 | Event Hubs namespace | `ehns-netflix-...` | RG -> the namespace | `azurerm_eventhub_namespace` "ehns" |
| 5 | Event hub | `netflix-clickstream` | Namespace -> Entities -> Event Hubs | `azurerm_eventhub` "clickstream" |
| 6 | Producer access rule | `producer` | Event hub -> Shared access policies | `azurerm_eventhub_authorization_rule` "producer" |
| 7 | Key Vault | `kv-netflix-...` | RG -> the key vault | `azurerm_key_vault` "kv" |
| 8 | Vault secret | `eventhub-producer-connection` | Key Vault -> Objects -> Secrets | `azurerm_key_vault_secret` "eh_conn" |
| 9 | Databricks workspace | `dbx-netflix-...` | RG -> the workspace -> Launch Workspace | `azurerm_databricks_workspace` "dbx" |
| 10 | UC access connector | `dbx-uc-connector` | RG -> the access connector | `azurerm_databricks_access_connector` "uc" |
| 11 | Connector role grant | Storage Blob Data Contributor | Storage acct -> Access control (IAM) -> Role assignments | `azurerm_role_assignment` "uc_storage" |
| - | Name suffix generator | (not an Azure resource) | n/a | `random_string` "suffix" |

Note: Azure also auto-creates a `databricks-rg-...` group for the workspace's
internals. You don't manage it; leave it alone.

---

## Bucket 2 - Hand-created bootstrap  (no file; made with `az`)

| # | Thing | Name | Find in Portal | How it was created |
|---|-------|------|----------------|--------------------|
| A | State resource group | `rg-tfstate` | Resource groups -> rg-tfstate | `az group create` (Step 9) |
| B | State storage account | `sttfstate...` | rg-tfstate -> storage account | `az storage account create` (Step 9) |
| C | State file (blob) | `netflix-clickstream.tfstate` | State storage -> Containers -> tfstate | written by `terraform apply`; pointer is `infra/backend.tf` |
| D | CI app registration | `gh-netflix-clickstream` | Microsoft Entra ID -> App registrations | `az ad app create` (Step 7) |
| E | Federated credentials | `gh-main`, `gh-pr` | App reg -> Certificates & secrets -> Federated credentials | `az ad app federated-credential create` (Step 7) |
| F | CI role: Contributor | on subscription | Subscription -> Access control (IAM) -> Role assignments | `az role assignment create` (Step 7) |
| G | CI role: User Access Admin | on subscription | Subscription -> Access control (IAM) -> Role assignments | `az role assignment create` (fix step) |

---

## Quick verify commands

```powershell
# Everything Terraform built
az resource list -g rg-netflix-clickstream -o table

# Terraform's own output values (workspace URL, names)
cd infra; terraform output; cd ..

# The CI identity and its trust
az ad app list --display-name "gh-netflix-clickstream" -o table
az ad app federated-credential list --id <appId> -o table
az role assignment list --assignee <appId> -o table
```

---

## Mental model

**In `main.tf` -> Terraform owns it** (change via PR, remove via `terraform destroy`).
**Made with `az` -> bootstrap** (change or delete by hand). You always need a
little bootstrap - an identity + a state store - before Terraform can manage
the rest.
