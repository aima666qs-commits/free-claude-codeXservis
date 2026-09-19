from free_claude_code.skills.telemetry import (
    record_skill_route,
    reset_skill_telemetry,
    skill_telemetry,
)


def test_telemetry_records_aggregates_without_request_text(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("XFCC_HOME", str(tmp_path))
    reset_skill_telemetry()

    record_skill_route(
        ("ui-ux-pro", "request-orchestrator"),
        estimated_original_tokens=100,
        estimated_injected_tokens=10,
    )
    record_skill_route((), estimated_original_tokens=50, estimated_injected_tokens=0)

    data = skill_telemetry()

    assert data["total_requests"] == 2
    assert data["routed_requests"] == 1
    assert data["skill_hits"] == {"ui-ux-pro": 1, "request-orchestrator": 1}
    assert data["route_rate_pct"] == 50.0
    assert data["estimated_context_overhead_pct"] == 6.67
    assert "request" not in str(data).casefold()
