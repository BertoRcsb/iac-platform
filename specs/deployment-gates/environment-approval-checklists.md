# Spec: Environment Approval Checklists

## Objective
Standardize environment promotion decisions with explicit evidence and approval identity.

## Required Checklist per Environment
Use `./scripts/generate-env-approval-checklist.sh <env> <task_id>` for:
- regression
- prerelease
- stage
- preprod
- prod

## Mandatory Sections
1. Scope and objective
2. Quality/tests evidence
3. Security/compliance checks
4. Observability and operations checks
5. Evidence links and references
6. Final decision (GO/NO-GO)
7. Approval record (approved_by + note + date)

## Rule
No environment promotion should occur without completed checklist and explicit manager approval.
