from free_claude_code.skills.router import select_skills


def test_router_prioritizes_specific_skill_and_caps_selection() -> None:
    result = select_skills(
        "Build a Remotion animated video and complete the implementation.",
        max_skills=2,
    )

    assert result.slugs == ("remotion-video", "request-orchestrator")
    assert "<xfcc-skill-router>" in result.prompt
    assert "remotion-video" in result.prompt


def test_router_selects_context_engineering_for_large_context() -> None:
    result = select_skills("x" * 5000)

    assert result.slugs == ("context-engineering",)


def test_router_does_not_inject_for_unrelated_short_text() -> None:
    result = select_skills("hello")

    assert result.slugs == ()
    assert result.prompt == ""


def test_short_ui_token_does_not_match_build() -> None:
    result = select_skills("Build the backend implementation.")

    assert "ui-ux-pro" not in result.slugs
