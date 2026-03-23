variable "project_id" {
  description = "GCP project ID for the client whitelist stack."
  type        = string
}

variable "region" {
  description = "GCP region where resources are created."
  type        = string
}

variable "name_prefix" {
  description = "Prefix used for resource naming when names are not explicitly set."
  type        = string
  default     = "client-whitelist"
}

variable "create_network" {
  description = "Whether this stack creates a VPC network."
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
  description = "Whether this stack creates a subnetwork."
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
  description = "Subnetwork CIDR when create_subnetwork is true."
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
  description = "CIDR block for the Serverless VPC Access Connector."
  type        = string
  default     = "10.42.16.0/28"
}

variable "connector_min_throughput" {
  description = "Minimum throughput for connector in Mbps."
  type        = number
  default     = 200
}

variable "connector_max_throughput" {
  description = "Maximum throughput for connector in Mbps."
  type        = number
  default     = 300
}
