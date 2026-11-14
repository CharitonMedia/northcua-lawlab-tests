import unittest
from pathlib import Path
from nexau.archs.main_sub.config import AgentConfig
from nexau.archs.llm.llm_config import LLMConfig
from northcua.agents.web.runner.model_step import WebAgentModelStepExecutor


class SystemPromptTests(unittest.TestCase):
    def test_missing_prompt_uses_bundled_web_template(self):
        cfg = AgentConfig(
            name="prompt-regression",
            llm_config=LLMConfig(model="unit-test", api_key="local-no-auth", base_url="http://127.0.0.1:19093/v1"),
        )
        WebAgentModelStepExecutor._configure_agent_for_step(cfg)
        self.assertEqual(cfg.system_prompt_type, "jinja")
        self.assertTrue(Path(cfg.system_prompt).is_file())
        self.assertIn("Reliable form input and stopping", Path(cfg.system_prompt).read_text())

    def test_custom_prompt_is_preserved(self):
        cfg = AgentConfig(
            name="custom-regression",
            llm_config=LLMConfig(model="unit-test", api_key="local-no-auth", base_url="http://127.0.0.1:19093/v1"),
            system_prompt="Explicit custom instructions.",
            system_prompt_type="string",
        )
        WebAgentModelStepExecutor._configure_agent_for_step(cfg)
        self.assertEqual(cfg.system_prompt, "Explicit custom instructions.")
        self.assertEqual(cfg.system_prompt_type, "string")


if __name__ == "__main__":
    unittest.main()
