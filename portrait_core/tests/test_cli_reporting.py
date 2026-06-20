"""Тесты краткого CLI-отчета."""

import locale
import subprocess
import sys
import unittest
from pathlib import Path

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.analyzer import analyze_points
from portrait_core.reporting import build_report, format_summary_report


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI_ENCODING = locale.getpreferredencoding(False)


class CliReportingTestCase(unittest.TestCase):
    def test_summary_report_hides_dense_mesh(self):
        points = ManualAdapter().extract_points("manual-test-image")
        report = build_report(
            "manual-test-image",
            points,
            analyze_points(points),
        )

        summary = format_summary_report(report)

        self.assertIn("ПОРТРЕТ: краткий отчет", summary)
        self.assertIn("Морфология:", summary)
        self.assertNotIn("'vertices'", summary)

    def test_demo_mode_prints_summary_by_default(self):
        result = subprocess.run(
            [sys.executable, "portrait_core/main.py", "--demo"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding=CLI_ENCODING,
            errors="replace",
            timeout=20,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ПОРТРЕТ: краткий отчет", result.stdout)
        self.assertNotIn("'measurements'", result.stdout)

    def test_demo_mode_can_print_full_json(self):
        result = subprocess.run(
            [sys.executable, "portrait_core/main.py", "--demo", "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding=CLI_ENCODING,
            errors="replace",
            timeout=20,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"measurements"', result.stdout)
        self.assertIn('"schema_version"', result.stdout)


if __name__ == "__main__":
    unittest.main()
