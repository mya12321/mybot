<fact_extraction>
Extract key facts from this conversation. Only output items matching these categories:

- **User facts**: personal info, preferences, stated opinions, habits
- **Decisions**: choices made, conclusions reached
- **Solutions**: working approaches discovered through trial and error, especially non-obvious methods that succeeded after failed attempts
- **Events**: plans, deadlines, notable occurrences
- **Preferences**: communication style, tool preferences

**Priority order:** user corrections and preferences > solutions > decisions > events > environment facts.
The most valuable memory prevents the user from having to repeat themselves.

**Skip:** code patterns derivable from source, git history, or anything already in existing memory.

Output as concise bullet points, one fact per line. No preamble, no commentary.
If nothing noteworthy, output: `(nothing)`
</fact_extraction>