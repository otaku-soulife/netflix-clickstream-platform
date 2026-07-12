terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstate276350"
    container_name       = "tfstate"
    key                  = "netflix-clickstream.tfstate"
  }
}
