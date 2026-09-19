# XFCC Project Memory

## Architecture
- FastAPI proxy with a local-only Admin UI.
- ProviderRuntimeManager owns provider generations, model discovery/cache, and graceful replacement.
- Provider catalog and Settings are the source of truth for model/provider configuration.
- Claude Code clients are launched through the FCC proxy environment.

## Invariants
- Never store secrets, API keys, OAuth tokens, private keys, or raw credentials in project memory.
- Keep /admin and /admin/api/* loopback-only.
- Managed XFCC skills may update only ~/.claude/skills/xfcc-*/SKILL.md.
- Never overwrite third-party or user-owned skills.
- Global ~/.claude/CLAUDE.md changes must remain additive and bounded by XFCC markers.
- Preserve active requests during provider-runtime replacement.

## Managed Claude layer
- Built-in managed skills: discovery-interview, request-orchestrator, humanizer, ui-ux-pro, design-reference, context-engineering, persistent-memory, marketing-suite, remotion-video.
- Skills synchronize automatically at FCC server startup.
- Admin endpoints: GET /admin/api/skills and POST /admin/api/skills/sync.
- Admin UI exposes a Skills + Memory view with status and manual re-sync.
- Project-specific durable context belongs in .claude/xfcc-memory.md.

## Verification
- Manager tests cover idempotency, preservation of existing CLAUDE.md content, and protection of third-party skills.
- Full repository CI must remain green before release.

## Next action
- Verify the feature branch in CI, reconcile any failures, then merge only after checks pass.
