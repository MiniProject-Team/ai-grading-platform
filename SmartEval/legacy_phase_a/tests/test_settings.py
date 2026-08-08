import unittest

from smarteval.config.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_default_paths_are_project_relative(self) -> None:
        settings = Settings.from_environment()
        self.assertEqual(settings.input_directory.name, "inputs")
        self.assertEqual(settings.log_directory.name, "logs")
