"""Validated local installer for third-party Markdown Claude Code skills."""

import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .manager import managed_root, skills_root

_MAX_SKILL_BYTES = 100_000
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_CRITICAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "prompt_override",
        re.compile(
            r"ignore\s+(all\s+)?(previous|prior|system|developer)\s+instructions",
            re.IGNORECASE,
        ),
    ),
    (
        "credential_theft",
        re.compile(
            r"(\.ssh/id_rsa|\.aws/credentials|browser\s+cookies?|steal\s+.*token|"
            r"exfiltrat\w*\s+.*(secret|token|credential))",
            re.IGNORECASE,
        ),
    ),
    (
        "destructive_shell",
        re.compile(
            r"(rm\s+-rf\s+/(?:\s|$)|format\s+[a-z]:|del\s+/f\s+/s\s+/q\s+[a-z]:\\)",
            re.IGNORECASE,
        ),
    ),
)


class SkillValidationError(ValueError):
    pass


def normalize_github_skill_url(url: str) -> str:
    """Accept only GitHub-hosted SKILL.md source and normalize blob URLs."""
    clean = url.strip()
    parsed = urlparse(clean)
    if parsed.scheme != "https":
        raise SkillValidationError("Only HTTPS GitHub URLs are allowed.")
    host = (parsed.hostname or "").casefold()
    if host == "raw.githubusercontent.com":
        if not parsed.path.casefold().endswith("/skill.md"):
            raise SkillValidationError("URL must point to a SKILL.md file.")
        return clean
    if host != "github.com":
        raise SkillValidationError("Only github.com or raw.githubusercontent.com is allowed.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 5 or parts[2] != "blob":
        raise SkillValidationError("GitHub URL must be a blob link to SKILL.md.")
    if parts[-1].casefold() != "skill.md":
        raise SkillValidationError("URL must point to SKILL.md.")
    owner, repo, _, ref, *path = parts
    return (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/"
        + "/".join(path)
    )


def validate_skill_document(content: str) -> dict[str, Any]:
    """Perform bounded static validation; Markdown is never executed."""
    encoded = content.encode("utf-8")
    if not encoded or len(encoded) > _MAX_SKILL_BYTES:
        raise SkillValidationError(
            f"SKILL.md must be between 1 and {_MAX_SKILL_BYTES} UTF-8 bytes."
        )
    if not content.startswith("---\n"):
        raise SkillValidationError("SKILL.md must begin with YAML-style frontmatter.")

    closing = content.find("\n---\n", 4)
    if closing < 0:
        raise SkillValidationError("SKILL.md frontmatter is not closed.")
    frontmatter = content[4:closing]
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip().casefold()] = value.strip().strip('"').strip("'")

    name = fields.get("name", "").casefold().replace("_", "-").replace(" ", "-")
    name = re.sub(r"[^a-z0-9-]+", "-", name).strip("-")
    if not _SLUG_RE.fullmatch(name):
        raise SkillValidationError("Frontmatter must contain a safe name/slug.")
    description = fields.get("description", "").strip()
    if len(description) < 8:
        raise SkillValidationError("Frontmatter description is missing or too short.")

    findings = [
        finding
        for finding, pattern in _CRITICAL_PATTERNS
        if pattern.search(content)
    ]
    if findings:
        raise SkillValidationError(
            "Static security scan blocked this skill: " + ", ".join(findings)
        )
    digest = hashlib.sha256(encoded).hexdigest()
    return {
        "slug": name,
        "description": description,
        "sha256": digest,
        "bytes": len(encoded),
        "security_findings": [],
        "validation": "static-non-executable",
    }


def _registry_path() -> Path:
    return managed_root() / "xfcc" / "community-skills.json"


def _backup_root() -> Path:
    return managed_root() / "xfcc" / "skill-backups"


def _load_registry() -> dict[str, Any]:
    path = _registry_path()
    if not path.exists():
        return {"skills": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"skills": {}}
    return data if isinstance(data, dict) else {"skills": {}}


def _save_registry(data: dict[str, Any]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _require_slug(slug: str) -> str:
    normalized = slug.strip().casefold()
    if not _SLUG_RE.fullmatch(normalized):
        raise SkillValidationError("Invalid community skill slug.")
    return normalized


def _skill_path(slug: str) -> Path:
    safe_slug = _require_slug(slug)
    return skills_root() / f"community-{safe_slug}" / "SKILL.md"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _backup(slug: str, source: Path) -> str | None:
    if not source.is_file():
        return None
    target = _backup_root() / slug / f"{_timestamp()}-{source.stat().st_size}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return str(target)


def install_community_skill(
    content: str,
    *,
    source_url: str,
) -> dict[str, Any]:
    """Install or update one validated community skill with automatic backup."""
    validation = validate_skill_document(content)
    slug = str(validation["slug"])
    path = _skill_path(slug)
    backup = _backup(slug, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)

    registry = _load_registry()
    raw_skills = registry.get("skills")
    skills = raw_skills if isinstance(raw_skills, dict) else {}
    prior = skills.get(slug)
    backups: list[str] = []
    if isinstance(prior, dict):
        raw_backups = prior.get("backups")
        if isinstance(raw_backups, list):
            backups.extend(str(item) for item in raw_backups)
    if backup is not None:
        backups.append(backup)
    skills[slug] = {
        "slug": slug,
        "description": validation["description"],
        "source_url": source_url,
        "sha256": validation["sha256"],
        "enabled": True,
        "installed_at": datetime.now(UTC).isoformat(),
        "backups": backups[-10:],
    }
    registry["skills"] = skills
    _save_registry(registry)
    return {"ok": True, **validation, "enabled": True, "updated": backup is not None}


def community_skill_status() -> dict[str, Any]:
    registry = _load_registry()
    raw = registry.get("skills")
    entries = raw if isinstance(raw, dict) else {}
    result = []
    for slug, value in sorted(entries.items()):
        if not isinstance(value, dict):
            continue
        item = dict(value)
        item["present"] = _skill_path(str(slug)).is_file()
        item["backup_count"] = len(item.get("backups", []))
        result.append(item)
    return {"skills": result, "root": str(skills_root())}


def disable_community_skill(slug: str) -> dict[str, Any]:
    slug = _require_slug(slug)
    path = _skill_path(slug)
    registry = _load_registry()
    skills = registry.get("skills")
    if not isinstance(skills, dict) or slug not in skills:
        raise SkillValidationError("Community skill is not registered.")
    entry = skills[slug]
    if not isinstance(entry, dict):
        raise SkillValidationError("Community skill registry entry is invalid.")
    snapshot = _backup(slug, path)
    if snapshot is not None:
        path.unlink()
        backups = entry.get("backups")
        existing = list(backups) if isinstance(backups, list) else []
        existing.append(snapshot)
        entry["backups"] = existing[-10:]
    entry["enabled"] = False
    _save_registry(registry)
    return {"ok": True, "slug": slug, "enabled": False}


def enable_community_skill(slug: str) -> dict[str, Any]:
    slug = _require_slug(slug)
    registry = _load_registry()
    skills = registry.get("skills")
    if not isinstance(skills, dict) or slug not in skills:
        raise SkillValidationError("Community skill is not registered.")
    entry = skills[slug]
    if not isinstance(entry, dict):
        raise SkillValidationError("Community skill registry entry is invalid.")
    if _skill_path(slug).is_file():
        entry["enabled"] = True
        _save_registry(registry)
        return {"ok": True, "slug": slug, "enabled": True}

    backups = entry.get("backups")
    candidates = list(backups) if isinstance(backups, list) else []
    if not candidates:
        raise SkillValidationError("No snapshot is available to enable this skill.")
    source = Path(str(candidates[-1]))
    if not source.is_file():
        raise SkillValidationError("Latest skill snapshot is missing.")
    target = _skill_path(slug)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    entry["enabled"] = True
    _save_registry(registry)
    return {"ok": True, "slug": slug, "enabled": True}


def rollback_community_skill(slug: str) -> dict[str, Any]:
    slug = _require_slug(slug)
    registry = _load_registry()
    skills = registry.get("skills")
    if not isinstance(skills, dict) or slug not in skills:
        raise SkillValidationError("Community skill is not registered.")
    entry = skills[slug]
    if not isinstance(entry, dict):
        raise SkillValidationError("Community skill registry entry is invalid.")
    backups = entry.get("backups")
    candidates = list(backups) if isinstance(backups, list) else []
    if not candidates:
        raise SkillValidationError("No previous version is available.")
    source = Path(str(candidates.pop()))
    if not source.is_file():
        raise SkillValidationError("Previous version snapshot is missing.")
    target = _skill_path(slug)
    _backup(slug, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    entry["backups"] = candidates
    entry["enabled"] = True
    entry["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    entry["installed_at"] = datetime.now(UTC).isoformat()
    _save_registry(registry)
    return {"ok": True, "slug": slug, "enabled": True, "rolled_back": True}
