from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jxops.incident import analyze_lines, render_report, run_analysis


class IncidentAnalysisTests(unittest.TestCase):
    def test_detects_warp_loop_and_region_churn(self) -> None:
        lines = [
            "WARN WARP actor=a from=left to=right",
            "WARN WARP actor=a from=right to=left",
            "WARN WARP actor=a from=left to=right",
            "WARN WARP actor=a from=right to=left",
            "INFO AOI action=enter entity=b region=edge",
            "INFO AOI action=leave entity=b region=edge",
            "INFO AOI action=enter entity=b region=edge",
            "INFO AOI action=leave entity=b region=edge",
            "INFO AOI action=enter entity=b region=edge",
            "INFO AOI action=leave entity=b region=edge",
        ]
        analysis = analyze_lines(lines)
        self.assertEqual({"warp-loop", "region-churn"}, {item.kind for item in analysis.findings})

    def test_report_has_bounded_incident_sections(self) -> None:
        analysis = analyze_lines(
            [
                "WARN WARP actor=a from=left to=right",
                "WARN WARP actor=a from=right to=left",
                "WARN WARP actor=a from=left to=right",
                "WARN WARP actor=a from=right to=left",
            ]
        )
        report = render_report(analysis, "sample.log")
        self.assertIn("## Root Cause", report)
        self.assertIn("## Bounded Remediation", report)
        self.assertIn("## Verification Plan", report)

    def test_missing_log_returns_usage_error(self) -> None:
        with TemporaryDirectory() as directory:
            result = run_analysis(
                Path(directory) / "missing.log",
                Path(directory) / "report.md",
            )
        self.assertEqual(2, result)


if __name__ == "__main__":
    unittest.main()

