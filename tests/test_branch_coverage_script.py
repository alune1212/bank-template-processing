from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_branch_coverage.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_branch_coverage_script", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_coverage_xml(xml_path: Path, branch_rate: str) -> None:
    xml_path.write_text(
        f'<?xml version="1.0" ?>\n<coverage branch-rate="{branch_rate}"></coverage>\n',
        encoding="utf-8",
    )


def test_read_branch_rate_percent_parses_float(tmp_path):
    module = _load_script_module()
    xml_path = tmp_path / "coverage.xml"
    _write_coverage_xml(xml_path, "0.9058")

    assert module._read_branch_rate_percent(xml_path) == 90.58


def test_main_outputs_ascii_safe_messages(tmp_path, monkeypatch):
    module = _load_script_module()
    xml_path = tmp_path / "coverage.xml"
    _write_coverage_xml(xml_path, "0.9058")

    stdout_buffer = io.BytesIO()
    stdout = io.TextIOWrapper(stdout_buffer, encoding="ascii")

    monkeypatch.setattr(sys, "argv", ["check_branch_coverage.py", "--xml", str(xml_path), "--min-branch", "85"])
    monkeypatch.setattr(sys, "stdout", stdout)

    exit_code = module.main()

    stdout.flush()
    output = stdout_buffer.getvalue().decode("ascii")
    stdout.close()

    assert exit_code == 0
    assert "[branch-gate] overall branch coverage: 90.58%" in output
    assert "[branch-gate] threshold met" in output


def test_main_returns_one_when_threshold_not_met(tmp_path, monkeypatch, capsys):
    module = _load_script_module()
    xml_path = tmp_path / "coverage.xml"
    _write_coverage_xml(xml_path, "0.8400")

    monkeypatch.setattr(sys, "argv", ["check_branch_coverage.py", "--xml", str(xml_path), "--min-branch", "85"])

    assert module.main() == 1

    captured = capsys.readouterr()
    assert "threshold not met: 84.00% < 85.00%" in captured.out


def test_main_returns_two_when_file_missing(monkeypatch, capsys, tmp_path):
    module = _load_script_module()
    missing_path = tmp_path / "missing.xml"

    monkeypatch.setattr(sys, "argv", ["check_branch_coverage.py", "--xml", str(missing_path), "--min-branch", "85"])

    assert module.main() == 2

    captured = capsys.readouterr()
    assert "read failed" in captured.out
