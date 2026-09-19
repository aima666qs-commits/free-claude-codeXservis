"""Small local aggregate telemetry store for managed skill routing."""

import json
import threading
from pathlib import Path
from typing import Any

from .manager import managed_root

_LOCK = threading.Lock()
_SCHEMA_VERSION = 1


def _path() -> Path:
    return managed_root() / "xfcc" / "skill-router-telemetry.json"


def _empty() -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "total_requests": 0,
        "routed_requests": 0,
        "total_selected_skills": 0,
        "estimated_original_tokens": 0,
        "estimated_injected_tokens": 0,
        "skill_hits": {},
        "last_selected": [],
    }


def _read() -> dict[str, Any]:
    path = _path()
    if not path.exists():
        return _empty()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return _empty()
    return raw if isinstance(raw, dict) else _empty()


def _write(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def record_skill_route(
    slugs: tuple[str, ...],
    *,
    estimated_original_tokens: int,
    estimated_injected_tokens: int,
) -> None:
    """Record aggregate counts only; never persist request text or secrets."""
    with _LOCK:
        data = _read()
        data["total_requests"] = int(data.get("total_requests", 0)) + 1
        if slugs:
            data["routed_requests"] = int(data.get("routed_requests", 0)) + 1
        data["total_selected_skills"] = int(data.get("total_selected_skills", 0)) + len(
            slugs
        )
        data["estimated_original_tokens"] = int(
            data.get("estimated_original_tokens", 0)
        ) + max(0, estimated_original_tokens)
        data["estimated_injected_tokens"] = int(
            data.get("estimated_injected_tokens", 0)
        ) + max(0, estimated_injected_tokens)
        raw_hits = data.get("skill_hits")
        hits = raw_hits if isinstance(raw_hits, dict) else {}
        for slug in slugs:
            hits[slug] = int(hits.get(slug, 0)) + 1
        data["skill_hits"] = hits
        data["last_selected"] = list(slugs)
        _write(data)


def skill_telemetry() -> dict[str, Any]:
    """Return aggregates plus derived routing/overhead metrics."""
    with _LOCK:
        data = _read()
    total = max(0, int(data.get("total_requests", 0)))
    routed = max(0, int(data.get("routed_requests", 0)))
    original = max(0, int(data.get("estimated_original_tokens", 0)))
    injected = max(0, int(data.get("estimated_injected_tokens", 0)))
    data["route_rate_pct"] = round((routed / total * 100.0), 2) if total else 0.0
    data["estimated_context_overhead_pct"] = (
        round((injected / original * 100.0), 2) if original else 0.0
    )
    return data


def reset_skill_telemetry() -> dict[str, Any]:
    with _LOCK:
        data = _empty()
        _write(data)
    return data
