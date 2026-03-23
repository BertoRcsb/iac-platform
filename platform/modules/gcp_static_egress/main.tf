terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

locals {
  desired_network_name    = coalesce(var.network_name, "${var.name_prefix}-vpc")
  desired_subnetwork_name = coalesce(var.subnetwork_name, "${var.name_prefix}-subnet")
  desired_router_name     = coalesce(var.router_name, "${var.name_prefix}-router")
  desired_nat_name        = coalesce(var.nat_name, "${var.name_prefix}-nat")
  desired_nat_ip_name     = coalesce(var.nat_ip_name, "${var.name_prefix}-nat-ip")
  desired_connector_name  = coalesce(var.connector_name, "${var.name_prefix}-connector")
}

data "google_compute_network" "existing" {
  count   = var.create_network ? 0 : 1
  name    = var.existing_network_name
  project = var.project_id
}

resource "google_compute_network" "this" {
  count                   = var.create_network ? 1 : 0
  project                 = var.project_id
  name                    = local.desired_network_name
  auto_create_subnetworks = false
}

locals {
  network_name      = var.create_network ? google_compute_network.this[0].name : data.google_compute_network.existing[0].name
  network_self_link = var.create_network ? google_compute_network.this[0].self_link : data.google_compute_network.existing[0].self_link
}

data "google_compute_subnetwork" "existing" {
  count   = var.create_subnetwork ? 0 : 1
  name    = var.existing_subnetwork_name
  region  = var.region
  project = var.project_id
}

resource "google_compute_subnetwork" "this" {
  count                    = var.create_subnetwork ? 1 : 0
  project                  = var.project_id
  region                   = var.region
  name                     = local.desired_subnetwork_name
  ip_cidr_range            = var.subnetwork_ip_cidr_range
  network                  = local.network_self_link
  private_ip_google_access = true
}

locals {
  subnetwork_name      = var.create_subnetwork ? google_compute_subnetwork.this[0].name : data.google_compute_subnetwork.existing[0].name
  subnetwork_self_link = var.create_subnetwork ? google_compute_subnetwork.this[0].self_link : data.google_compute_subnetwork.existing[0].self_link
}

resource "google_compute_address" "nat_ip" {
  project = var.project_id
  region  = var.region
  name    = local.desired_nat_ip_name
}

resource "google_compute_router" "this" {
  project = var.project_id
  region  = var.region
  name    = local.desired_router_name
  network = local.network_self_link
}

resource "google_compute_router_nat" "this" {
  project                            = var.project_id
  region                             = var.region
  name                               = local.desired_nat_name
  router                             = google_compute_router.this.name
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = [google_compute_address.nat_ip.self_link]
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_vpc_access_connector" "this" {
  project        = var.project_id
  region         = var.region
  name           = local.desired_connector_name
  network        = local.network_name
  ip_cidr_range  = var.connector_ip_cidr_range
  min_throughput = var.connector_min_throughput
  max_throughput = var.connector_max_throughput
}
