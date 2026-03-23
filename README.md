# iac-platform

Local-first Terraform monorepo for platform engineering.

This repository is designed to start without any cloud account, while keeping a structure that scales to enterprise cloud usage. Infrastructure remains the source of truth through Terraform modules, stacks, and environments.

## Purpose

- Provide a pragmatic local lab for day-1 productivity.
- Standardize delivery with a single SDD method: `Research -> PRD -> Spec -> Code -> Review`.
- Keep Claude and Codex operating with the same workflow and shared standards.
- Scaffold the real GCP fixed-egress client whitelist scenario without hardcoded credentials.

## Repository architecture

- `platform/modules`: reusable infrastructure building blocks.
- `platform/stacks`: composable root interfaces per use case.
- `platform/providers`: provider reference patterns.
- `environments`: runnable entrypoints (`lab`) and cloud scaffolds.
- `agents`: shared + agent-specific prompts, rules, and workflows.
- `docs`: PRDs, specs, decisions, and architecture notes.
- `tools/scripts`: helper scripts for verification and SDD document generation.
- `app/iacctl`: small CLI wrapper for consistent local execution.

## Local-first approach

- No mandatory remote backend configured.
- No hardcoded credentials, project IDs, bucket names, or secrets.
- `environments/lab` runs with local providers only.

## SDD workflow

Shared operating method:

1. `Research`
2. `PRD`
3. `Spec`
4. `Code`
5. `Review`

See `agents/shared/workflows/sdd-workflow.md`.

## Claude role

Claude is optimized for concise research synthesis, PRD/spec drafting, and architecture review using the shared standards.

## Codex role

Codex is optimized for constrained implementation and diff-level review, with strict scope control based on approved specs.

## Local lab

The local lab (`environments/lab`) uses `platform/stacks/local_foundation`, which consumes a local module that writes a local artifact file with metadata and a generated token.

## GCP whitelist scaffold

`environments/gcp-client-whitelist` consumes `platform/stacks/gcp_client_whitelist`, which wraps `platform/modules/gcp_static_egress`.

This scaffold models fixed egress for serverless outbound traffic (Cloud Router + Cloud NAT + Serverless VPC Access Connector), intended for client-side IP allowlists. Corporate values are provided later through environment variables and tfvars.

## First commands

```bash
cd iac-platform
./app/iacctl/iacctl.sh init lab
./app/iacctl/iacctl.sh validate lab
./app/iacctl/iacctl.sh plan lab
```

Or with Make directly:

```bash
cd iac-platform/agents-local
make verify ENV=lab
```
