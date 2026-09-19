from free_claude_code.api.skill_routing import (
    apply_skill_routing,
    apply_skill_routing_to_token_count,
)
from free_claude_code.application.routing import (
    ResolvedModel,
    RoutedMessagesRequest,
    RoutedTokenCountRequest,
)
from free_claude_code.config.reasoning import ReasoningPreference
from free_claude_code.core.anthropic import (
    Message,
    MessagesRequest,
    SystemContent,
    TokenCountRequest,
)
from free_claude_code.core.reasoning import ReasoningPolicy


def _resolved() -> ResolvedModel:
    return ResolvedModel(
        original_model="claude-sonnet",
        provider_id="openai",
        provider_model="gpt-test",
        provider_model_ref="openai/gpt-test",
        reasoning_preference=ReasoningPreference.OFF,
    )


def test_messages_skill_routing_appends_compact_system_context(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("XFCC_HOME", str(tmp_path))
    request = MessagesRequest(
        model="gpt-test",
        messages=[Message(role="user", content="Сделай редизайн панели UI UX.")],
        system=[SystemContent(type="text", text="Existing system")],
    )
    routed = RoutedMessagesRequest(
        request=request,
        resolved=_resolved(),
        reasoning=ReasoningPolicy.off(),
    )

    updated = apply_skill_routing(routed)

    assert isinstance(updated.request.system, list)
    assert updated.request.system[0].text == "Existing system"
    assert "ui-ux-pro" in updated.request.system[-1].text


def test_token_count_routing_matches_provider_context_without_telemetry() -> None:
    request = TokenCountRequest(
        model="gpt-test",
        messages=[Message(role="user", content="Сделай маркетинг для Threads.")],
    )
    routed = RoutedTokenCountRequest(request=request, resolved=_resolved())

    updated = apply_skill_routing_to_token_count(routed)

    assert isinstance(updated.request.system, str)
    assert "marketing-suite" in updated.request.system
