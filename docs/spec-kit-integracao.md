# Integracao Spec Kit no AgentCtl

## Objetivo
Usar o fluxo spec-driven do Spec Kit como base, mantendo arquitetura limpa e operacao rapida.

Referencias:
- https://github.com/github/spec-kit.git
- https://github.github.com/spec-kit/quickstart.html

## Mapeamento Pratico

1. **Specify (o que/por que)**  
   `./scripts/agentctl new --input "<demanda>"`  
   ou  
   `./scripts/agentctl run --input "<demanda>"`

2. **Clarify (remover ambiguidade)**  
   Atualize o contexto da demanda e rode:  
   `./scripts/agentctl plan --task <TASK_ID>`

3. **Plan (plano tecnico)**  
   `./scripts/agentctl plan --task <TASK_ID>`

4. **Tasks/Checklist (quebra executavel)**  
   `./scripts/agentctl spec-pack --task <TASK_ID>`

5. **Analyze (quality gate antes de executar)**  
   `./scripts/agentctl spec-analyze --task <TASK_ID>`

6. **Implementacao controlada**  
   `./scripts/agentctl route --task <TASK_ID>`  
   `./scripts/agentctl gate-check --task <TASK_ID> --manager-approved --approved-by "<manager>"`  
   `./scripts/agentctl execute --task <TASK_ID> --manager-approved --auto-approve --approved-by "<manager>"`  
   `./scripts/agentctl review --task <TASK_ID>`  
   `./scripts/agentctl learn --task <TASK_ID>`

## Saidas Geradas

Para cada spec-pack:
- `specs/features/<NNN-feature>/spec.md`
- `specs/features/<NNN-feature>/plan.md`
- `specs/features/<NNN-feature>/tasks.md`
- `specs/features/<NNN-feature>/checklists/spec-quality.md`

## Regras de Arquitetura Limpa

- **Domain**: regras, contratos, estado, sem acoplamento externo.
- **Application**: casos de uso e orquestracao.
- **Infrastructure**: adaptadores (arquivo, Jira, providers, UI, scripts).

## Regra de Performance

- local-first por padrao.
- evitar chamadas externas sem necessidade.
- gates explicitos e saidas estruturadas para depuracao rapida.
