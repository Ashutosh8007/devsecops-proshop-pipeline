# Deployment Gatekeeper Agent

Composes outputs from the Security Triage Agent and a SonarQube quality
gate result to produce a single final GO/NO-GO deployment decision. Uses
a local LLM (Ollama, llama3.2) via LangChain to reason about tradeoffs
between security and code quality signals, rather than a hardcoded rule.

## Why compose two agents instead of one big check?

Each upstream agent focuses on a single concern (security, quality). The
gatekeeper's job is reconciliation — deciding what to do when signals
disagree (e.g. security fails but quality passes). This mirrors how a
real release manager would weigh multiple, sometimes-conflicting reports
before approving a deployment.

## Usage

```bash
python3 agent.py <triage-report.md> <sonarqube-status.json>
```

Exits non-zero on a NO-GO verdict — a Jenkins pipeline stage can check
this exit code (or grep `gate-decision.txt` for `FINAL VERDICT: NO-GO`)
to block deployment automatically.

## Sample run

Tested against a real Security Triage Agent NO-GO verdict (5 CRITICAL
CVEs in proshop-backend) composed with a passing simulated SonarQube
quality gate. The agent correctly prioritized the security failure over
the passing quality gate and blocked deployment.
