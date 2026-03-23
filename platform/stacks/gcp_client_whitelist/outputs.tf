output "network_name" {
  description = "Effective network name used by the stack."
  value       = module.static_egress.network_name
}

output "subnetwork_name" {
  description = "Effective subnetwork name used by the stack."
  value       = module.static_egress.subnetwork_name
}

output "connector_name" {
  description = "Serverless VPC Access Connector name."
  value       = module.static_egress.connector_name
}

output "nat_ip_address" {
  description = "Static egress IP address to share for client allowlisting."
  value       = module.static_egress.nat_ip_address
}

output "router_name" {
  description = "Cloud Router name."
  value       = module.static_egress.router_name
}

output "nat_name" {
  description = "Cloud NAT name."
  value       = module.static_egress.nat_name
}
