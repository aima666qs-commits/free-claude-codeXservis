"""Idempotent deployment of the managed Claude Code skill pack."""

import os
from dataclasses import asdict
from pathlib import Path

from .catalog import BUILTIN_SKILLS, ManagedSkill

_START = "<!-- XFCC MANAGED MEMORY START -->"
_END = "<!-- XFCC MANAGED MEMORY END -->"
_MEMORY_GUIDANCE = """<!-- XFCC MANAGED MEMORY START -->
## XFCC managed project memory

For substantial multi-session work, read `.claude/xfcc-memory.md` when it exists before making claims about project state. Keep that file concise and update it at the end of substantial tasks with durable decisions, architecture/invariants, changed areas, verified blockers, release state, and the next concrete action.

Never store passwords, API keys, auth tokens, private keys, or transient logs in memory. Verify mutable facts against the repository or runtime before acting.
<!-- XFCC MANAGED MEMORY END -->"""


def _home() -> Path:
    override = os.getenv("XFCC_HOME")
    return Path(override).expanduser() if override else Path.home()


def managed_root() -> Path:
    return _home() / ".claude"


def skills_root() -> Path:
    return managed_root() / "skills"


def _render(skill: ManagedSkill) -> str:
    return (
        f"---\nname: {skill.slug}\ndescription: {skill.purpose}\n"
        "managed-by: xfcc\n---\n\n"
        f"{skill.body}"
    )


def _atomic_write(path: Path, content: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)
    return True


def _merge_memory_guidance(path: Path) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    start = current.find(_START)
    end = current.find(_END)
    if start >= 0 and end >= start:
        end += len(_END)
        merged = current[:start].rstrip() + "\n\n" + _MEMORY_GUIDANCE + current[end:]
    else:
        suffix = "\n\n" if current.strip() else ""
        merged = current.rstrip() + suffix + _MEMORY_GUIDANCE + "\n"
    if current == merged:
        return False
    return _atomic_write(path, merged)


def sync_managed_skills() -> dict[str, object]:
    """Install/update the XFCC-owned skill files and additive memory guidance."""
    changed: list[str] = []
    root = skills_root()
    root.mkdir(parents=True, exist_ok=True)
    for skill in BUILTIN_SKILLS:
        path = root / f"xfcc-{skill.slug}" / "SKILL.md"
        if _atomic_write(path, _render(skill)):
            changed.append(skill.slug)

    memory_changed = _merge_memory_guidance(managed_root() / "CLAUDE.md")
    (managed_root() / "xfcc").mkdir(parents=True, exist_ok=True)
    readme = managed_root() / "xfcc" / "README.md"
    _atomic_write(
        readme,
        "# XFCC managed layer\n\n"
        "This directory is owned by Free Claude Code. Built-in reusable skills live "
        "under ~/.claude/skills/xfcc-*/SKILL.md. Project memory belongs in "
        ".claude/xfcc-memory.md and must never contain secrets.\n",
    )
    return {
        "ok": True,
        "skill_count": len(BUILTIN_SKILLS),
        "changed_skills": changed,
        "memory_guidance_changed": memory_changed,
        "root": str(root),
    }


def managed_skill_status() -> dict[str, object]:
    """Return non-secret status for the Admin UI."""
    root = skills_root()
    items = []
    for skill in BUILTIN_SKILLS:
        path = root / f"xfcc-{skill.slug}" / "SKILL.md"
        expected = _render(skill)
        state = "missing"
        if path.exists():
            try:
                state = (
                    "current"
                    if path.read_text(encoding="utf-8") == expected
                    else "modified"
                )
            except OSError:
                state = "unreadable"
        item = asdict(skill)
        item.pop("body", None)
        item.update({"state": state, "path": str(path)})
        items.append(item)
    memory_path = managed_root() / "CLAUDE.md"
    memory_state = "missing"
    if memory_path.exists():
        try:
            text = memory_path.read_text(encoding="utf-8")
            memory_state = "current" if _START in text and _END in text else "missing"
        except OSError:
            memory_state = "unreadable"
    return {
        "root": str(root),
        "skills": items,
        "memory": {"state": memory_state, "path": str(memory_path)},
    }
