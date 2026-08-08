import unittest

from smarthtr.config.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_default_device_is_supported(self):
        self.assertIn(Settings.from_environment().device, {"auto", "cpu", "cuda"})
