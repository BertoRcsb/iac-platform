# Guia Web Pratico - AgentCtl

## O que e
O AgentCtl e um sistema local para organizar demandas tecnicas com IA, executar fluxo controlado e registrar aprendizado.

## Para que serve
- transformar pedido em task estruturada
- gerar plano tecnico e riscos
- validar gate de aprovacao antes de executar
- executar localmente com seguranca
- revisar resultado e documentar aprendizado

## O que da para fazer hoje na Web UI
- criar e rodar pipeline por texto ou contexto Jira
- autorizar card Jira e planejar execucao
- gerar e analisar spec pack (spec/plan/tasks/checklist)
- consultar status da task
- rodar doctor (saude do ambiente)
- revisar codigo
- rodar debug automatico com refatoracao segura

## Como abrir
1. No repositorio:
   - `cd /home/ronan/Projects/iac-platform`
2. Iniciar UI:
   - `./scripts/agentctl-ui`
3. Abrir no navegador:
   - `http://127.0.0.1:8787/?lang=pt`

## Fluxo mais simples (dia a dia)
1. Em `Executar Pipeline`, escreva a demanda e clique `Executar`.
2. Abra `Status` para pegar o `task_id`.
3. Clique `Gerar Spec Pack`.
4. Clique `Analisar Spec Pack` e confirme `GO`.
5. Execute `GO / NO-GO`, depois `execute/review/learn` (via CLI ou fluxo guiado).

## Fluxo Jira simples
1. Preencher link/chave do card.
2. Clicar `Autorizar Card`.
3. Clicar `Ler e Planejar`.
4. Se aprovado, seguir gate e execucao.

## Regras de seguranca
- nao executar mudancas criticas sem aprovacao humana
- usar allowlist para cards Jira
- manter `DRY_RUN=true` ate validar piloto
- registrar `approved_by` para auditoria

## Resultado esperado
No final de cada tarefa voce tem:
- estado claro (DONE/BLOCKED)
- evidencias de execucao
- documentacao de aprendizado reutilizavel

