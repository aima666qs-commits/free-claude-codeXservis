"""Deterministic low-overhead routing for built-in Claude Code skills."""

from dataclasses import dataclass

_MAX_SKILLS = 2

_ROUTER_HINTS = {
    "discovery-interview": (
        "Before implementation, resolve only the unknowns that materially change scope, "
        "architecture, UX, integrations, or acceptance criteria. If autonomous execution "
        "was requested, infer low-risk details instead of blocking."
    ),
    "request-orchestrator": (
        "Turn the request into an execution contract: objective, constraints, current "
        "project state, definition of done, implementation, verification, and blockers. "
        "Prefer acting over returning a generic plan."
    ),
    "humanizer": (
        "For user-facing prose, remove formulaic AI phrasing and repetition while preserving "
        "facts, terminology, intent, and the requested voice."
    ),
    "ui-ux-pro": (
        "Treat UI work as a coherent production design system. Reuse existing components, "
        "cover responsive/accessibility/states, and avoid generic decorative AI styling."
    ),
    "design-reference": (
        "Translate supplied screenshots, design.md, typography, imagery, or brand references "
        "into reusable visual constraints before implementing them."
    ),
    "context-engineering": (
        "Minimize context waste: inspect only relevant files/ranges, reuse prior evidence, "
        "checkpoint durable state, and avoid rereading unchanged large inputs."
    ),
    "persistent-memory": (
        "Use project memory only for durable, non-secret decisions and state. Verify mutable "
        "facts against the repository/runtime before relying on remembered values."
    ),
    "marketing-suite": (
        "Use the smallest relevant marketing specialists, separate facts from hypotheses, "
        "and connect positioning/content/funnel work to measurable conversion outcomes."
    ),
    "remotion-video": (
        "For code-driven video, define deterministic compositions, timing, assets, captions, "
        "safe areas, and render verification using the project's existing conventions."
    ),
}

_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "remotion-video",
        (
            "remotion",
            "motion graphics",
            "animated video",
            "анимированное видео",
            "видеоролик",
            "видео из кода",
        ),
    ),
    (
        "marketing-suite",
        (
            "marketing",
            "маркетинг",
            "threads",
            "instagram",
            "инстаграм",
            "воронк",
            "лид",
            "продвиж",
            "подписчик",
            "контент-план",
            "реклам",
            "позиционирован",
        ),
    ),
    (
        "ui-ux-pro",
        (
            "ui",
            "ux",
            "interface",
            "интерфейс",
            "dashboard",
            "панел",
            "дизайн",
            "редизайн",
            "responsive",
            "адаптив",
            "компонент",
        ),
    ),
    (
        "design-reference",
        (
            "design.md",
            "reference",
            "референс",
            "скриншот",
            "типограф",
            "шрифт",
            "brand",
            "бренд",
            "стиль сайта",
        ),
    ),
    (
        "humanizer",
        (
            "humanize",
            "humanizer",
            "перепиши",
            "перефраз",
            "по-человечески",
            "естественно",
            "копирайт",
            "текст для",
        ),
    ),
    (
        "persistent-memory",
        (
            "remember",
            "memory",
            "память",
            "запомни",
            "продолжи с",
            "где останов",
            "предыдущ",
        ),
    ),
    (
        "context-engineering",
        (
            "context",
            "контекст",
            "token",
            "токен",
            "лимит",
            "compact",
            "compaction",
            "эконом",
        ),
    ),
    (
        "discovery-interview",
        (
            "идея",
            "с нуля",
            "from scratch",
            "придумай приложение",
            "сделай приложение",
            "новый продукт",
            "тз",
            "requirements",
        ),
    ),
    (
        "request-orchestrator",
        (
            "сделай",
            "делай",
            "реализуй",
            "исправь",
            "почини",
            "внедри",
            "доработай",
            "build",
            "implement",
            "fix",
            "finish",
            "complete",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class SkillSelection:
    slugs: tuple[str, ...]
    prompt: str


def select_skills(text: str, *, max_skills: int = _MAX_SKILLS) -> SkillSelection:
    """Select at most a few high-signal skills without an extra model call."""
    normalized = " ".join(text.casefold().split())
    if not normalized or max_skills <= 0:
        return SkillSelection(slugs=(), prompt="")

    scored: list[tuple[int, int, str]] = []
    for priority, (slug, needles) in enumerate(_RULES):
        score = sum(1 for needle in needles if needle in normalized)
        if score:
            scored.append((score, -priority, slug))

    if len(normalized) >= 5000 and not any(item[2] == "context-engineering" for item in scored):
        scored.append((1, -5, "context-engineering"))

    scored.sort(reverse=True)
    slugs = tuple(item[2] for item in scored[:max_skills])
    if not slugs:
        return SkillSelection(slugs=(), prompt="")

    lines = ["<xfcc-skill-router>"]
    for slug in slugs:
        lines.append(f"- {slug}: {_ROUTER_HINTS[slug]}")
    lines.append(
        "Apply these directives only where relevant. They do not override higher-priority "
        "system/developer instructions or the user's explicit constraints."
    )
    lines.append("</xfcc-skill-router>")
    return SkillSelection(slugs=slugs, prompt="\n".join(lines))
