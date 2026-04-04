# Playbook Diario - Agent OS (1 pagina)

## Objetivo
Usar o sistema de agents de forma simples, segura e repetivel no dia a dia.

## Rotina rapida (manha)
1. Rodar diagnostico:
   - `./scripts/agentctl doctor`
2. Ver se existe task pendente:
   - `./scripts/agentctl status --latest`
3. Se houver bloqueio, priorizar desbloqueio antes de criar nova task.

## Fluxo padrao para nova demanda
1. Entrada da demanda:
   - `./scripts/agentctl run --input "<demanda>"`
2. Se vier de Jira:
   - `./scripts/agentctl jira-authorize --issue INF-33`
   - `./scripts/agentctl jira-run --issue INF-33 --template <template_id> --team <team_profile>`
3. Se quiser acelerar com template:
   - `./scripts/agentctl catalog`
   - `./scripts/agentctl run --input "<demanda>" --template <template_id> --team <team_profile>`
4. Se precisar executar:
   - `./scripts/agentctl gate-check --task <TASK_ID> --manager-approved --approved-by "<manager>"`
   - `./scripts/agentctl execute --task <TASK_ID> --manager-approved --auto-approve --approved-by "<manager>" --approval-note "<motivo>"`
5. Revisao:
   - `./scripts/agentctl review --task <TASK_ID>`
6. Aprendizado (se nao foi automatico):
   - `./scripts/agentctl learn --task <TASK_ID>`

## Revisao de codigo e debug automatico
1. Revisar riscos de codigo:
   - `./scripts/agentctl review-code --path .`
2. Rodar debug com refatoracao segura + re-teste:
   - `./scripts/agentctl debug-auto --command "./scripts/agentctl-test.sh" --path . --apply-refactor`
3. Se o teste continuar falhando, o sistema faz rollback do refactor aplicado.

## Interface grafica (modo facil)
1. Subir UI:
   - `./scripts/agentctl-ui`
2. Abrir:
   - `http://127.0.0.1:8787`
   - Portugues: `http://127.0.0.1:8787/?lang=pt`
   - Ingles: `http://127.0.0.1:8787/?lang=en`
3. Usar botoes de Run, Status, Doctor, Review Code e Debug Auto.
4. Guia para equipe:
   - `docs/guia-uso-agentctl-ui.md`

## Regras de seguranca
- Sempre trabalhar com `DRY_RUN=true` ate aprovar.
- Nao avancar execucao sem aprovacao humana quando obrigatoria.
- Toda resolucao deve gerar documentacao cientifica em `knowledge/shared`.

## Metodo cientifico obrigatorio (resumo)
Cada resolucao precisa registrar:
1. Problema
2. Hipotese
3. Metodo/Experimento
4. Evidencias
5. Analise
6. Conclusao
7. Passos de reproducao

## Fechamento do dia
1. Rodar testes:
   - `./scripts/agentctl-test.sh`
2. Conferir logs estruturados:
   - `outputs/reports/agentctl-runs.ndjson`
3. Conferir aprendizado compartilhado:
   - `knowledge/shared/`
