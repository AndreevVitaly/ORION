"""Тесты способов запуска консольного приложения."""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class EntrypointTestCase(unittest.TestCase):
    def test_main_file_can_be_run_directly(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "portrait_core" / "main.py"),
                "--help",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=15,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertIn(b"--backend", result.stdout)
        self.assertIn(b"--demo", result.stdout)


if __name__ == "__main__":
    unittest.main()
