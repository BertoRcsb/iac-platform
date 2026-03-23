output "network_name" {
  description = "Effective VPC network name used by this module."
  value       = local.network_name
}

output "subnetwork_name" {
  description = "Effective subnetwork name used by this module."
  value       = local.subnetwork_name
}

output "connector_name" {
  description = "Serverless VPC Access Connector name."
  value       = google_vpc_access_connector.this.name
}

output "nat_ip_address" {
  description = "Reserved static egress IP address from Cloud NAT."
  value       = google_compute_address.nat_ip.address
}

output "router_name" {
  description = "Cloud Router name."
  value       = google_compute_router.this.name
}

output "nat_name" {
  description = "Cloud NAT name."
  value       = google_compute_router_nat.this.name
}

output "network_self_link" {
  description = "VPC network self link."
  value       = local.network_self_link
}

output "subnetwork_self_link" {
  description = "Subnetwork self link."
  value       = local.subnetwork_self_link
}
