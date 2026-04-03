# Workflow: AgentCtl Lifecycle

1. `agentctl new` receives input and creates task contract (`task.json`)
2. `agentctl plan` triages and plans
3. `agentctl route` selects provider/model candidate
4. `agentctl execute` applies dry-run or approved execution
5. `agentctl review` validates results and closes task
6. `agentctl learn` writes scientific learning documentation

## State Machine

NEW -> TRIAGED -> PLANNED -> APPROVED -> EXECUTING -> REVIEW -> DONE/BLOCKED

## Rules

- Explicit approval required when `REQUIRE_MANAGER_APPROVAL=true`
- Scientific learning document is generated for each resolved task
- Structured logs are written to `outputs/reports/agentctl-runs.ndjson`
