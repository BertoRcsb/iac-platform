# Agent OS Clean Architecture

## Overview

Agent OS is structured with explicit architectural boundaries:

1. Domain
2. Application
3. Infrastructure

This keeps business rules stable while provider/tool integrations can evolve independently.

## Layers

### Domain (`app/agent_os/domain`)

Contains:
- task state machine
- classification and risk rules
- task schema validation
- entity model
- LLM interface contract

No dependency on external provider implementation.

### Application (`app/agent_os/application`)

Contains use-cases:
- new
- plan
- route
- execute
- review
- learn
- status
- run

Applies orchestration rules, approval gates, idempotency, and logging.

### Infrastructure (`app/agent_os/infrastructure`)

Contains adapters:
- file repository
- config loader
- provider router
- LLM adapter implementation
- doctor checks
- structured logger

## State Machine

`NEW -> TRIAGED -> PLANNED -> APPROVED -> EXECUTING -> REVIEW -> DONE/BLOCKED`

Invalid transitions are rejected at runtime.

## Scientific Learning Rule

Every resolved task should produce a scientific learning document with:
- problem
- hypothesis
- method
- evidence
- analysis
- conclusion
- reproducibility

This makes knowledge transferable to other teams.
