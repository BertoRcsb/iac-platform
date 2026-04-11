# iac-platform - README Geral

## O que e
O `iac-platform` e um sistema de operacao de demandas tecnicas com IA, focado em:
- organizacao de tasks
- planejamento tecnico com risco
- execucao controlada por aprovacao
- documentacao de aprendizado reutilizavel

Nao e um sistema de deploy automatico em producao.

## Para que foi feito
Este repositorio foi criado para dar um fluxo unico e seguro para demandas de plataforma/DevOps:
1. receber demanda (texto/Jira)
2. classificar e planejar
3. validar gate antes de executar
4. executar com trilha de auditoria
5. revisar e registrar aprendizado

## O que ele ja faz hoje
- CLI unica (`agentctl`) para todo fluxo
- UI web local (PT/EN)
- intake de demanda por texto e Jira
- GO/NO-GO gate
- spec-driven mode (spec/plan/tasks/checklist)
- revisao de codigo e debug com refatoracao segura
- trilha de aprovacao (`approved_by`, logs, evidencias)
- documentacao cientifica automatizada por tarefa

## Como usar (simples)
### Opcao A - Web UI
1. `cd /home/ronan/Projects/iac-platform`
2. `./scripts/agentctl-ui`
3. abrir `http://127.0.0.1:8787/?lang=pt`
4. preencher demanda em `Executar Pipeline`
5. usar `Status` -> `Gerar Spec Pack` -> `Analisar Spec Pack` -> `GO/NO-GO`

### Opcao B - CLI
1. `./scripts/agentctl run --input "<demanda>"`
2. `./scripts/agentctl status --latest`
3. `./scripts/agentctl spec-pack --latest`
4. `./scripts/agentctl spec-analyze --latest`
5. `./scripts/agentctl gate-check --latest --manager-approved --approved-by "<gestor>"`

## Regras de seguranca atuais
- sem aprovacao humana, sem execucao critica
- cards Jira so com allowlist
- `DRY_RUN=true` recomendado ate piloto aprovado
- toda acao relevante com identidade de aprovacao

## O que falta para ficar 100% operacional
1. Fechar release estavel (tag/versionamento de go-live).
2. Definir e validar politica formal de aprovacao interna.
3. Mover segredos para cofre seguro (nao deixar token em arquivo local simples).
4. Rodar piloto controlado com cards reais (10-20) e medir resultado.
5. Validar processo com seguranca/compliance (LGPD, retencao de logs, auditoria).
6. Ativar escrita real no Jira de forma gradual (`JIRA_ACTIONS_ENABLED=true`), apos piloto.
7. Estabilizar operacao continua da UI/servico na maquina de operacao.
8. Fechar runbook oficial de incidentes e rollback.

## Documentos importantes
- README tecnico completo: `README.md`
- guia pratico web: `docs/guia-web-pratico.md`
- playbook diario: `docs/playbook-operacao-diaria.md`
- integracao spec-kit: `docs/spec-kit-integracao.md`

