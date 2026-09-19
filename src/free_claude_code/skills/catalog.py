"""Built-in managed skills distilled from the reviewed workflow videos."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ManagedSkill:
    slug: str
    title: str
    purpose: str
    body: str


def _skill(slug: str, title: str, purpose: str, body: str) -> ManagedSkill:
    return ManagedSkill(\n        slug=slug, title=title, purpose=purpose, body=body.strip() + "\n"\n    )


BUILTIN_SKILLS: tuple[ManagedSkill, ...] = (
    _skill(
        "discovery-interview",
        "Discovery Interview",
        "Turn an underspecified idea into an implementation-ready brief before coding.",
        """
# Discovery Interview

Use this skill when the request is broad, ambiguous, expensive to reverse, or likely to hide product requirements.

## Goal
Convert a raw idea into a concise implementation contract. Do not interrogate the user mechanically. Ask only questions whose answers materially change architecture, scope, UX, constraints, data, integrations, rollout, or acceptance criteria.

## Protocol
1. Inspect the existing project before asking questions.
2. Infer everything safely inferable from the codebase and prior decisions.
3. Ask a small batch of high-value questions, normally 3-7.
4. Cover only relevant dimensions: user, job-to-be-done, target platforms, data, auth, integrations, success criteria, constraints, UX direction, edge cases, migration, rollout.
5. After answers, produce:
   - problem statement;
   - users and jobs;
   - in-scope / out-of-scope;
   - functional requirements;
   - UX flow;
   - technical design;
   - data and API changes;
   - risks and mitigations;
   - test/acceptance checklist;
   - ordered execution plan.
6. If the user explicitly says to proceed autonomously, infer low-risk details and continue instead of blocking on non-essential questions.

Prefer implementation-ready specificity over long prose.
""",
    ),
    _skill(
        "request-orchestrator",
        "Request Orchestrator",
        "Make short requests usable by recovering context, asking targeted questions, and selecting the right output contract.",
        """
# Request Orchestrator

Use when the user gives a one-line task but expects a complete result.

## Operating contract
- Investigate before answering: inspect referenced files, current state, and existing implementation.
- Recover relevant project context before asking the user to repeat it.
- Ask only questions that alter the result materially.
- Infer ordinary implementation details from conventions in the repository.
- Convert the request into an internal execution contract:
  objective, constraints, inputs, missing facts, definition of done, verification.
- Default to acting when the user asked for implementation.
- Preserve existing architecture unless change is necessary.
- Finish with a verified result, not a generic plan.

## Output discipline
For implementation tasks, report changed behavior, files, verification, remaining blockers, and measurable impact. Do not expose hidden chain-of-thought.
""",
    ),
    _skill(
        "humanizer",
        "Humanizer",
        "Remove formulaic AI phrasing while preserving technical precision and the requested voice.",
        """
# Humanizer

Use for user-facing prose, UI copy, marketing copy, explanations, and long-form writing when natural language quality matters.

## Rules
- Preserve facts, intent, terminology, and requested tone.
- Prefer concrete verbs and specific nouns.
- Vary sentence length naturally.
- Remove canned openings, filler conclusions, fake enthusiasm, repetitive summaries, and template phrases.
- Avoid excessive em dashes, stacked headings, and obvious LLM rhythm.
- Do not manufacture anecdotes, emotions, personal experience, citations, or certainty.
- Keep technical writing precise; humanization must never reduce correctness.
- Match the audience and medium rather than applying one universal style.

Return only the improved text when the task is purely editorial.
""",
    ),
    _skill(
        "ui-ux-pro",
        "UI UX Pro",
        "Apply production-grade interface heuristics instead of generic AI-generated UI.",
        """
# UI UX Pro

Use for product UI, dashboards, websites, mobile screens, component systems, and visual polish.

## Process
1. Inspect the existing design system, tokens, components, routes, and responsive behavior.
2. Define the visual hierarchy and primary user journey before styling.
3. Reuse existing components before adding new abstractions.
4. Validate accessibility: contrast, focus, keyboard flow, hit targets, labels, reduced motion.
5. Validate responsive states, loading, empty, error, success, disabled, and destructive states.
6. Prefer a coherent visual language over isolated decorative effects.
7. Avoid generic AI aesthetics: default purple gradients, random glassmorphism, excessive cards, uniform spacing with no hierarchy, novelty animation without purpose.
8. Use typography, spacing, color, depth, motion, and density as a system.

## Quality gates
- Critical action visible and unambiguous.
- No layout breakage at mobile/tablet/desktop widths.
- Components have consistent states.
- Text is readable and localized.
- Animation supports comprehension.
- The result still feels native to the existing product.
""",
    ),
    _skill(
        "design-reference",
        "Design Reference",
        "Convert design.md, screenshots, brand references, or typography samples into reusable implementation constraints.",
        """
# Design Reference

Use when the user provides design.md, screenshots, a reference site, typography, imagery, or a brand object/style to reuse.

## Extract
Create a compact reference model containing:
- visual principles and mood;
- typography roles and scale;
- color tokens;
- spacing and grid;
- radii, borders, elevation;
- component patterns;
- imagery/illustration treatment;
- motion rules;
- responsive behavior;
- explicit do / avoid constraints.

## Implementation
- Treat the reference as a design system, not a screenshot to trace blindly.
- Preserve the current product architecture and accessibility.
- When combining a type sample with an object/material reference, separate letterform structure from material/style treatment, then combine them deliberately.
- Store reusable project-specific rules in a local design.md only when the user asked for persistence or the project already uses that convention.
- Verify the final result visually when browser or screenshot tools are available.
""",
    ),
    _skill(
        "context-engineering",
        "Context Engineering",
        "Reduce wasted context and token use while preserving decisions, evidence, and execution continuity.",
        """
# Context Engineering

Use on long-running coding tasks, large repositories, repeated agent loops, or when limits/cost matter.

## Context budget
- Read the smallest set of files that can answer the current question.
- Prefer targeted search and bounded ranges over dumping whole repositories.
- Keep stable instructions separate from transient task notes.
- Summarize completed phases into decisions, changed files, tests, blockers, and next step.
- Do not repeatedly reload unchanged large files.
- Reuse concrete identifiers and prior tool outputs.
- Remove temporary context once it no longer affects the task.
- Put high-value evidence close to the decision it supports.
- When context becomes large, checkpoint state before compaction.

## Checkpoint format
Objective:
Current state:
Decisions:
Changed files:
Verification:
Open blockers:
Next action:

Token reduction is secondary to correctness. Never omit evidence needed to avoid a wrong edit.
""",
    ),
    _skill(
        "persistent-memory",
        "Persistent Project Memory",
        "Carry decisions and project state across Claude Code sessions without bloating every prompt.",
        """
# Persistent Project Memory

Use for multi-session projects.

## Memory files
Prefer a project file at .claude/xfcc-memory.md for project-specific state. Keep it concise and non-secret.

Record only durable information:
- architecture and invariants;
- user-approved decisions;
- active integrations;
- important commands and paths;
- current blockers;
- release state;
- next concrete action.

Do not store passwords, API keys, auth tokens, private keys, or ephemeral logs.

## Update policy
At the end of a substantial task, update only facts that will matter next session. Remove stale entries. Keep the file compact enough to scan quickly.

## Start-of-session policy
If .claude/xfcc-memory.md exists, read it before making project claims. Verify mutable facts against the repository or runtime before acting.
""",
    ),
    _skill(
        "marketing-suite",
        "Marketing Suite",
        "Provide a structured multi-specialist marketing workflow including Threads, funnels, copy, lifecycle, and creative.",
        """
# Marketing Suite

Use only for marketing, growth, positioning, content, funnel, lifecycle, or campaign tasks.

Route the task through the smallest relevant specialist set:
positioning, audience research, offer, messaging, copywriting, landing page, SEO, content strategy, social strategy, Threads, Instagram, email, lifecycle, lead magnet, funnel, CRO, creative strategy, ad concepts, launch, retention, analytics, experimentation, partnerships, and editorial QA.

## Workflow
1. Establish offer, audience, channel, conversion event, constraints, and evidence.
2. Select specialists; do not run all modes by default.
3. Produce one coherent strategy, not 23 disconnected mini-answers.
4. Separate hypotheses from known facts.
5. Define measurable leading and lagging indicators.
6. Include experiments with stop/continue criteria.

## Threads mode
Use text-native distribution: strong opening claim, useful standalone body, conversation hooks, reply strategy, profile-to-offer bridge, and repeatable series. Do not claim that every post is guaranteed recommendation reach. Treat platform behavior as variable and verify current claims when decisions depend on them.
""",
    ),
    _skill(
        "remotion-video",
        "Remotion Video",
        "Create code-driven animated video with a reproducible Remotion workflow.",
        """
# Remotion Video

Use when the user asks for programmatic motion graphics, explainers, social clips, product demos, or reusable video templates.

## Workflow
1. Inspect whether Remotion already exists in the project.
2. Reuse project tokens, fonts, assets, and component conventions.
3. Define composition size, fps, duration, scenes, transitions, audio, captions, and render target.
4. Keep timing deterministic and data-driven.
5. Respect safe areas for vertical/social output.
6. Verify a representative frame sequence and run the project's render/typecheck commands.
7. Do not add Remotion to an unrelated project unless the user actually wants code-driven video.

Prefer reusable compositions over one-off hard-coded timelines.
""",
    ),
)
