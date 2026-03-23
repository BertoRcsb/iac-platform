variable "project_id" {
  description = "GCP project ID where resources are managed."
  type        = string
}

variable "region" {
  description = "GCP region for regional resources."
  type        = string
}

variable "name_prefix" {
  description = "Prefix used when resource names are not provided."
  type        = string
  default     = "client-whitelist"
}

variable "create_network" {
  description = "Whether to create a VPC network in this module."
  type        = bool
  default     = false
}

variable "network_name" {
  description = "Optional network name when create_network is true."
  type        = string
  default     = null
}

variable "existing_network_name" {
  description = "Existing network name used when create_network is false."
  type        = string
  default     = null

  validation {
    condition     = var.create_network || try(trimspace(var.existing_network_name) != "", false)
    error_message = "existing_network_name is required when create_network is false."
  }
}

variable "create_subnetwork" {
  description = "Whether to create a subnetwork in this module."
  type        = bool
  default     = false
}

variable "subnetwork_name" {
  description = "Optional subnetwork name when create_subnetwork is true."
  type        = string
  default     = null
}

variable "existing_subnetwork_name" {
  description = "Existing subnetwork name used when create_subnetwork is false."
  type        = string
  default     = null

  validation {
    condition     = var.create_subnetwork || try(trimspace(var.existing_subnetwork_name) != "", false)
    error_message = "existing_subnetwork_name is required when create_subnetwork is false."
  }
}

variable "subnetwork_ip_cidr_range" {
  description = "CIDR used when creating the subnetwork."
  type        = string
  default     = "10.42.0.0/24"
}

variable "nat_ip_name" {
  description = "Optional static external IP resource name for NAT."
  type        = string
  default     = null
}

variable "router_name" {
  description = "Optional Cloud Router name."
  type        = string
  default     = null
}

variable "nat_name" {
  description = "Optional Cloud NAT name."
  type        = string
  default     = null
}

variable "connector_name" {
  description = "Optional Serverless VPC Access Connector name."
  type        = string
  default     = null
}

variable "connector_ip_cidr_range" {
  description = "CIDR block for the Serverless VPC Access Connector."
  type        = string
  default     = "10.42.16.0/28"
}

variable "connector_min_throughput" {
  description = "Minimum throughput in Mbps for the VPC Access Connector."
  type        = number
  default     = 200
}

variable "connector_max_throughput" {
  description = "Maximum throughput in Mbps for the VPC Access Connector."
  type        = number
  default     = 300
}
