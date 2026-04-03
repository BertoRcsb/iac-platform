from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.agent_os.application.services import AgentService, ServiceError
from app.agent_os.infrastructure.config import AgentSettings, JiraSettings, ProviderSettings
from app.agent_os.infrastructure.file_repo import TaskRepository
from app.agent_os.infrastructure.jira_client import JiraIssue, extract_issue_key
from app.agent_os.infrastructure.llm_adapters import RuleBasedLLMAdapter
from app.agent_os.infrastructure.logging import StructuredLogger


class TestJiraIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        (self.base_dir / "tasks" / "incoming").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "config").mkdir(parents=True, exist_ok=True)

        self.service = AgentService(
            base_dir=self.base_dir,
            repo=TaskRepository(self.base_dir),
            settings=AgentSettings(),
            provider_settings=ProviderSettings(),
            jira_settings=JiraSettings(
                enabled=True,
                base_url="https://acme.atlassian.net",
                email="bot@example.com",
                api_token="token",
                require_issue_allowlist=True,
                allowlist_file="config/jira-issue-allowlist.txt",
            ),
            llm=RuleBasedLLMAdapter(),
            logger=StructuredLogger(self.base_dir),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_extract_issue_key(self) -> None:
        self.assertEqual(extract_issue_key("https://acme.atlassian.net/browse/INF-33"), "INF-33")
        self.assertEqual(extract_issue_key("inf-222"), "INF-222")
        self.assertEqual(extract_issue_key("no key"), "")

    @patch("app.agent_os.application.services.fetch_jira_issue")
    def test_jira_run_plans_without_execution(self, mock_fetch) -> None:
        mock_fetch.return_value = JiraIssue(
            key="INF-33",
            url="https://acme.atlassian.net/browse/INF-33",
            summary="Pipeline failed in sonar",
            description="Build step returns 401",
            status="To Do",
            priority="High",
            issue_type="Task",
            labels=["ci", "sonar"],
        )

        result = self.service.jira_run(
            issue_ref="INF-33",
            context="Service api-logwriter",
            template_id="pipeline-failure",
            team_profile="devops",
            manager_approved=False,
            auto_approve=False,
        )
        self.assertEqual(result["state"], "PLANNED")
        self.assertEqual(result["jira_issue_key"], "INF-33")

    @patch("app.agent_os.application.services.fetch_jira_issue")
    def test_jira_run_blocks_execution_when_not_authorized(self, mock_fetch) -> None:
        mock_fetch.return_value = JiraIssue(
            key="INF-50",
            url="https://acme.atlassian.net/browse/INF-50",
            summary="Need access update",
            description="Grant read role",
            status="To Do",
            priority="Medium",
            issue_type="Task",
            labels=[],
        )
        with self.assertRaises(ServiceError) as ctx:
            self.service.jira_run(
                issue_ref="INF-50",
                manager_approved=True,
                auto_approve=True,
            )
        self.assertIn("not authorized in allowlist", ctx.exception.message)

    def test_authorize_jira_issue(self) -> None:
        result = self.service.authorize_jira_issue("https://acme.atlassian.net/browse/INF-99")
        self.assertEqual(result["issue_key"], "INF-99")
        allowlist = self.base_dir / "config" / "jira-issue-allowlist.txt"
        self.assertIn("INF-99", allowlist.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
