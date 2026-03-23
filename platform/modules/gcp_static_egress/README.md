# gcp_static_egress

Scaffold module for fixed egress IP in GCP serverless workloads.

It models:

- optional VPC creation or existing VPC usage
- optional subnetwork creation or existing subnetwork usage
- regional static external IP
- Cloud Router
- Cloud NAT
- Serverless VPC Access Connector

This module is parameterized for corporate values and intentionally does not hardcode credentials, project IDs, or backend settings.
