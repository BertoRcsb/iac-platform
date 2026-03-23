terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

module "static_egress" {
  source = "../../modules/gcp_static_egress"

  project_id               = var.project_id
  region                   = var.region
  name_prefix              = var.name_prefix
  create_network           = var.create_network
  network_name             = var.network_name
  existing_network_name    = var.existing_network_name
  create_subnetwork        = var.create_subnetwork
  subnetwork_name          = var.subnetwork_name
  existing_subnetwork_name = var.existing_subnetwork_name
  subnetwork_ip_cidr_range = var.subnetwork_ip_cidr_range
  nat_ip_name              = var.nat_ip_name
  router_name              = var.router_name
  nat_name                 = var.nat_name
  connector_name           = var.connector_name
  connector_ip_cidr_range  = var.connector_ip_cidr_range
  connector_min_throughput = var.connector_min_throughput
  connector_max_throughput = var.connector_max_throughput
}
