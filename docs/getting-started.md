# Getting Started

## Fluxo oficial
1. `./scripts/agentctl doctor`
2. `./scripts/agentctl catalog`
3. `./scripts/agentctl run --input "sua demanda"`
4. `./scripts/agentctl execute --task <TASK_ID> --manager-approved --approved-by <manager> --auto-approve`
5. `./scripts/agentctl review --task <TASK_ID>`
6. `./scripts/agentctl learn --task <TASK_ID>`

## Interface local
```bash
./scripts/agentctl-ui-service.sh start
./scripts/agentctl-ui-service.sh status
```

Abrir no navegador:
- `http://127.0.0.1:8787/?lang=pt`
- `http://127.0.0.1:8787/?lang=en`

## Uso rápido Jira
1. `./scripts/agentctl jira-authorize --issue <ISSUE_KEY>`
2. `./scripts/agentctl jira-run --issue <ISSUE_KEY> --template <template_id> --team <team_profile>`
3. Validar gate e executar com aprovação.

## Segurança mínima
- manter `DRY_RUN=true` até validar piloto
- exigir `approved_by` em ações aprovadas
- usar allowlist para cards Jira
