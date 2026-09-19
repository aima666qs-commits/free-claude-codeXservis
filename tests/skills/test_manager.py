from pathlib import Path

from free_claude_code.skills.catalog import BUILTIN_SKILLS
from free_claude_code.skills.manager import managed_skill_status, sync_managed_skills


def test_sync_is_idempotent_and_preserves_existing_global_claude_md(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("XFCC_HOME", str(tmp_path))
    global_file = tmp_path / ".claude" / "CLAUDE.md"
    global_file.parent.mkdir(parents=True)
    global_file.write_text("# Existing user rules\n", encoding="utf-8")

    first = sync_managed_skills()
    second = sync_managed_skills()

    assert first["skill_count"] == len(BUILTIN_SKILLS)
    assert first["changed_skills"]
    assert second["changed_skills"] == []
    text = global_file.read_text(encoding="utf-8")
    assert "# Existing user rules" in text
    assert text.count("XFCC MANAGED MEMORY START") == 1

    status = managed_skill_status()
    assert all(item["state"] == "current" for item in status["skills"])
    assert status["memory"]["state"] == "current"


def test_sync_updates_only_xfcc_owned_skill_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XFCC_HOME", str(tmp_path))
    foreign = tmp_path / ".claude" / "skills" / "third-party" / "SKILL.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("third party", encoding="utf-8")

    sync_managed_skills()

    assert foreign.read_text(encoding="utf-8") == "third party"
    for skill in BUILTIN_SKILLS:
        assert (
            tmp_path / ".claude" / "skills" / f"xfcc-{skill.slug}" / "SKILL.md"
        ).is_file()
