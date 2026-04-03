# Workflow: Team Mode Operations

1. Receive input (text, mixed language, or Jira link with context)
2. Select team profile (`platform-core`, `sre`, `devops`, `security`)
3. Select task template (`pipeline-failure`, `observability-rollout`, `access-request`, `release-gate`, `learning-doc`)
4. Run planning with explicit risk and approval gates
5. Execute only after manager approval
6. Review and close task
7. Publish scientific learning for shared reuse

Command examples:
- `./scripts/agentctl catalog`
- `./scripts/agentctl run --input "Pipeline failed in Sonar" --template pipeline-failure --team devops`
