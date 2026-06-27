from gbmbert.preflight import format_preflight_markdown, run_preflight


def test_run_preflight_returns_named_checks() -> None:
    report = run_preflight(model_name="missing/local-model-for-test")

    names = {check.name for check in report.checks}
    assert "python" in names
    assert "local_venv" in names
    assert "NCBI_EMAIL" in names
    assert "hf_model_cache" in names


def test_format_preflight_markdown_includes_safety_boundary() -> None:
    report = run_preflight(model_name="missing/local-model-for-test")

    markdown = format_preflight_markdown(report)

    assert "# GBM-AI Preflight Report" in markdown
    assert "Research-use only. Not medical advice." in markdown
