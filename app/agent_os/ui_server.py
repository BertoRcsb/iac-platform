"""Simple local web UI for AgentCtl."""

from __future__ import annotations

import argparse
import html
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.agent_os.domain.jira_comment_templates import available_comment_templates
from app.agent_os.domain.team_templates import available_task_templates, available_team_profiles

I18N: dict[str, dict[str, str]] = {
    "pt": {
        "title": "AgentCtl UI",
        "header": "AgentCtl Web UI",
        "subtitle": "Interface local do Agent OS com modo equipe.",
        "language": "Idioma",
        "run_card": "Executar Pipeline (Modo Equipe)",
        "input": "Entrada",
        "template": "Template",
        "team_profile": "Perfil de Equipe",
        "manager_approved": "aprovado pelo gestor",
        "auto_approve": "auto aprovar",
        "approved_by": "Aprovado por",
        "approval_note": "Nota de aprovação",
        "run_button": "Executar",
        "run_hint": "Use template + equipe para acelerar o plano com fluxo DevOps padrão.",
        "jira_card": "Jira (Ler Card e Resolver)",
        "jira_issue": "Card Jira (link ou chave)",
        "jira_context": "Contexto adicional (opcional)",
        "jira_authorize_button": "Autorizar Card",
        "jira_run_button": "Ler e Planejar",
        "jira_execute_button": "Ler e Executar (se autorizado)",
        "jira_transitions_button": "Listar Transições",
        "jira_comment": "Comentário Jira",
        "jira_comment_button": "Publicar Comentário",
        "jira_transition": "Transição Jira",
        "jira_transition_button": "Mover Status",
        "jira_transition_name": "Nome da transição",
        "jira_comment_template": "Template de Comentário Jira",
        "jira_comment_mode": "Modo do template",
        "jira_comment_template_button": "Gerar Comentário",
        "jira_comment_template_post_now": "publicar agora",
        "status_doctor_card": "Status / Catálogo / Doctor",
        "gate_card": "GO / NO-GO",
        "gate_button": "Validar Gate",
        "task_id_optional": "Task ID (opcional)",
        "latest": "mais recente",
        "status_button": "Status",
        "catalog_button": "Catálogo",
        "doctor_button": "Doctor",
        "spec_pack_button": "Gerar Spec Pack",
        "spec_analyze_button": "Analisar Spec Pack",
        "feature_name_optional": "Nome da Feature (opcional)",
        "code_review_card": "Revisão de Código",
        "path": "Caminho",
        "review_button": "Revisar Código",
        "auto_debug_card": "Debug Automático",
        "validation_command": "Comando de Validação",
        "apply_safe_refactor": "aplicar refatoração segura",
        "debug_button": "Executar Debug",
        "default_template": "Sem template",
        "default_team_profile": "Sem perfil de equipe",
        "run_input_required": "A entrada é obrigatória para executar o pipeline",
        "jira_issue_required": "Informe o link ou chave do card Jira",
        "unsupported_path": "Rota não suportada",
        "jira_issue_placeholder": "https://.../browse/ABC-123 ou ABC-123",
        "manager_name_placeholder": "nome do gestor",
        "approval_note_placeholder": "contexto da aprovacao",
        "jira_context_placeholder": "Detalhes adicionais",
        "jira_comment_placeholder": "Resumo da acao",
        "jira_transition_placeholder": "In Progress",
        "task_placeholder": "task-...",
        "quick_guide_title": "Guia Rapido",
        "quick_guide_text": "1) Executar Pipeline  2) Status (pegar task_id)  3) Gerar Spec Pack  4) Analisar Spec Pack  5) Gate e execucao com aprovacao",
        "advanced_panel": "Acoes avancadas",
        "logo_note": "Emblema conceitual integrado (nao oficial)",
        "essential_flow": "Fluxo essencial",
    },
    "en": {
        "title": "AgentCtl UI",
        "header": "AgentCtl Web UI",
        "subtitle": "Local Agent OS interface with team mode.",
        "language": "Language",
        "run_card": "Run Pipeline (Team Mode)",
        "input": "Input",
        "template": "Template",
        "team_profile": "Team Profile",
        "manager_approved": "manager approved",
        "auto_approve": "auto approve",
        "approved_by": "Approved by",
        "approval_note": "Approval note",
        "run_button": "Run",
        "run_hint": "Use template + team for faster planning with a standard DevOps flow.",
        "jira_card": "Jira (Read Card and Solve)",
        "jira_issue": "Jira card (URL or key)",
        "jira_context": "Additional context (optional)",
        "jira_authorize_button": "Authorize Card",
        "jira_run_button": "Read and Plan",
        "jira_execute_button": "Read and Execute (if authorized)",
        "jira_transitions_button": "List Transitions",
        "jira_comment": "Jira Comment",
        "jira_comment_button": "Post Comment",
        "jira_transition": "Jira Transition",
        "jira_transition_button": "Move Status",
        "jira_transition_name": "Transition name",
        "jira_comment_template": "Jira Comment Template",
        "jira_comment_mode": "Template mode",
        "jira_comment_template_button": "Build Comment",
        "jira_comment_template_post_now": "post now",
        "status_doctor_card": "Status / Catalog / Doctor",
        "gate_card": "GO / NO-GO",
        "gate_button": "Validate Gate",
        "task_id_optional": "Task ID (optional)",
        "latest": "latest",
        "status_button": "Status",
        "catalog_button": "Catalog",
        "doctor_button": "Doctor",
        "spec_pack_button": "Generate Spec Pack",
        "spec_analyze_button": "Analyze Spec Pack",
        "feature_name_optional": "Feature Name (optional)",
        "code_review_card": "Code Review",
        "path": "Path",
        "review_button": "Review Code",
        "auto_debug_card": "Auto Debug",
        "validation_command": "Validation Command",
        "apply_safe_refactor": "apply safe refactor",
        "debug_button": "Run Debug",
        "default_template": "No template",
        "default_team_profile": "No team profile",
        "run_input_required": "Input is required to run pipeline",
        "jira_issue_required": "Provide Jira URL or issue key",
        "unsupported_path": "Unsupported path",
        "jira_issue_placeholder": "https://.../browse/ABC-123 or ABC-123",
        "manager_name_placeholder": "manager name",
        "approval_note_placeholder": "approval context",
        "jira_context_placeholder": "Additional details",
        "jira_comment_placeholder": "Action summary",
        "jira_transition_placeholder": "In Progress",
        "task_placeholder": "task-...",
        "quick_guide_title": "Quick Guide",
        "quick_guide_text": "1) Run Pipeline  2) Status (get task_id)  3) Generate Spec Pack  4) Analyze Spec Pack  5) Gate and execute with approval",
        "advanced_panel": "Advanced actions",
        "logo_note": "Integrated conceptual emblem (unofficial)",
        "essential_flow": "Essential flow",
    },
}


def normalize_lang(lang: str | None) -> str:
    if lang in I18N:
        return str(lang)
    return "pt"


def run_agentctl(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["python3", "-m", "app.agent_os.cli", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def option_list(items: list[dict[str, object]], default_label: str, value_key: str = "id", label_key: str = "name") -> str:
    options = [f"<option value=''>{html.escape(default_label)}</option>"]
    for item in items:
        item_id = str(item.get(value_key, ""))
        name = str(item.get(label_key, item_id))
        options.append(f"<option value='{html.escape(item_id)}'>{html.escape(name)} ({html.escape(item_id)})</option>")
    return "\n".join(options)


def page_template(output: str = "", err: str = "", lang: str = "pt") -> str:
    lang = normalize_lang(lang)
    t = I18N[lang]
    output_block = f"<pre>{html.escape(output)}</pre>" if output else ""
    err_block = f"<pre class='error'>{html.escape(err)}</pre>" if err else ""
    team_options = option_list(available_team_profiles(), t["default_team_profile"])
    template_options = option_list(available_task_templates(), t["default_template"])
    comment_mode_options = option_list(available_comment_templates(), "execution-complete", value_key="mode", label_key="title")
    pt_active = "font-weight:700;text-decoration:underline;" if lang == "pt" else ""
    en_active = "font-weight:700;text-decoration:underline;" if lang == "en" else ""
    lang_hidden = f"<input type='hidden' name='lang' value='{html.escape(lang)}'>"
    return f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>{t["title"]}</title>
  <style>
    :root {{
      --bg-a: #0a1220;
      --bg-b: #0f1c31;
      --card: #12243d;
      --line: #2a456c;
      --text: #e6edf8;
      --muted: #9db1cc;
      --accent: #3f9cff;
      --accent-2: #2f7dd0;
    }}
    body {{
      font-family: "Space Grotesk", "Work Sans", "Segoe UI", sans-serif;
      margin: 0;
      background: radial-gradient(circle at 15% 0%, var(--bg-b), var(--bg-a) 55%, #060b13 100%);
      color: var(--text);
    }}
    .container {{ max-width: 1080px; margin: 24px auto; padding: 0 16px; }}
    .top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:14px; }}
    .brand {{ display:flex; align-items:center; gap:12px; }}
    .brand h1 {{ margin:0; font-size:25px; }}
    .brand p {{ margin:2px 0 0; color:var(--muted); font-size:13px; }}
    .lang {{ font-size:13px; color:var(--muted); }}
    .lang a {{ color:#d2e5ff; }}
    .grid {{ display:grid; grid-template-columns: 1.3fr 1fr; gap:14px; }}
    .stack {{ display:grid; gap:14px; }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: linear-gradient(160deg, rgba(26, 45, 74, 0.92), rgba(19, 37, 62, 0.9));
      box-shadow: 0 14px 28px rgba(0,0,0,0.28);
    }}
    h3 {{ margin:0 0 8px; }}
    label {{ display:block; margin:7px 0 3px; font-size:12px; color:var(--muted); }}
    input, textarea, select {{
      width:100%;
      padding:9px;
      box-sizing:border-box;
      border:1px solid #2f4d76;
      border-radius:8px;
      background:#0f2038;
      color:var(--text);
    }}
    input::placeholder, textarea::placeholder {{ color:#7992b2; }}
    button {{
      margin-top:10px;
      padding:8px 12px;
      cursor:pointer;
      border:1px solid #3f8fdf;
      border-radius:8px;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color:#fff;
      font-weight:600;
    }}
    .row {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
    .flow {{
      border:1px dashed #3f5f88;
      padding:8px 10px;
      border-radius:8px;
      color:#bcd0ec;
      margin-bottom:10px;
      font-size:12px;
    }}
    details {{
      border:1px solid var(--line);
      border-radius:10px;
      padding:8px 10px;
      background: rgba(13, 26, 43, 0.9);
    }}
    summary {{ cursor:pointer; color:#cfe1fa; font-weight:600; }}
    .out {{ margin-top:16px; }}
    pre {{
      white-space:pre-wrap;
      background:#081221;
      color:#dfe8f7;
      padding:12px;
      border-radius:9px;
      border:1px solid #223d62;
    }}
    .error {{ color:#ffe0e4; background:#3a0f18; border-color:#6e2333; }}
    .micro {{ font-size:12px; color:var(--muted); }}
    @media (max-width: 860px) {{
      .top {{ flex-direction:column; align-items:flex-start; }}
      .grid, .row {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
  <div class='container'>
    <div class='top'>
      <div class='brand'>
        <svg width='72' height='72' viewBox='0 0 88 88' role='img' aria-label='emblem'>
          <defs>
            <linearGradient id='g1' x1='0' y1='0' x2='1' y2='1'>
              <stop offset='0%' stop-color='#1b4f89' />
              <stop offset='100%' stop-color='#2f7cd0' />
            </linearGradient>
            <linearGradient id='g2' x1='0' y1='0' x2='1' y2='1'>
              <stop offset='0%' stop-color='#2e8b57' />
              <stop offset='100%' stop-color='#1f6f45' />
            </linearGradient>
          </defs>
          <path d='M44 6 L76 18 L72 58 L44 82 L16 58 L12 18 Z' fill='url(#g1)' stroke='#7fb3ff' stroke-width='2'/>
          <path d='M44 34 L72 22 L70 56 L44 78 L18 56 L16 22 Z' fill='url(#g2)' opacity='0.95'/>
          <path d='M26 40 Q44 24 62 40' fill='none' stroke='#d8e6ff' stroke-width='3' stroke-linecap='round'/>
          <path d='M44 24 L49 52 L44 62 L39 52 Z' fill='#f3d06b' stroke='#fff1ba' stroke-width='1'/>
          <circle cx='44' cy='20' r='4.5' fill='#f3d06b'/>
        </svg>
        <div>
          <h1>{t["header"]}</h1>
          <p>{t["subtitle"]}</p>
          <p class='micro'>{t["logo_note"]}</p>
        </div>
      </div>
      <div class='lang'>{t["language"]}: <a href='/?lang=pt' style='{pt_active}'>Português</a> | <a href='/?lang=en' style='{en_active}'>English</a></div>
    </div>

    <div class='grid'>
      <div class='stack'>
        <div class='card'>
          <h3>{t["run_card"]}</h3>
          <div class='flow'><strong>{t["essential_flow"]}:</strong> {t["quick_guide_text"]}</div>
          <form method='post' action='/run'>
            {lang_hidden}
            <label>{t["input"]}</label>
            <textarea name='input' rows='3' placeholder='Pipeline falhou no Sonar'></textarea>
            <div class='row'>
              <div>
                <label>{t["template"]}</label>
                <select name='template'>{template_options}</select>
              </div>
              <div>
                <label>{t["team_profile"]}</label>
                <select name='team'>{team_options}</select>
              </div>
            </div>
            <div class='row'>
              <label><input type='checkbox' name='manager_approved'> {t["manager_approved"]}</label>
              <label><input type='checkbox' name='auto_approve'> {t["auto_approve"]}</label>
            </div>
            <div class='row'>
              <div>
                <label>{t["approved_by"]}</label>
                <input name='approved_by' placeholder='{t["manager_name_placeholder"]}'>
              </div>
              <div>
                <label>{t["approval_note"]}</label>
                <input name='approval_note' placeholder='{t["approval_note_placeholder"]}'>
              </div>
            </div>
            <button type='submit'>{t["run_button"]}</button>
          </form>
          <p class='micro'>{t["run_hint"]}</p>
        </div>

        <div class='card'>
          <h3>{t["jira_card"]}</h3>
          <form method='post' action='/jira-run'>
            {lang_hidden}
            <label>{t["jira_issue"]}</label>
            <input name='issue' placeholder='{t["jira_issue_placeholder"]}'>
            <label>{t["jira_context"]}</label>
            <textarea name='context' rows='2' placeholder='{t["jira_context_placeholder"]}'></textarea>
            <div class='row'>
              <button type='submit'>{t["jira_run_button"]}</button>
              <button type='submit' formaction='/jira-authorize'>{t["jira_authorize_button"]}</button>
            </div>
          </form>
          <p class='micro'>{t["jira_execute_button"]}</p>
        </div>
      </div>

      <div class='stack'>
        <div class='card'>
          <h3>{t["status_doctor_card"]}</h3>
          <form method='post' action='/status'>
            {lang_hidden}
            <label>{t["task_id_optional"]}</label>
            <input name='task' placeholder='{t["task_placeholder"]}'>
            <label><input type='checkbox' name='latest' checked> {t["latest"]}</label>
            <div class='row'>
              <button type='submit'>{t["status_button"]}</button>
              <button type='submit' formaction='/doctor'>{t["doctor_button"]}</button>
            </div>
          </form>
          <form method='post' action='/spec-pack'>
            {lang_hidden}
            <label>{t["feature_name_optional"]}</label>
            <input name='feature' placeholder='feature-name'>
            <label>{t["task_id_optional"]}</label>
            <input name='task' placeholder='{t["task_placeholder"]}'>
            <label><input type='checkbox' name='latest' checked> {t["latest"]}</label>
            <div class='row'>
              <button type='submit'>{t["spec_pack_button"]}</button>
              <button type='submit' formaction='/spec-analyze'>{t["spec_analyze_button"]}</button>
            </div>
          </form>
        </div>

        <div class='card'>
          <h3>{t["gate_card"]}</h3>
          <form method='post' action='/gate-check'>
            {lang_hidden}
            <label>{t["task_id_optional"]}</label>
            <input name='task' placeholder='{t["task_placeholder"]}'>
            <label><input type='checkbox' name='latest' checked> {t["latest"]}</label>
            <label>{t["approved_by"]}</label>
            <input name='approved_by' placeholder='{t["manager_name_placeholder"]}'>
            <div class='row'>
              <label><input type='checkbox' name='manager_approved'> {t["manager_approved"]}</label>
              <label><input type='checkbox' name='auto_approve'> {t["auto_approve"]}</label>
            </div>
            <button type='submit'>{t["gate_button"]}</button>
          </form>
        </div>

        <details>
          <summary>{t["advanced_panel"]}</summary>
          <div class='stack' style='margin-top:10px;'>
            <div class='card'>
              <h3>{t["code_review_card"]}</h3>
              <form method='post' action='/review-code'>
                {lang_hidden}
                <label>{t["path"]}</label>
                <input name='path' value='.'>
                <button type='submit'>{t["review_button"]}</button>
              </form>
            </div>

            <div class='card'>
              <h3>{t["auto_debug_card"]}</h3>
              <form method='post' action='/debug-auto'>
                {lang_hidden}
                <label>{t["validation_command"]}</label>
                <input name='command' value='./scripts/agentctl-test.sh'>
                <label>{t["path"]}</label>
                <input name='path' value='.'>
                <label><input type='checkbox' name='apply_refactor'> {t["apply_safe_refactor"]}</label>
                <button type='submit'>{t["debug_button"]}</button>
              </form>
            </div>

            <div class='card'>
              <h3>Jira Extra</h3>
              <form method='post' action='/jira-transitions'>
                {lang_hidden}
                <label>{t["jira_issue"]}</label>
                <input name='issue' placeholder='{t["jira_issue_placeholder"]}'>
                <button type='submit'>{t["jira_transitions_button"]}</button>
              </form>
              <form method='post' action='/jira-comment'>
                {lang_hidden}
                <label>{t["jira_issue"]}</label>
                <input name='issue' placeholder='{t["jira_issue_placeholder"]}'>
                <label>{t["jira_comment"]}</label>
                <textarea name='comment' rows='2' placeholder='{t["jira_comment_placeholder"]}'></textarea>
                <button type='submit'>{t["jira_comment_button"]}</button>
              </form>
              <form method='post' action='/jira-transition'>
                {lang_hidden}
                <label>{t["jira_issue"]}</label>
                <input name='issue' placeholder='{t["jira_issue_placeholder"]}'>
                <label>{t["jira_transition_name"]}</label>
                <input name='to_status' placeholder='{t["jira_transition_placeholder"]}'>
                <button type='submit'>{t["jira_transition_button"]}</button>
              </form>
              <form method='post' action='/jira-comment-template'>
                {lang_hidden}
                <label>{t["jira_comment_mode"]}</label>
                <select name='mode'>{comment_mode_options}</select>
                <label>{t["jira_issue"]}</label>
                <input name='issue' placeholder='{t["jira_issue_placeholder"]}'>
                <button type='submit'>{t["jira_comment_template_button"]}</button>
              </form>
              <form method='post' action='/catalog'>
                {lang_hidden}
                <button type='submit'>{t["catalog_button"]}</button>
              </form>
            </div>
          </div>
        </details>
      </div>
    </div>

    <div class='out'>
      {output_block}
      {err_block}
    </div>
  </div>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _path_and_lang(self) -> tuple[str, str]:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query, keep_blank_values=True)
        lang = normalize_lang(query.get("lang", ["pt"])[0])
        return parsed.path, lang

    def _read_form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length).decode("utf-8")
        return parse_qs(data, keep_blank_values=True)

    def _send(self, body: str, status: int = HTTPStatus.OK) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        _, lang = self._path_and_lang()
        self._send(page_template(lang=lang))

    def do_POST(self) -> None:  # noqa: N802
        form = self._read_form()
        path, lang = self._path_and_lang()
        lang = normalize_lang(form.get("lang", [lang])[0])
        t = I18N[lang]

        args: list[str] = []
        if path == "/run":
            input_text = form.get("input", [""])[0].strip()
            if not input_text:
                self._send(page_template(err=t["run_input_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            args = ["run", "--input", input_text]
            approved_by = form.get("approved_by", [""])[0].strip()
            approval_note = form.get("approval_note", [""])[0].strip()
            template = form.get("template", [""])[0].strip()
            team = form.get("team", [""])[0].strip()
            if template:
                args += ["--template", template]
            if team:
                args += ["--team", team]
            if "manager_approved" in form:
                args.append("--manager-approved")
            if "auto_approve" in form:
                args.append("--auto-approve")
            if approved_by:
                args += ["--approved-by", approved_by]
            if approval_note:
                args += ["--approval-note", approval_note]
        elif path == "/status":
            task = form.get("task", [""])[0].strip()
            args = ["status"]
            if task:
                args += ["--task", task]
            if "latest" in form:
                args.append("--latest")
        elif path == "/doctor":
            args = ["doctor"]
        elif path == "/catalog":
            args = ["catalog"]
        elif path == "/spec-pack":
            task = form.get("task", [""])[0].strip()
            feature = form.get("feature", [""])[0].strip()
            args = ["spec-pack"]
            if task:
                args += ["--task", task]
            if "latest" in form:
                args.append("--latest")
            if feature:
                args += ["--feature", feature]
        elif path == "/spec-analyze":
            task = form.get("task", [""])[0].strip()
            args = ["spec-analyze"]
            if task:
                args += ["--task", task]
            if "latest" in form:
                args.append("--latest")
        elif path == "/jira-authorize":
            issue = form.get("issue", [""])[0].strip()
            if not issue:
                self._send(page_template(err=t["jira_issue_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            args = ["jira-authorize", "--issue", issue]
        elif path == "/jira-transitions":
            issue = form.get("issue", [""])[0].strip()
            if not issue:
                self._send(page_template(err=t["jira_issue_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            args = ["jira-transitions", "--issue", issue]
        elif path == "/jira-run":
            issue = form.get("issue", [""])[0].strip()
            if not issue:
                self._send(page_template(err=t["jira_issue_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            context = form.get("context", [""])[0].strip()
            approved_by = form.get("approved_by", [""])[0].strip()
            approval_note = form.get("approval_note", [""])[0].strip()
            args = ["jira-run", "--issue", issue]
            if context:
                args += ["--context", context]
            template = form.get("template", [""])[0].strip()
            team = form.get("team", [""])[0].strip()
            if template:
                args += ["--template", template]
            if team:
                args += ["--team", team]
            if "manager_approved" in form:
                args.append("--manager-approved")
            if "auto_approve" in form:
                args.append("--auto-approve")
            if approved_by:
                args += ["--approved-by", approved_by]
            if approval_note:
                args += ["--approval-note", approval_note]
        elif path == "/jira-comment":
            issue = form.get("issue", [""])[0].strip()
            comment_text = form.get("comment", [""])[0].strip()
            if not issue:
                self._send(page_template(err=t["jira_issue_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            if not comment_text:
                self._send(page_template(err=t["run_input_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            approved_by = form.get("approved_by", [""])[0].strip()
            approval_note = form.get("approval_note", [""])[0].strip()
            args = ["jira-comment", "--issue", issue, "--comment", comment_text]
            if "manager_approved" in form:
                args.append("--manager-approved")
            if approved_by:
                args += ["--approved-by", approved_by]
            if approval_note:
                args += ["--approval-note", approval_note]
        elif path == "/jira-transition":
            issue = form.get("issue", [""])[0].strip()
            to_status = form.get("to_status", [""])[0].strip()
            if not issue:
                self._send(page_template(err=t["jira_issue_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            if not to_status:
                self._send(page_template(err=t["run_input_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            approved_by = form.get("approved_by", [""])[0].strip()
            approval_note = form.get("approval_note", [""])[0].strip()
            args = ["jira-transition", "--issue", issue, "--to-status", to_status]
            if "manager_approved" in form:
                args.append("--manager-approved")
            if approved_by:
                args += ["--approved-by", approved_by]
            if approval_note:
                args += ["--approval-note", approval_note]
        elif path == "/jira-comment-template":
            issue = form.get("issue", [""])[0].strip()
            mode = form.get("mode", ["execution-complete"])[0].strip() or "execution-complete"
            task = form.get("task", [""])[0].strip()
            extra = form.get("extra", [""])[0].strip()
            approved_by = form.get("approved_by", [""])[0].strip()
            approval_note = form.get("approval_note", [""])[0].strip()
            args = ["jira-comment-template", "--mode", mode]
            if issue:
                args += ["--issue", issue]
            if task:
                args += ["--task", task]
            if "latest" in form:
                args.append("--latest")
            if extra:
                args += ["--extra", extra]
            if "post_now" in form:
                args.append("--post")
            if "manager_approved" in form:
                args.append("--manager-approved")
            if approved_by:
                args += ["--approved-by", approved_by]
            if approval_note:
                args += ["--approval-note", approval_note]
        elif path == "/gate-check":
            task = form.get("task", [""])[0].strip()
            approved_by = form.get("approved_by", [""])[0].strip()
            args = ["gate-check"]
            if task:
                args += ["--task", task]
            if "latest" in form:
                args.append("--latest")
            if "manager_approved" in form:
                args.append("--manager-approved")
            if "auto_approve" in form:
                args.append("--auto-approve")
            if approved_by:
                args += ["--approved-by", approved_by]
        elif path == "/review-code":
            target = form.get("path", ["."])[0].strip() or "."
            args = ["review-code", "--path", target]
        elif path == "/debug-auto":
            command = form.get("command", ["./scripts/agentctl-test.sh"])[0].strip() or "./scripts/agentctl-test.sh"
            target = form.get("path", ["."])[0].strip() or "."
            args = ["debug-auto", "--command", command, "--path", target]
            if "apply_refactor" in form:
                args.append("--apply-refactor")
        else:
            self._send(page_template(err=f"{t['unsupported_path']}: {path}", lang=lang), status=HTTPStatus.NOT_FOUND)
            return

        code, out, err = run_agentctl(args)
        err_msg = err if code != 0 and err else ""
        self._send(page_template(output=out, err=err_msg, lang=lang), status=HTTPStatus.OK if code == 0 else HTTPStatus.BAD_REQUEST)


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentCtl local web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"AgentCtl UI running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
