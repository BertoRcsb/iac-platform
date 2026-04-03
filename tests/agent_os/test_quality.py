from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.agent_os.application.services import AgentService
from app.agent_os.infrastructure.config import AgentSettings, JiraSettings, ProviderSettings
from app.agent_os.infrastructure.file_repo import TaskRepository
from app.agent_os.infrastructure.llm_adapters import RuleBasedLLMAdapter
from app.agent_os.infrastructure.logging import StructuredLogger


class TestQualityAutomation(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

        (self.base_dir / "tasks" / "incoming").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "knowledge" / "shared").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "config").mkdir(parents=True, exist_ok=True)

        settings = AgentSettings()
        providers = ProviderSettings()

        self.service = AgentService(
            base_dir=self.base_dir,
            repo=TaskRepository(self.base_dir),
            settings=settings,
            provider_settings=providers,
            jira_settings=JiraSettings(),
            llm=RuleBasedLLMAdapter(),
            logger=StructuredLogger(self.base_dir),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_review_code_detects_shell_risk(self) -> None:
        target = self.base_dir / "script.sh"
        target.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")

        result = self.service.review_code(str(target))
        self.assertGreaterEqual(result["summary"]["medium"], 1)
        rules = {f["rule"] for f in result["findings"]}
        self.assertIn("shell-strict-mode", rules)

    def test_debug_auto_rolls_back_when_validation_fails(self) -> None:
        target = self.base_dir / "script.sh"
        original = "#!/usr/bin/env bash\necho ok\n"
        target.write_text(original, encoding="utf-8")

        result = self.service.debug_auto(command="false", target=str(target), apply_refactor=True)

        self.assertNotEqual(result["after"]["returncode"], 0)
        self.assertTrue(result["rollback"])
        self.assertEqual(target.read_text(encoding="utf-8"), original)
        self.assertTrue((self.base_dir / result["scientific_doc"]).exists())

    def test_debug_auto_success_generates_doc(self) -> None:
        target = self.base_dir / "ok.py"
        target.write_text("print('ok')\n", encoding="utf-8")

        result = self.service.debug_auto(command="python3 -c 'print(1)'", target=str(target), apply_refactor=False)

        self.assertEqual(result["after"]["returncode"], 0)
        self.assertTrue((self.base_dir / result["scientific_doc"]).exists())


if __name__ == "__main__":
    unittest.main()
