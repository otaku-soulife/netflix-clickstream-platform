##############################################
# Netflix Clickstream Platform - Phase 1 infra
# Provisions the Azure foundation for the lakehouse:
#   Resource Group, ADLS Gen2, Event Hubs (Kafka),
#   Key Vault, Databricks workspace, UC access connector
##############################################

terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

# Random suffix keeps globally-unique names (storage, key vault) from colliding
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  suffix = random_string.suffix.result
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# ---------------- ADLS Gen2 (lakehouse storage) ----------------
resource "azurerm_storage_account" "lake" {
  name                     = "stnetflix${local.suffix}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true # hierarchical namespace = ADLS Gen2
}

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.lake.name
  container_access_type = "private"
}

# ---------------- Event Hubs (Kafka-compatible streaming bus) ----------------
# Standard tier is required for the Kafka protocol and >1 consumer group.
resource "azurerm_eventhub_namespace" "ehns" {
  name                = "ehns-netflix-${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  capacity            = 1 # 1 throughput unit; plenty for this project
}

resource "azurerm_eventhub" "clickstream" {
  name                = "netflix-clickstream"
  namespace_name      = azurerm_eventhub_namespace.ehns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 2
  message_retention   = 1 # days
}

# Producer credential (Send). Consumers use their own rule / managed identity.
resource "azurerm_eventhub_authorization_rule" "producer" {
  name                = "producer"
  namespace_name      = azurerm_eventhub_namespace.ehns.name
  eventhub_name       = azurerm_eventhub.clickstream.name
  resource_group_name = azurerm_resource_group.rg.name
  listen              = true
  send                = true
  manage              = false
}

# ---------------- Key Vault (secrets) ----------------
resource "azurerm_key_vault" "kv" {
  name                       = "kv-netflix-${local.suffix}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  # Access-policy model so the Databricks KV-backed secret scope wizard works cleanly
  access_policy {
    tenant_id          = data.azurerm_client_config.current.tenant_id
    object_id          = data.azurerm_client_config.current.object_id
    secret_permissions = ["Get", "List", "Set", "Delete", "Purge", "Recover"]
  }
}

# Store the Event Hubs producer connection string for the containerized generator
resource "azurerm_key_vault_secret" "eh_conn" {
  name         = "eventhub-producer-connection"
  value        = azurerm_eventhub_authorization_rule.producer.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

# ---------------- Azure Databricks workspace ----------------
# premium SKU is required for Unity Catalog features.
resource "azurerm_databricks_workspace" "dbx" {
  name                = "dbx-netflix-${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "premium"
}

# ---------------- Unity Catalog storage access ----------------
# Managed identity Databricks uses to read/write ADLS for UC external locations.
resource "azurerm_databricks_access_connector" "uc" {
  name                = "dbx-uc-connector"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_role_assignment" "uc_storage" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.uc.identity[0].principal_id
}
