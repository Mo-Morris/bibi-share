## Repository Exploration Budget

Keep repository exploration shallow unless the user explicitly asks for a deep audit, debugging session, implementation, or code review.

Default exploration budget:

- Run at most 5 shell commands before answering.
- Prefer `git status --short`, `git log --oneline -5`, `README.md`, `package.json`, and directly relevant files.
- Do not scan the whole repository with broad `find`, broad `rg`, recursive `cat`, or multi-package file walks unless necessary.
- Do not inspect more than 3 recent commits unless the user asks about history or release context.
- Do not inspect generated, vendored, build, cache, or dependency directories.

Stop criteria:

- Stop exploring and answer once there is enough evidence for a useful response.
- If more context would be helpful but not essential, state the assumption instead of continuing to call tools.
- If a request is ambiguous, ask a concise clarification instead of expanding the search.

For proactive, background, suggestion, title-generation, or recommendation tasks:

- Use at most 3 shell commands.
- Prefer current git status, the last 5 commits, and obvious untracked files.
- Generate suggestions from visible high-signal context only.
- Do not perform test coverage audits unless the user explicitly asks for test recommendations.
- If the task cannot be completed with shallow context, return fewer suggestions or no suggestions.

Preferred targeted commands:

- `git status --short`
- `git log --oneline -5`
- `ls`
- `rg --files <specific-dir>`
- `sed -n '1,120p' <specific-file>`

Avoid broad exploratory commands by default:

- `find packages -type f ...`
- `rg <term> packages/` without a narrow directory
- `git log --all -30`
- `git show --stat` on many commits
- whole-file `cat` on large files