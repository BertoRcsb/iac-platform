# iac-platform

AI-driven platform governance repository for infrastructure, observability, task orchestration, and controlled delivery workflows.

Quick overview:
- `README-GERAL.md` (simple guide: what it is, how to use, and what is missing for 100% go-live)

---

## Purpose

This repository acts as the orchestration layer for:

- AI agent collaboration
- task intake and prioritization
- structured execution workflows
- documentation and learning loops
- environment promotion control

It does not perform infrastructure provisioning by itself.
It does not automatically deploy to GCP.
It does not replace human leadership.

It exists to support a human-led platform operation.

---

## Core Vision

Create a system where multiple AI agents collaborate to:

- understand incoming demands
- classify priorities
- propose solutions
- execute technical preparation
- review each other
- document decisions and lessons learned
- require explicit human approval before advancing environments

---

## Agent Roles

- Intake Agent
- Architect Agent
- Analysis Agent
- Execution Agent
- Review Agent
- Documentation Agent
- Notification Agent
- Release Agent
- Manager Agent (human leadership)

---

## Deployment Gates

No environment advancement should occur without approval.

Expected promotion flow:

1. Regression Test
2. Prerelease
3. Stage
4. Pre-prod
5. Prod

Each gate requires:
- checklist
- validation
- human approval
- recorded evidence

---

## Current Stage

Foundation phase.

This repository currently focuses on:
- structure
- workflows
- specifications
- agent roles
- task orchestration

No live cloud changes are performed from here yet.

---

## Jira/Text Intake (Local Only)

This repository supports a 3-phase local workflow:

1. `intake` (capture request)
2. `plan` (classification + analysis)
3. `execute` (controlled local actions)

1. Create local config:
   - `cp config/jira-intake.env.example config/jira-intake.env`
2. Keep safe defaults:
   - `AUTO_ACTIONS_ENABLED="false"`
   - `AUTO_ACTIONS_LOCAL_ONLY="true"`
   - `DRY_RUN="true"`
3. Run intake (link, text, or both):
   - `./scripts/intake-task.sh --link "https://your-domain.atlassian.net/browse/ABC-123"`
   - `./scripts/intake-task.sh --text "Pipeline failed in Sonar and build step"`
   - `./scripts/intake-task.sh --link "https://.../browse/OBS-777" --text "Aplicar padrão de observabilidade no api-logwriter"`
4. Execute after approval:
   - Simulation: `./scripts/execute-task.sh --task tasks/incoming/task-xxxx.md`
   - Apply local actions: `./scripts/execute-task.sh --task tasks/incoming/task-xxxx.md --apply --manager-approved`

What `intake-task.sh` does:
- classifies task priority/category
- generates plan automatically
- creates a task file under `tasks/incoming`
- adds AI provider routing recommendation (`ai-router.sh`)

What `execute-task.sh` does:
- reads task classification
- runs only local scripts/artifacts (checklists/reports/approval records)
- appends execution logs into the task file
- respects manager approval + dry-run controls
- stays in simulation unless all conditions are met:
  - `AUTO_ACTIONS_ENABLED="true"`
  - `DRY_RUN="false"`
  - `--apply --manager-approved` provided
- triggers continuous learning updates (`learn-task.sh`) into `knowledge/*`

## AI Team Learning Loop

The repository now supports a collaborative and self-updating AI team model.

- Team contract: `agents/team/README.md`
- Learning workflow: `workflows/continuous-learning-loop.md`
- Learning script: `./scripts/learn-task.sh --task tasks/incoming/task-xxxx.md`

Learning updates append entries to:
- `knowledge/lessons-learned.md`
- `knowledge/improvement-log.md`
- `knowledge/decision-log.md`

This remains local-only and under human governance.

## AI Provider Router (Free-First)

The repository now includes a provider routing layer:
- Router script: `./scripts/ai-router.sh`
- Provider config: `config/ai-providers.env.example`
- Runtime local config: `config/ai-providers.env`

Setup:
1. `cp config/ai-providers.env.example config/ai-providers.env`
2. Keep free-first defaults:
   - `AI_FREE_FIRST="true"`
   - `AI_ALLOW_PAID_FALLBACK="false"`
3. Run router manually:
   - `./scripts/ai-router.sh --task "Pipeline failed in Sonar" --category ci-cd --priority P2`

Router behavior:
- chooses provider/model by category/profile (reasoning, writing, balanced)
- prefers free/local providers (for example `ollama`) by default
- can be later configured for paid APIs (`openai`, `claude`) when you decide
- does not execute external API calls automatically (recommendation only)

## External AI SDKs Installed (Local)

A local module was prepared in `tools/ai-hub` with installed SDKs for:
- OpenAI
- Anthropic Claude
- Google Gemini
- Groq
- OpenRouter (via OpenAI-compatible client)
- Hugging Face Inference

Quick commands:
- Check provider readiness:
  - `./scripts/ai-hub-check.sh`
- Simulated provider call:
  - `./scripts/ai-hub-call.sh openrouter "Summarize this task" true`
- Real provider call (after keys/config):
  - `./scripts/ai-hub-call.sh openrouter "Summarize this task" false`
- Free-first setup helper:
  - `./scripts/setup-ai-free-first.sh`
- with keys + real tests:
    `./scripts/setup-ai-free-first.sh --openrouter-key "<KEY>" --groq-key "<KEY>" --hf-key "<KEY>" --run-real-tests`

---

## AgentCtl (Unified CLI)

Use a single command entrypoint for the full lifecycle:

- `./scripts/agentctl new --input "<text-or-link>"`
- `./scripts/agentctl plan --task <task_id|path>`
- `./scripts/agentctl route --task <task_id|path>`
- `./scripts/agentctl execute --task <task_id|path> --manager-approved --approved-by "<manager>" --auto-approve`
- `./scripts/agentctl review --task <task_id|path>`
- `./scripts/agentctl learn --task <task_id|path>`
- `./scripts/agentctl status --task <task_id|path>`
- `./scripts/agentctl spec-pack --task <task_id|path>`
- `./scripts/agentctl spec-analyze --task <task_id|path>`
- `./scripts/agentctl gate-check --task <task_id|path> --manager-approved --approved-by "<manager>"`
- `./scripts/agentctl catalog`
- `./scripts/agentctl doctor`
- `./scripts/agentctl jira-authorize --issue <ISSUE_KEY>`
- `./scripts/agentctl jira-run --issue <ISSUE_KEY> --context "detalhes extras" --template access-request --team devops`
- `./scripts/agentctl jira-run --issue <ISSUE_KEY> --template access-request --team devops --manager-approved --approved-by "<manager>" --auto-approve`
- `./scripts/agentctl jira-transitions --issue <ISSUE_KEY>`
- `./scripts/agentctl jira-comment --issue <ISSUE_KEY> --comment "Atualização do piloto" --manager-approved --approved-by "<manager>" --dry-run false`
- `./scripts/agentctl jira-transition --issue <ISSUE_KEY> --to-status "In Progress" --manager-approved --approved-by "<manager>" --dry-run false`
- `./scripts/agentctl jira-comment-template --mode execution-complete --issue <ISSUE_KEY> --task <task_id|path>`
- `./scripts/agentctl jira-comment-template --mode execution-complete --issue <ISSUE_KEY> --task <task_id|path> --post --manager-approved --approved-by "<manager>" --dry-run false`
- `./scripts/agentctl run --input "<text-or-link>"`
- `./scripts/agentctl run --input "<text-or-link>" --manager-approved --approved-by "<manager>" --auto-approve`
- `./scripts/agentctl run --input "<text-or-link>" --template <template_id> --team <team_profile>`
- `./scripts/agentctl review-code --path .`
- `./scripts/agentctl debug-auto --command "./scripts/agentctl-test.sh" --path . --apply-refactor`

Each command outputs:
- `Reasoning Summary`
- `Decision`

And includes task data payload for observability.

Spec-driven note:
- `run` now auto-generates a spec pack (`spec.md`, `plan.md`, `tasks.md`, checklist) under `specs/features/`.
- You can regenerate manually with `./scripts/agentctl spec-pack --task <task_id>`.
- Validate readiness with `./scripts/agentctl spec-analyze --task <task_id>`.

---

## Web UI (Simple)

Run local graphical interface:

- `./scripts/agentctl-ui`
- Open `http://127.0.0.1:8787`
- Portuguese default: `http://127.0.0.1:8787/?lang=pt`
- English option: `http://127.0.0.1:8787/?lang=en`

Available actions:
- run pipeline
- run pipeline with team template/profile
- status
- catalog (templates and teams)
- doctor
- code review
- auto debug/refactor

Usage guide for team onboarding:
- `docs/ui-guide.md`
- Practical quick guide:
  `docs/guia-web-pratico.md`

Keep UI always active (background service):
- `./scripts/agentctl-ui-service.sh start`
- `./scripts/agentctl-ui-service.sh status`
- `./scripts/agentctl-ui-service.sh restart`
- `./scripts/agentctl-ui-service.sh stop`
- Optional autostart on login (Linux user service):
  `./scripts/agentctl-ui-service.sh install-user-service`

---

## Jira API (Authorized Cards Only)

Configure:
1. Fill `config/jira-intake.env`:
   - `JIRA_API_ENABLED="true"`
   - `JIRA_ACTIONS_ENABLED="true"` (only when ready for real Jira writes)
   - `JIRA_ALLOWED_TRANSITIONS="To Do,In Progress,Done"`
   - `JIRA_AUTO_SYNC_ON_REVIEW="true"` (optional)
   - `JIRA_AUTO_SYNC_ON_SIMULATION="false"` (recommended)
   - `JIRA_AUTO_SYNC_POST_COMMENT="true"`
   - `JIRA_AUTO_SYNC_TRANSITION="true|false"`
   - `JIRA_AUTO_SYNC_DONE_COMMENT_MODE="execution-complete"`
   - `JIRA_AUTO_SYNC_BLOCKED_COMMENT_MODE="blocked"`
   - `JIRA_AUTO_SYNC_DONE_TRANSITION="Done"` (optional)
   - `JIRA_AUTO_SYNC_BLOCKED_TRANSITION=""` (optional)
   - `JIRA_BASE_URL="https://your-company.atlassian.net"`
   - `JIRA_EMAIL="your-email"`
   - `JIRA_API_TOKEN="your-token"`
2. Keep authorization gate enabled:
   - `JIRA_REQUIRE_ISSUE_ALLOWLIST="true"`
   - `JIRA_ISSUE_ALLOWLIST_FILE="config/jira-issue-allowlist.txt"`

Workflow:
1. Authorize card:
   - `./scripts/agentctl jira-authorize --issue <ISSUE_KEY>`
2. Read card and generate solution plan:
   - `./scripts/agentctl jira-run --issue <ISSUE_KEY> --template access-request --team devops`
3. Execute only if authorized + approved:
   - `./scripts/agentctl jira-run --issue <ISSUE_KEY> --template access-request --team devops --manager-approved --approved-by "<manager>" --auto-approve`
4. Optional external adapter actions (comment/transition):
   - `./scripts/agentctl jira-transitions --issue <ISSUE_KEY>`
   - `./scripts/agentctl jira-comment --issue <ISSUE_KEY> --comment "Pilot update" --manager-approved --approved-by "<manager>" --dry-run false`
   - `./scripts/agentctl jira-transition --issue <ISSUE_KEY> --to-status "In Progress" --manager-approved --approved-by "<manager>" --dry-run false`
   - `./scripts/agentctl jira-comment-template --mode execution-complete --issue <ISSUE_KEY> --task <task_id|path>`
   - `./scripts/agentctl jira-comment-template --mode execution-complete --issue <ISSUE_KEY> --task <task_id|path> --post --manager-approved --approved-by "<manager>" --dry-run false`
5. Optional auto-sync on review:
   - when enabled, task closure (`DONE/BLOCKED`) can automatically post Jira comment template and optional transition
   - default behavior skips simulated executions unless `JIRA_AUTO_SYNC_ON_SIMULATION=true`
   - auto-sync requires Jira actions enabled and approval identity registered in execution (`approved_by`)
   - result is recorded in task review under `jira_sync`

Security rule:
- If card is not in allowlist, execution is blocked with suggested command.
- If execution needs approval, `approved_by` must be informed for audit trail.

GO/NO-GO command before execution:
- `./scripts/agentctl gate-check --task <task_id> --manager-approved --approved-by "<manager-name>"`

---

## Team Mode (Fast)

List available options:
- `./scripts/agentctl catalog`

Create and run with template + team profile:
- `./scripts/agentctl run --input "Pipeline failed in Sonar for service X" --template pipeline-failure --team devops`
- `./scripts/agentctl run --input "Apply observability standard to api-logwriter" --template observability-rollout --team platform-core`

Current built-in templates:
- `pipeline-failure`
- `observability-rollout`
- `access-request`
- `release-gate`
- `learning-doc`

Current team profiles:
- `platform-core`
- `sre`
- `devops`
- `security`

---

## Spec-Driven Mode (Spec Kit Inspired)

Reference approach:
- https://github.com/github/spec-kit.git
- https://github.github.com/spec-kit/quickstart.html

Mapping to this project:
1. Specify (`what/why`): `./scripts/agentctl new --input "<demanda>"` or `run`
2. Clarify: refine input/context and rerun `plan`
3. Plan: `./scripts/agentctl plan --task <task_id>`
4. Spec pack: `./scripts/agentctl spec-pack --task <task_id>`
5. Spec quality gate: `./scripts/agentctl spec-analyze --task <task_id>`
6. Route/execute/review/learn:
   - `route`
   - `gate-check`
   - `execute`
   - `review`
   - `learn`

Generated artifacts:
- `specs/features/<NNN-feature>/spec.md`
- `specs/features/<NNN-feature>/plan.md`
- `specs/features/<NNN-feature>/tasks.md`
- `specs/features/<NNN-feature>/checklists/spec-quality.md`

Clean Architecture + Clean Code rules enforced in artifacts:
- explicit domain/application/infrastructure boundaries
- approval gates and audit trail mandatory
- local-first validation before external actions
- reproducible steps and testable acceptance criteria

---

## Task Contract

Task contract is standardized as JSON schema:
- `specs/task-schema/task.schema.json`

State machine:
- `NEW -> TRIAGED -> PLANNED -> APPROVED -> EXECUTING -> REVIEW -> DONE/BLOCKED`

Persisted task files are stored as:
- `tasks/incoming/<task_id>/task.json`

---

## Nano Config

AgentCtl nano-config file:
- `config/agentctl.env.example`

Key variables:
- `PROFILE=local|staging|prod`
- `DRY_RUN=true|false`
- `REQUIRE_MANAGER_APPROVAL=true|false`
- `AI_FREE_FIRST=true|false`
- `AI_ALLOW_PAID_FALLBACK=true|false`
- `MAX_LLM_CALLS_PER_TASK`
- `MAX_COST_USD_PER_TASK`
- `AUTO_LEARNING_ENABLED=true|false`
- `AUTO_LEARNING_ON_SIMULATION=true|false`
- `DEFAULT_PROVIDER_PROFILE=reasoning|writing|fast|balanced`

---

## Clean Architecture

Implementation layers:
- Domain: `app/agent_os/domain`
- Application: `app/agent_os/application`
- Infrastructure: `app/agent_os/infrastructure`
- Architecture reference: `docs/architecture/agent-os-clean-architecture.md`

Goals:
- business rules independent from provider
- explicit transitions and approval gates
- deterministic defaults with local safety
- structured logs in `outputs/reports/agentctl-runs.ndjson`

---

## Scientific Learning

Each resolved task can generate scientific documentation for shared learning:
- `./scripts/agentctl learn --task <task_id|path>`
- `./scripts/agentctl debug-auto --command "./scripts/agentctl-test.sh" --path . --apply-refactor`

Generated output:
- `knowledge/shared/<task_id>-scientific-method.md`
- `knowledge/shared/debug-<timestamp>-auto-debug.md`

Method sections include:
- problem
- hypothesis
- experiment method
- evidence
- analysis
- conclusion
- reproducibility steps

This enforces continuous documentation and organizational learning.

---

## Real Local Execution (Pilot)

When `DRY_RUN=false`, execution now runs real **local** actions by category:
- `ci-cd`: run validation command
- `observability`: generate checklist + run validation command
- `release`: generate release note/report + run validation command
- `access-gcp`: register approval request + run validation command

Behavior:
- Success: task moves to `REVIEW` with `EXECUTED_LOCAL`
- Failure: task moves to `BLOCKED` with `FAILED_LOCAL`

Recommended pilot flow:
1. `./scripts/agentctl gate-check --task <task_id> --manager-approved --approved-by "<manager>"`
2. `./scripts/agentctl execute --task <task_id> --manager-approved --auto-approve --approved-by "<manager>" --approval-note "pilot autorizado" --dry-run false`
3. One-command local pilot for authorized card:
   - `./scripts/pilot-authorized-card.sh <ISSUE_KEY> "descrição da demanda"`

Environment approval checklist generator:
- `./scripts/generate-env-approval-checklist.sh <regression|prerelease|stage|preprod|prod> <task_id>`
- Specification:
  `specs/deployment-gates/environment-approval-checklists.md`

---

## Tests

Run automated tests:

- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `./scripts/agentctl-test.sh`

Covered flow tests:
- dry-run execution behavior
- state transition validation
- provider routing
- approval log registration
- code review risk detection
- debug auto rollback/refactor validation

CI on GitHub:
- `.github/workflows/agentctl-ci.yml`
- Runs `py_compile`, test suite, and doctor report on `push/pull_request` to `main`

---

## Daily Playbook

Short operational guide for team usage:
- `docs/daily-operations.md`

No deployment or cloud provisioning is executed by this flow.
