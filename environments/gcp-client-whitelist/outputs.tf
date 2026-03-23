output "connector_name" {
  description = "Serverless VPC Access Connector name."
  value       = module.gcp_client_whitelist.connector_name
}

output "nat_ip_address" {
  description = "Static egress IP address for client allowlists."
  value       = module.gcp_client_whitelist.nat_ip_address
}

output "router_name" {
  description = "Cloud Router name."
  value       = module.gcp_client_whitelist.router_name
}

output "network_name" {
  description = "Effective VPC network name used by this environment."
  value       = module.gcp_client_whitelist.network_name
}

output "subnetwork_name" {
  description = "Effective subnetwork name used by this environment."
  value       = module.gcp_client_whitelist.subnetwork_name
}
