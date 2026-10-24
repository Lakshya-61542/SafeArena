import tempfile
import unittest
from pathlib import Path

from backend.app import create_app
from backend.config import Config


class AppTestCase(unittest.TestCase):
    """Fresh app + fresh temp data dir for every test."""
    config_overrides: dict = {}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data_dir = Path(self._tmp.name)
        self.config = Config(data_dir=self.data_dir, **self.config_overrides)
        self.app = create_app(self.config, **getattr(self, "app_kwargs", {}))
        self.client = self.app.test_client()
        self.ctx = self.app.extensions["safearena"]
