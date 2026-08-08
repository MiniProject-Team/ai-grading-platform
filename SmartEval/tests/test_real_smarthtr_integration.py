from __future__ import annotations

import os
from pathlib import Path
import unittest

from integration.smarthtr_client import SharedRuntimeSmartHTRClient


@unittest.skipUnless(
    os.getenv("RUN_COLAB_SMARTHTR_TESTS", "false").lower() == "true",
    "Set RUN_COLAB_SMARTHTR_TESTS=true inside the Colab shared runtime to run real SmartHTR recognition.",
)
class SharedRuntimeSmartHTRIntegrationTests(unittest.TestCase):
    def test_recognizes_a_real_complete_document(self):
        document = os.getenv("SMARTHR_INTEGRATION_FILE")
        if not document:
            self.skipTest("Set SMARTHR_INTEGRATION_FILE to a PDF or image accessible to the Colab runtime.")
        result = SharedRuntimeSmartHTRClient().recognize(Path(document))
        self.assertTrue(result.full_text.strip())
        self.assertTrue(result.pages)
