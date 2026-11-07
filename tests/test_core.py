from core import validate_analysis, build_demo_analysis, _parse_json

def test_parse_json_with_code_fence():
    assert _parse_json('```json\n{"ok": true}\n```') == {"ok": True}

def test_validate_analysis_clamps_score_and_adds_defaults():
    result = validate_analysis({"readiness_score": 150})
    assert result["readiness_score"] == 100
    assert result["requirements"] == []

def test_demo_analysis_returns_expected_sections():
    result = build_demo_analysis("Python SQL FastAPI project", "Python developer with SQL and AWS experience. " * 3)
    assert "requirements" in result
    assert "priority_actions" in result
    assert result["readiness_label"].startswith("Demo mode")
