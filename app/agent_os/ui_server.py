"""Simple local web UI for AgentCtl."""

from __future__ import annotations

import argparse
import html
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

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
        "status_doctor_card": "Status / Catálogo / Doctor",
        "gate_card": "GO / NO-GO",
        "gate_button": "Validar Gate",
        "task_id_optional": "Task ID (opcional)",
        "latest": "mais recente",
        "status_button": "Status",
        "catalog_button": "Catálogo",
        "doctor_button": "Doctor",
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
        "status_doctor_card": "Status / Catalog / Doctor",
        "gate_card": "GO / NO-GO",
        "gate_button": "Validate Gate",
        "task_id_optional": "Task ID (optional)",
        "latest": "latest",
        "status_button": "Status",
        "catalog_button": "Catalog",
        "doctor_button": "Doctor",
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


def option_list(items: list[dict[str, object]], default_label: str) -> str:
    options = [f"<option value=''>{html.escape(default_label)}</option>"]
    for item in items:
        item_id = str(item.get("id", ""))
        name = str(item.get("name", item_id))
        options.append(f"<option value='{html.escape(item_id)}'>{html.escape(name)} ({html.escape(item_id)})</option>")
    return "\n".join(options)


def page_template(output: str = "", err: str = "", lang: str = "pt") -> str:
    lang = normalize_lang(lang)
    t = I18N[lang]
    output_block = f"<pre>{html.escape(output)}</pre>" if output else ""
    err_block = f"<pre style='color:#b00020'>{html.escape(err)}</pre>" if err else ""
    team_options = option_list(available_team_profiles(), t["default_team_profile"])
    template_options = option_list(available_task_templates(), t["default_template"])
    pt_active = "font-weight:700;text-decoration:underline;" if lang == "pt" else ""
    en_active = "font-weight:700;text-decoration:underline;" if lang == "en" else ""
    lang_hidden = f"<input type='hidden' name='lang' value='{html.escape(lang)}'>"
    return f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>{t["title"]}</title>
  <style>
    body {{
      font-family: "Space Grotesk", "Work Sans", "Segoe UI", sans-serif;
      margin: 0;
      background: radial-gradient(circle at 0% 0%, #eef5ff, #f9fafc 48%, #fff 100%);
      color: #0f172a;
    }}
    .container {{ max-width: 1120px; margin: 20px auto; padding: 0 16px; }}
    h1 {{ margin-top: 0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .card {{
      border: 1px solid #dbe2ea;
      padding: 12px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.86);
      backdrop-filter: blur(2px);
      box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);
    }}
    label {{ display: block; margin: 6px 0 2px; font-size: 13px; }}
    input, textarea, select {{ width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #c9d5e3; border-radius: 8px; }}
    button {{
      margin-top: 8px;
      padding: 8px 12px;
      cursor: pointer;
      border: 1px solid #1f4f8a;
      border-radius: 8px;
      background: linear-gradient(135deg, #1f4f8a, #2f6bb4);
      color: #fff;
      font-weight: 600;
    }}
    .out {{ margin-top: 18px; }}
    pre {{ white-space: pre-wrap; background: #0f172a; color: #e5e7eb; padding: 12px; border-radius: 8px; }}
    .micro {{ font-size: 12px; color: #334155; }}
    @media (max-width: 860px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class='container'>
  <h1>{t["header"]}</h1>
  <p>{t["subtitle"]}</p>
  <p class='micro'>{t["language"]}: <a href='/?lang=pt' style='{pt_active}'>Português</a> | <a href='/?lang=en' style='{en_active}'>English</a></p>

    <div class='grid'>
    <div class='card'>
      <h3>{t["run_card"]}</h3>
      <form method='post' action='/run'>
        {lang_hidden}
        <label>{t["input"]}</label>
        <textarea name='input' rows='3' placeholder='Pipeline falhou no Sonar'></textarea>
        <label>{t["template"]}</label>
        <select name='template'>
          {template_options}
        </select>
        <label>{t["team_profile"]}</label>
        <select name='team'>
          {team_options}
        </select>
        <label><input type='checkbox' name='manager_approved'> {t["manager_approved"]}</label>
        <label><input type='checkbox' name='auto_approve'> {t["auto_approve"]}</label>
        <label>{t["approved_by"]}</label>
        <input name='approved_by' placeholder='nome do gestor'>
        <label>{t["approval_note"]}</label>
        <input name='approval_note' placeholder='contexto da aprovação'>
        <button type='submit'>{t["run_button"]}</button>
      </form>
      <p class='micro'>{t["run_hint"]}</p>
    </div>

    <div class='card'>
      <h3>{t["jira_card"]}</h3>
      <form method='post' action='/jira-authorize'>
        {lang_hidden}
        <label>{t["jira_issue"]}</label>
        <input name='issue' placeholder='https://.../browse/INF-33 or INF-33'>
        <button type='submit'>{t["jira_authorize_button"]}</button>
      </form>
      <form method='post' action='/jira-run'>
        {lang_hidden}
        <label>{t["jira_issue"]}</label>
        <input name='issue' placeholder='https://.../browse/INF-33 or INF-33'>
        <label>{t["jira_context"]}</label>
        <textarea name='context' rows='3' placeholder='Detalhes adicionais'></textarea>
        <label>{t["template"]}</label>
        <select name='template'>
          {template_options}
        </select>
        <label>{t["team_profile"]}</label>
        <select name='team'>
          {team_options}
        </select>
        <label><input type='checkbox' name='manager_approved'> {t["manager_approved"]}</label>
        <label><input type='checkbox' name='auto_approve'> {t["auto_approve"]}</label>
        <label>{t["approved_by"]}</label>
        <input name='approved_by' placeholder='nome do gestor'>
        <label>{t["approval_note"]}</label>
        <input name='approval_note' placeholder='contexto da aprovação'>
        <button type='submit'>{t["jira_run_button"]}</button>
      </form>
      <p class='micro'>{t["jira_execute_button"]}</p>
    </div>

    <div class='card'>
      <h3>{t["status_doctor_card"]}</h3>
      <form method='post' action='/status'>
        {lang_hidden}
        <label>{t["task_id_optional"]}</label>
        <input name='task' placeholder='task-...'>
        <label><input type='checkbox' name='latest' checked> {t["latest"]}</label>
        <button type='submit'>{t["status_button"]}</button>
      </form>
      <form method='post' action='/catalog'>
        {lang_hidden}
        <button type='submit'>{t["catalog_button"]}</button>
      </form>
      <form method='post' action='/doctor'>
        {lang_hidden}
        <button type='submit'>{t["doctor_button"]}</button>
      </form>
    </div>

    <div class='card'>
      <h3>{t["gate_card"]}</h3>
      <form method='post' action='/gate-check'>
        {lang_hidden}
        <label>{t["task_id_optional"]}</label>
        <input name='task' placeholder='task-...'>
        <label><input type='checkbox' name='latest' checked> {t["latest"]}</label>
        <label><input type='checkbox' name='manager_approved'> {t["manager_approved"]}</label>
        <label><input type='checkbox' name='auto_approve'> {t["auto_approve"]}</label>
        <label>{t["approved_by"]}</label>
        <input name='approved_by' placeholder='nome do gestor'>
        <button type='submit'>{t["gate_button"]}</button>
      </form>
    </div>

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
        elif path == "/jira-authorize":
            issue = form.get("issue", [""])[0].strip()
            if not issue:
                self._send(page_template(err=t["jira_issue_required"], lang=lang), status=HTTPStatus.BAD_REQUEST)
                return
            args = ["jira-authorize", "--issue", issue]
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
