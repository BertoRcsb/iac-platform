# gcp-client-whitelist environment

Scaffold environment for the real fixed-egress client whitelist use case.

## Purpose

- Support serverless outbound calls (Cloud Run or Cloud Functions 1st gen).
- Route outbound traffic through Cloud NAT.
- Publish a static egress IP to external clients for allowlisting.

## Values to provide before apply

- `project_id`
- `region`
- network/subnetwork strategy:
  - existing (`existing_network_name`, `existing_subnetwork_name`)
  - or creation (`create_network=true`, `create_subnetwork=true`)
- corporate authentication and authorization setup

## Important notes

- Backend and credentials are intentionally not hardcoded.
- This scaffold is safe by default and meant for later corporate values.
