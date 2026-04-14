from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.agent_os.application.services import AgentService, ServiceError
from app.agent_os.domain.state_machine import InvalidStateTransitionError, assert_transition
from app.agent_os.infrastructure.config import AgentSettings, JiraSettings, ProviderSettings
from app.agent_os.infrastructure.file_repo import TaskRepository
from app.agent_os.infrastructure.llm_adapters import RuleBasedLLMAdapter
from app.agent_os.infrastructure.logging import StructuredLogger


class TestAgentFlow(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

        (self.base_dir / "tasks" / "incoming").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "config").mkdir(parents=True, exist_ok=True)

        settings = AgentSettings(
            dry_run=True,
            require_manager_approval=True,
            ai_free_first=True,
            ai_allow_paid_fallback=False,
            auto_learning_enabled=True,
            auto_learning_on_simulation=True,
            default_provider_profile="balanced",
        )
        providers = ProviderSettings(
            ollama_enabled=False,
            openrouter_enabled=True,
            openrouter_api_key="test-key",
            groq_enabled=False,
            gemini_enabled=False,
            openai_enabled=False,
            claude_enabled=False,
            hf_enabled=False,
        )

        self.repo = TaskRepository(self.base_dir)
        self.service = AgentService(
            base_dir=self.base_dir,
            repo=self.repo,
            settings=settings,
            provider_settings=providers,
            jira_settings=JiraSettings(),
            llm=RuleBasedLLMAdapter(),
            logger=StructuredLogger(self.base_dir),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_state_transition_validation(self) -> None:
        with self.assertRaises(InvalidStateTransitionError):
            assert_transition("NEW", "DONE", reason="invalid direct jump")

    def test_dry_run_execution(self) -> None:
        created = self.service.new_task("Pipeline failed in Sonar", "text", "inline")
        self.service.plan_task(created["task_file"])
        self.service.route_task(created["task_file"])

        executed = self.service.execute_task(
            created["task_file"],
            manager_approved=True,
            auto_approve=True,
            approved_by="qa-manager",
            dry_run=True,
        )
        self.assertEqual(executed["execution_status"], "SIMULATED")
        self.assertEqual(executed["state"], "REVIEW")
        self.assertEqual(executed["approved_by"], "qa-manager")

    def test_provider_routing(self) -> None:
        created = self.service.new_task("Apply observability standard", "text", "inline")
        self.service.plan_task(created["task_file"])
        routed = self.service.route_task(created["task_file"])

        self.assertEqual(routed["provider"], "openrouter")
        self.assertIn("openrouter", routed["candidates"])

    def test_approval_log_when_not_approved(self) -> None:
        created = self.service.new_task("Release to production gate", "text", "inline")
        self.service.plan_task(created["task_file"])

        with self.assertRaises(ServiceError) as ctx:
            self.service.execute_task(created["task_file"], manager_approved=False, auto_approve=False)

        self.assertIn("Manager approval required", ctx.exception.message)

        task_file = Path(created["task_file"])
        payload = json.loads(task_file.read_text(encoding="utf-8"))
        approval_logs = payload["execution"].get("approval_logs", [])
        self.assertGreaterEqual(len(approval_logs), 1)

    def test_execute_requires_approved_by_for_audit(self) -> None:
        created = self.service.new_task("Release to production gate", "text", "inline")
        self.service.plan_task(created["task_file"])

        with self.assertRaises(ServiceError) as ctx:
            self.service.execute_task(created["task_file"], manager_approved=True, auto_approve=True, approved_by="")

        self.assertIn("GO/NO-GO blocked execution", ctx.exception.message)

    def test_gate_check_reports_go(self) -> None:
        created = self.service.new_task("Pipeline failed in Sonar", "text", "inline")
        self.service.plan_task(created["task_file"])
        gate = self.service.gate_check(
            created["task_file"],
            manager_approved=True,
            auto_approve=True,
            approved_by="release-manager",
            dry_run=True,
        )
        self.assertEqual(gate["gate_check"]["overall"], "GO")

    def test_real_local_execution_success(self) -> None:
        created = self.service.new_task("Pipeline failed in Sonar", "text", "inline")
        self.service.plan_task(created["task_file"])
        executed = self.service.execute_task(
            created["task_file"],
            manager_approved=True,
            auto_approve=True,
            approved_by="ops-manager",
            dry_run=False,
        )
        self.assertEqual(executed["execution_status"], "EXECUTED_LOCAL")
        self.assertEqual(executed["state"], "REVIEW")

    def test_real_local_execution_failure_blocks_task(self) -> None:
        created = self.service.new_task("Pipeline failed in Sonar", "text", "inline")
        self.service.plan_task(created["task_file"])
        payload = json.loads(Path(created["task_file"]).read_text(encoding="utf-8"))
        payload["plan"]["validation_command"] = "false"
        Path(created["task_file"]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        executed = self.service.execute_task(
            created["task_file"],
            manager_approved=True,
            auto_approve=True,
            approved_by="ops-manager",
            dry_run=False,
        )
        self.assertEqual(executed["execution_status"], "FAILED_LOCAL")
        self.assertEqual(executed["state"], "BLOCKED")

    def test_template_drives_category_priority_and_workflow(self) -> None:
        created = self.service.new_task(
            "Build failed after dependency update",
            "text",
            "inline",
            template_id="pipeline-failure",
            team_profile="devops",
        )
        planned = self.service.plan_task(created["task_file"])

        self.assertEqual(planned["category"], "ci-cd")
        self.assertEqual(planned["priority"], "P2")
        self.assertEqual(planned["workflow"], "incident-analysis")

        payload = json.loads(Path(created["task_file"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["context"]["template"]["id"], "pipeline-failure")
        self.assertEqual(payload["context"]["team_profile"]["id"], "devops")

    def test_catalog_lists_templates_and_profiles(self) -> None:
        catalog = self.service.catalog()
        template_ids = {item["id"] for item in catalog["templates"]}
        team_ids = {item["id"] for item in catalog["team_profiles"]}
        self.assertIn("observability-rollout", template_ids)
        self.assertIn("platform-core", team_ids)

    def test_spec_pack_generation(self) -> None:
        created = self.service.new_task(
            "Apply observability standard to service api-logwriter",
            "text",
            "inline",
            template_id="observability-rollout",
            team_profile="platform-core",
        )
        self.service.plan_task(created["task_file"])
        packed = self.service.spec_pack_task(created["task_file"])

        spec_pack_path = self.base_dir / packed["spec_pack_path"]
        self.assertTrue(spec_pack_path.exists())
        self.assertTrue((spec_pack_path / "spec.md").exists())
        self.assertTrue((spec_pack_path / "plan.md").exists())
        self.assertTrue((spec_pack_path / "tasks.md").exists())
        self.assertTrue((spec_pack_path / "checklists" / "spec-quality.md").exists())
        self.assertEqual(packed["quality_status"], "PASS")

        status = self.service.status_task(created["task_file"])
        self.assertTrue(status["spec_pack"]["path"])
        self.assertEqual(status["spec_pack"]["quality_status"], "PASS")

        analyzed = self.service.spec_analyze_task(created["task_file"])
        self.assertEqual(analyzed["overall"], "GO")

    def test_spec_analyze_requires_spec_pack(self) -> None:
        created = self.service.new_task("Pipeline issue", "text", "inline")
        self.service.plan_task(created["task_file"])
        with self.assertRaises(ServiceError) as ctx:
            self.service.spec_analyze_task(created["task_file"])
        self.assertIn("Spec pack not found", ctx.exception.message)

    def test_new_task_with_invalid_template_returns_service_error(self) -> None:
        with self.assertRaises(ServiceError) as ctx:
            self.service.new_task(
                "Any task",
                "text",
                "inline",
                template_id="unknown-template",
                team_profile="devops",
            )
        self.assertIn("Unknown template", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
