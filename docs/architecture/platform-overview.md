# Platform Overview

## Why local-first now

This platform starts local-first to reduce setup friction, enable fast iteration, and keep delivery independent from early cloud access constraints.

## Ready for future corporate cloud usage

The repository already separates reusable modules, use-case stacks, and environment entrypoints. This allows later addition of:

- corporate remote state
- CI and policy checks
- organization-specific provider auth patterns
- environment promotion flows

without redesigning the core layout.

## Separation of concerns

- `platform/modules`: low-level reusable components.
- `platform/stacks`: opinionated composition for specific outcomes.
- `environments`: execution roots with concrete values and operational docs.

## Shared Claude + Codex method

Both agents follow the same SDD lifecycle and shared standards/checklists. Claude is oriented to research/spec quality; Codex is oriented to constrained implementation and review correctness.

## GCP client whitelist fit

The `gcp_static_egress` module and `gcp_client_whitelist` stack model fixed egress for serverless workloads. This directly supports client allowlist requirements where outbound calls must originate from known static IPs.
