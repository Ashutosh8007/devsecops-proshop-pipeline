# Code Review Agent

Reads a git diff (and optionally SonarQube metrics) and uses a local LLM
(Ollama, llama3.2) via LangChain to write a PR-review-style comment —
risks, good practices, and a merge recommendation — the way a senior
engineer would comment on a pull request.

## Why this over relying on SonarQube alone?

SonarQube catches known patterns (duplication, complexity, some security
rules) via static analysis. It can't reason about context — e.g. "this
function doesn't validate its JSON input" or "this error path will crash
instead of degrading gracefully." This agent reads the actual diff and
gives that contextual, human-style feedback.

## Usage

```bash
python3 agent.py <diff-file.txt> [sonarqube-metrics.json]
```

Generate a diff to test against:
```bash
git diff HEAD~1 HEAD > /tmp/latest.diff
python3 agent.py /tmp/latest.diff
```

## Sample run

Reviewed the real diff introducing the Incident/Monitoring Agent
(previous commit). Correctly flagged missing input validation, missing
error handling around the LLM call, and unguarded dict access on
optional alert fields — genuine, actionable findings, not generic praise.
