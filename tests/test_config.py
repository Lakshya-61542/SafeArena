import tempfile
import unittest
from pathlib import Path

from backend.config import Config, load_dotenv
from backend.main import validate_bind


class ConfigTests(unittest.TestCase):
    def test_defaults_are_local_mock_loopback(self):
        c = Config.from_env({})
        self.assertEqual((c.mode, c.llm_provider, c.bind_host, c.bind_port), ("local", "mock", "127.0.0.1", 8000))

    def test_invalid_values_rejected(self):
        for env in ({"SAFEARENA_MODE": "cloud"}, {"LLM_PROVIDER": "x"}, {"BIND_PORT": "abc"}, {"BIND_PORT": "70000"}, {"GEMINI_MODEL": "a/b?key=1"}):
            with self.assertRaises(ValueError, msg=env): Config.from_env(env)

    def test_api_key_not_in_repr(self):
        self.assertNotIn("SECRET", repr(Config.from_env({"GEMINI_API_KEY": "SECRET"})))

    def test_dotenv_loader(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"; p.write_text('# c\nA=1\nB="two"\nEXISTING=new\n\nbad line\n', encoding="utf-8")
            env = {"EXISTING": "old"}; load_dotenv(p, env)
            self.assertEqual(env, {"EXISTING": "old", "A": "1", "B": "two"})
            load_dotenv(Path(d) / "missing", env)

    def test_bind_guard(self):
        validate_bind(Config(bind_host="127.0.0.1"), {}); validate_bind(Config(bind_host="localhost"), {})
        with self.assertRaises(SystemExit): validate_bind(Config(bind_host="0.0.0.0"), {})
        validate_bind(Config(bind_host="0.0.0.0"), {"SAFEARENA_ALLOW_REMOTE_BIND": "1"})
        validate_bind(Config(bind_host="0.0.0.0", mode="docker"), {})  # container must listen on all interfaces


if __name__ == "__main__":
    unittest.main()
