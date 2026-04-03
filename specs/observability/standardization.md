# Spec: Observability Standardization

## Objective
Standardize observability across services using platform-observability-core.

## Requirements
- Use standardized Dockerfile and entrypoint
- Support Cloud Run PORT
- Support Datadog integration
- No hardcoded secrets
- Respect K_REVISION and ASPNETCORE_ENVIRONMENT

## Expected Outcome
Services follow the same observability contract and can be validated consistently.
