variable "project_id" {
  description = "Target GCP project ID."
  type        = string
}

variable "region" {
  description = "Target GCP region."
  type        = string
}

variable "name_prefix" {
  description = "Resource naming prefix for this environment."
  type        = string
  default     = "client-whitelist"
}

variable "create_network" {
  description = "Whether to create VPC network resources in this environment."
  type        = bool
  default     = false
}

variable "network_name" {
  description = "Optional network name when create_network is true."
  type        = string
  default     = null
}

variable "existing_network_name" {
  description = "Existing VPC network name when create_network is false."
  type        = string
  default     = null
}

variable "create_subnetwork" {
  description = "Whether to create subnetwork resources in this environment."
  type        = bool
  default     = false
}

variable "subnetwork_name" {
  description = "Optional subnetwork name when create_subnetwork is true."
  type        = string
  default     = null
}

variable "existing_subnetwork_name" {
  description = "Existing subnetwork name when create_subnetwork is false."
  type        = string
  default     = null
}

variable "subnetwork_ip_cidr_range" {
  description = "CIDR range when creating the subnetwork."
  type        = string
  default     = "10.42.0.0/24"
}

variable "nat_ip_name" {
  description = "Optional static NAT IP resource name."
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
  description = "CIDR block for the VPC Access Connector."
  type        = string
  default     = "10.42.16.0/28"
}

variable "connector_min_throughput" {
  description = "Minimum connector throughput in Mbps."
  type        = number
  default     = 200
}

variable "connector_max_throughput" {
  description = "Maximum connector throughput in Mbps."
  type        = number
  default     = 300
}
