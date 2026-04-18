# Dream Analysis

Compare conversation history against current memory files. Also scan memory files for stale content — even if not mentioned in history.

**Output format** — one line per finding:
- `[FILE] atomic fact` (not already in memory)
- `[FILE-REMOVE] reason for removal`
- `[SKILL] kebab-case-name: one-line description`

Files: USER (identity, preferences), SOUL (bot behavior, tone), MEMORY (knowledge, project context)

## Extraction Rules

1. Atomic facts only: "has a cat named Luna" not "discussed pet care"
2. Corrections override: `[USER] location is Tokyo, not Osaka`
3. Capture confirmed approaches the user validated

## Staleness Rules

Flag as `[FILE-REMOVE]` when any apply:
- Time-sensitive data older than 14 days (weather, daily status, one-time meetings, passed events)
- Completed one-time tasks (triage, reviews, finished research, resolved incidents)
- Resolved tracking (merged/closed PRs, fixed issues, completed migrations)
- Detailed incident info after 14 days — reduce to one-line summary
- Superseded approaches replaced by newer solutions or deprecated dependencies

## Skill Discovery

Flag `[SKILL]` only when ALL conditions are true:
1. A specific, repeatable workflow appeared 2+ times in conversation history
2. It involves clear steps (not vague preferences like "likes concise answers")
3. It is substantial enough to warrant its own instruction set (not trivial like "read a file")

Duplicates are acceptable — the next phase deduplicates against existing skills.

Do not add: current weather, transient status, temporary errors, conversational filler.

Output `[SKIP]` if nothing needs updating.
