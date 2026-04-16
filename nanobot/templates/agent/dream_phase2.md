<dream_update>
Update memory files based on the analysis below.

**Entry types:**
- `[FILE]` → add content to the appropriate file
- `[FILE-REMOVE]` → delete corresponding content from memory
- `[SKILL]` → create skill under `skills/<name>/SKILL.md` via write_file

<file_paths>
- SOUL.md
- USER.md
- memory/MEMORY.md
- skills/<name>/SKILL.md (for `[SKILL]` entries only)
</file_paths>

<editing_rules>
1. Edit directly — file contents provided below, no read_file needed
2. Use exact text as old_text, include surrounding blank lines for unique match
3. Batch changes to the same file into one edit_file call
4. For deletions: section header + all bullets as old_text, new_text empty
5. Surgical edits only — never rewrite entire files
6. If nothing to update, stop without calling tools
</editing_rules>

<skill_creation>
1. Use write_file to create `skills/<name>/SKILL.md`
2. Read `{{ skill_creator_path }}` for format reference before writing
3. **Dedup check**: read existing skills listed below — skip if one already covers the same workflow
4. Include YAML frontmatter with name and description fields
5. Keep SKILL.md under 2000 words — concise and actionable
6. Include: when to use, steps, output format, at least one example
7. Do NOT overwrite existing skills — skip if directory already exists
8. Reference specific tools the agent has access to (read_file, write_file, exec, web_search, etc.)
9. Skills are instruction sets, not code — do not include implementation
</skill_creation>

<quality>
- Every line must carry standalone value
- Concise bullets under clear headers
- When reducing (not deleting): keep essential facts, drop verbose details
- If uncertain whether to delete, keep but add "(verify currency)"
</quality>
</dream_update>