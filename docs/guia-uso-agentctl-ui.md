# Guia Rapido - AgentCtl UI

## PT-BR (padrao)

### 1) Abrir na sua maquina
1. Entre no repositorio:
   - `cd /home/ronan/Projects/iac-platform`
2. Inicie a interface (manual):
   - `./scripts/agentctl-ui`
3. Abra no navegador:
   - `http://127.0.0.1:8787`

Opcional (deixar sempre ativa):
- `./scripts/agentctl-ui-service.sh start`
- `./scripts/agentctl-ui-service.sh status`
- `./scripts/agentctl-ui-service.sh install-user-service` (auto start no login)

### 2) Trocar idioma
- Portugues (padrao): `http://127.0.0.1:8787/?lang=pt`
- Ingles: `http://127.0.0.1:8787/?lang=en`

### 3) Uso rapido
1. Clique em `Catalogo` para ver templates e perfis.
2. Em `Jira (Ler Card e Resolver)`:
   - preencha link/chave do card (ex.: `INF-33`)
   - clique `Autorizar Card` (gate de segurança)
   - clique `Ler e Planejar` para gerar solução
   - para executar com aprovação, preencha `Aprovado por` e `Nota de aprovação`
3. Em `Executar Pipeline (Modo Equipe)`:
   - preencha a entrada (texto ou contexto Jira)
   - selecione template e perfil de equipe (opcional)
   - clique em `Executar`
4. Depois rode:
   - `GO / NO-GO` (validar gate antes de executar)
   - `Status`
   - `Revisao de Codigo`
   - `Debug Automatico` (se necessario)

### 4) Parar interface
- No terminal onde a UI esta rodando: `Ctrl + C`

## EN (optional)

### 1) Open on your machine
1. Go to repository:
   - `cd /home/ronan/Projects/iac-platform`
2. Start UI (manual):
   - `./scripts/agentctl-ui`
3. Open browser:
   - `http://127.0.0.1:8787`

Optional (always active):
- `./scripts/agentctl-ui-service.sh start`
- `./scripts/agentctl-ui-service.sh status`
- `./scripts/agentctl-ui-service.sh install-user-service` (autostart on login)

### 2) Language
- Portuguese (default): `http://127.0.0.1:8787/?lang=pt`
- English: `http://127.0.0.1:8787/?lang=en`

### 3) Quick usage
1. Click `Catalog` to list team templates and profiles.
2. In `Jira (Read Card and Solve)`:
   - provide issue URL/key (e.g. `INF-33`)
   - click `Authorize Card` (security gate)
   - click `Read and Plan`
   - to execute with approval, fill `Approved by` and `Approval note`
3. In `Run Pipeline (Team Mode)`:
   - fill input (text or Jira context)
   - select template/team profile (optional)
   - click `Run`
4. Then use:
   - `GO / NO-GO` (validate gate before execution)
   - `Status`
   - `Code Review`
   - `Auto Debug` (if needed)
