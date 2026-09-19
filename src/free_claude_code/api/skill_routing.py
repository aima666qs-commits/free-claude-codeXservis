"""Apply managed skill routing to Anthropic-compatible request models."""

from dataclasses import replace

from free_claude_code.application.routing import (
    RoutedMessagesRequest,
    RoutedTokenCountRequest,
)
from free_claude_code.core.anthropic import (
    Message,
    MessagesRequest,
    SystemContent,
    TokenCountRequest,
)
from free_claude_code.core.token_estimation import estimate_text_tokens
from free_claude_code.skills import record_skill_route, select_skills


def _message_text(message: Message) -> str:
    if isinstance(message.content, str):
        return message.content
    parts: list[str] = []
    for block in message.content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts)


def _routing_text(request: MessagesRequest | TokenCountRequest) -> str:
    user_messages = [
        _message_text(message) for message in request.messages if message.role == "user"
    ]
    return "\n".join(text for text in user_messages[-3:] if text).strip()


def _system_text(system: str | list[SystemContent] | None) -> str:
    if isinstance(system, str):
        return system
    if isinstance(system, list):
        return "\n".join(item.text for item in system)
    return ""


def _append_system(
    system: str | list[SystemContent] | None,
    prompt: str,
) -> str | list[SystemContent]:
    if isinstance(system, list):
        return [*system, SystemContent(type="text", text=prompt)]
    if isinstance(system, str) and system.strip():
        return system.rstrip() + "\n\n" + prompt
    return prompt


def _apply_messages(request: MessagesRequest, *, record: bool) -> MessagesRequest:
    routing_text = _routing_text(request)
    selection = select_skills(routing_text)
    original_estimate = estimate_text_tokens(
        _system_text(request.system) + "\n" + routing_text
    )
    injected_estimate = estimate_text_tokens(selection.prompt)
    if record:
        record_skill_route(
            selection.slugs,
            estimated_original_tokens=original_estimate,
            estimated_injected_tokens=injected_estimate,
        )
    if not selection.prompt:
        return request
    return request.model_copy(
        update={"system": _append_system(request.system, selection.prompt)},
        deep=True,
    )


def apply_skill_routing(
    routed: RoutedMessagesRequest,
    *,
    record: bool = True,
) -> RoutedMessagesRequest:
    """Inject a compact skill directive while preserving routing metadata."""
    updated = _apply_messages(routed.request, record=record)
    if updated is routed.request:
        return routed
    return replace(routed, request=updated)


def apply_skill_routing_to_token_count(
    routed: RoutedTokenCountRequest,
) -> RoutedTokenCountRequest:
    """Mirror skill injection for token counting without double-counting telemetry."""
    request = routed.request
    routing_text = _routing_text(request)
    selection = select_skills(routing_text)
    if not selection.prompt:
        return routed
    updated = request.model_copy(
        update={"system": _append_system(request.system, selection.prompt)},
        deep=True,
    )
    return replace(routed, request=updated)
