"""Guardrails for the GitHub production-confidence workflow."""

from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "quality-gate.yml"


def test_quality_gate_runs_on_pull_requests_and_main():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in source
    assert "branches: [main]" in source
    assert "timeout-minutes:" in source
    assert "cancel-in-progress: true" in source


def test_quality_gate_compiles_and_runs_the_full_suite():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "python -m compileall -q ." in source
    assert "python -m pytest -q" in source
    assert "requirements-dev.txt" in source
