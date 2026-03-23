# gcp_client_whitelist

Stack scaffold for the real fixed-egress client whitelist demand.

Target scenario:

- Cloud Run / Cloud Functions 1st gen outbound calls
- fixed egress via Cloud NAT
- client-side IP allowlist based on reserved static egress IP

Before apply in a corporate setup, provide actual values for project, region, network/subnetwork strategy, and authentication flow.
