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
                actions_enabled=True,
                allowed_transition_names="To Do,In Progress,Done",
                require_issue_allowlist=True,
                allowlist_file="config/jira-issue-allowlist.txt",
            ),
            llm=RuleBasedLLMAdapter(),
            logger=StructuredLogger(self.base_dir),
        )

    def _create_review_ready_task(self, dry_run: bool = True) -> dict[str, str]:
        task = self.service.new_task(
            request="https://acme.atlassian.net/browse/INF-33\nPipeline falhou no Sonar",
            source_type="jira-link",
            source_reference="https://acme.atlassian.net/browse/INF-33",
            template_id="pipeline-failure",
            team_profile="devops",
        )
        self.service.plan_task(task["task_file"])
        self.service.execute_task(
            task["task_file"],
            manager_approved=True,
            auto_approve=True,
            approved_by="Ronan",
            dry_run=dry_run,
        )
        return task

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

    def test_jira_comment_dry_run(self) -> None:
        self.service.authorize_jira_issue("INF-33")
        result = self.service.jira_comment(
            issue_ref="INF-33",
            comment="Analise iniciada pelo piloto",
            manager_approved=True,
            approved_by="Ronan",
            approval_note="piloto",
            dry_run=True,
        )
        self.assertTrue(result["simulated"])
        self.assertEqual(result["issue_key"], "INF-33")

    def test_jira_comment_requires_approved_by(self) -> None:
        self.service.authorize_jira_issue("INF-33")
        with self.assertRaises(ServiceError) as ctx:
            self.service.jira_comment(
                issue_ref="INF-33",
                comment="Teste",
                manager_approved=True,
                approved_by="",
                dry_run=True,
            )
        self.assertIn("approved_by is required", ctx.exception.message)

    @patch("app.agent_os.application.services.transition_jira_issue")
    def test_jira_transition_real(self, mock_transition) -> None:
        self.service.authorize_jira_issue("INF-33")
        mock_transition.return_value = {
            "issue_key": "INF-33",
            "transition_id": "31",
            "transition_name": "In Progress",
        }
        result = self.service.jira_transition(
            issue_ref="INF-33",
            to_status="In Progress",
            manager_approved=True,
            approved_by="Ronan",
            approval_note="iniciar execução",
            dry_run=False,
        )
        self.assertFalse(result["simulated"])
        self.assertEqual(result["transition_name"], "In Progress")

    @patch("app.agent_os.application.services.list_jira_transitions")
    def test_jira_transitions_list(self, mock_list) -> None:
        from app.agent_os.infrastructure.jira_client import JiraTransition

        self.service.authorize_jira_issue("INF-33")
        mock_list.return_value = [JiraTransition(transition_id="11", name="In Progress")]
        result = self.service.jira_transitions("INF-33")
        self.assertEqual(result["issue_key"], "INF-33")
        self.assertEqual(result["transitions"][0]["name"], "In Progress")

    def test_jira_comment_template_preview(self) -> None:
        self.service.authorize_jira_issue("INF-33")
        task = self.service.new_task(
            request="https://acme.atlassian.net/browse/INF-33\nPipeline falhou no Sonar",
            source_type="jira-link",
            source_reference="https://acme.atlassian.net/browse/INF-33",
            template_id="pipeline-failure",
            team_profile="devops",
        )
        self.service.plan_task(task["task_file"])
        preview = self.service.jira_comment_template(
            mode="analysis-start",
            issue_ref="",
            task_ref=task["task_file"],
            post=False,
            approved_by="Ronan",
        )
        self.assertEqual(preview["issue_key"], "INF-33")
        self.assertIn("[AgentCtl Update]", preview["comment_preview"])

    def test_jira_comment_template_post_dry_run(self) -> None:
        self.service.authorize_jira_issue("INF-33")
        posted = self.service.jira_comment_template(
            mode="execution-complete",
            issue_ref="INF-33",
            post=True,
            manager_approved=True,
            approved_by="Ronan",
            dry_run=True,
        )
        self.assertEqual(posted["issue_key"], "INF-33")
        self.assertTrue(posted["simulated"])

    def test_review_auto_sync_disabled(self) -> None:
        task = self._create_review_ready_task(dry_run=False)
        reviewed = self.service.review_task(task["task_file"])
        sync = reviewed["jira_sync"]
        self.assertFalse(sync["enabled"])
        self.assertEqual(sync["status"], "SKIPPED")
        self.assertEqual(sync["reason"], "JIRA_AUTO_SYNC_ON_REVIEW=false")

    def test_review_auto_sync_skips_when_simulated_and_disabled(self) -> None:
        self.service.jira_settings.auto_sync_on_review = True
        self.service.jira_settings.auto_sync_on_simulation = False
        task = self._create_review_ready_task(dry_run=True)
        reviewed = self.service.review_task(task["task_file"])
        sync = reviewed["jira_sync"]
        self.assertEqual(sync["status"], "SKIPPED")
        self.assertIn("execution was simulated", sync["reason"])

    @patch("app.agent_os.application.services.add_jira_comment")
    def test_review_auto_sync_posts_comment_when_simulation_allowed(self, mock_add_comment) -> None:
        self.service.jira_settings.auto_sync_on_review = True
        self.service.jira_settings.auto_sync_on_simulation = True
        self.service.jira_settings.auto_sync_post_comment = True
        self.service.jira_settings.auto_sync_transition = False
        self.service.authorize_jira_issue("INF-33")
        mock_add_comment.return_value = {
            "issue_key": "INF-33",
            "comment_id": "10001",
        }

        task = self._create_review_ready_task(dry_run=True)
        reviewed = self.service.review_task(task["task_file"])
        sync = reviewed["jira_sync"]
        self.assertEqual(sync["status"], "COMPLETED")
        self.assertEqual(sync["issue_key"], "INF-33")
        self.assertEqual(len(sync["actions"]), 1)
        self.assertEqual(sync["actions"][0]["type"], "comment")
        self.assertEqual(sync["actions"][0]["comment_id"], "10001")
        mock_add_comment.assert_called_once()


if __name__ == "__main__":
    unittest.main()
