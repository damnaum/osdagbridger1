"""CLI integration tests — runs the actual ``osdagbridge`` commands."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "plate_girder"


class TestCLIAnalyze:
    def test_analyze_example_basic(self):
        """CLI analyze succeeds for example_basic.yaml."""
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "analyze",
             str(EXAMPLES_DIR / "example_basic.yaml")],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        assert "Analysis Results" in result.stdout

    def test_analyze_with_output_flag(self, tmp_path):
        """CLI analyze --output writes JSON file."""
        out_file = tmp_path / "results.json"
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "analyze",
             str(EXAMPLES_DIR / "example_basic.yaml"),
             "-o", str(out_file)],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["status"] == "completed"

    def test_analyze_missing_file(self):
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "analyze", "nonexistent.yaml"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_analyze_verification_01(self):
        yaml_path = EXAMPLES_DIR / "verification_case_01.yaml"
        if not yaml_path.exists():
            pytest.skip("verification_case_01.yaml missing")
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "analyze", str(yaml_path)],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0


class TestCLIReport:
    def test_report_generates_file(self, tmp_path):
        out_file = tmp_path / "report.txt"
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "report",
             str(EXAMPLES_DIR / "example_basic.yaml"),
             str(out_file)],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        assert out_file.exists()
        text = out_file.read_text()
        assert "OSDAGBRIDGE" in text
        assert "REPORT" in text


class TestCLIInfo:
    def test_info_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "info"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "plate_girder" in result.stdout


class TestCLIVersion:
    def test_version_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "osdagbridge", "--version"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "0.2.0" in result.stdout

