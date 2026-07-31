# Security Triage Agent

Uses a local LLM (Ollama, llama3.2) via LangChain to reason over Trivy
vulnerability scan results and produce a human-readable triage summary
with a GO/NO-GO deployment recommendation.

## Why an LLM instead of just sorting by severity?

A plain script can sort CVEs by severity, but it can't reason about which
findings actually matter in context (e.g. is the fix available? is this a
runtime or dev-only dependency?). The LLM reads the raw findings and writes
a prioritized, human-readable recommendation — closer to what a security
engineer would produce during triage.

## Usage

```bash
python3 agent.py <path-to-trivy-report.json> [--create-issue]
```

Requires Ollama running locally with `llama3.2` pulled. `--create-issue`
opens a GitHub issue automatically if the verdict is NO-GO (requires
`GITHUB_TOKEN` and `GITHUB_REPO` env vars).

## Sample output

See `triage-report.md` for a real run against
`ashutosh8007/proshop-backend:latest` (109 findings, 5 CRITICAL).
