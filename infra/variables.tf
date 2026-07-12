variable "resource_group_name" {
  type        = string
  description = "Resource group that will hold all project resources."
  default     = "rg-netflix-clickstream"
}

variable "location" {
  type        = string
  description = "Azure region. eastus is low-cost and has broad service support."
  default     = "eastus"
}
