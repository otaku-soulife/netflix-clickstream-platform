output "databricks_workspace_url" {
  description = "Open this to reach your workspace."
  value       = "https://${azurerm_databricks_workspace.dbx.workspace_url}"
}

output "storage_account_name" {
  value = azurerm_storage_account.lake.name
}

output "bronze_container" {
  value = azurerm_storage_container.bronze.name
}

output "eventhub_namespace" {
  value = azurerm_eventhub_namespace.ehns.name
}

output "eventhub_name" {
  value = azurerm_eventhub.clickstream.name
}

output "key_vault_name" {
  value = azurerm_key_vault.kv.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.kv.vault_uri
}

# Needed later when you create the Unity Catalog storage credential
output "uc_access_connector_id" {
  value = azurerm_databricks_access_connector.uc.id
}
