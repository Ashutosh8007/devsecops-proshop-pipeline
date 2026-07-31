# Incident/Monitoring Agent

Reads a Prometheus/Alertmanager webhook payload and uses a local LLM
(Ollama, llama3.2) via LangChain to translate raw alert labels/annotations
into a plain-English incident summary with a likely root cause, a concrete
next diagnostic step, and an impact severity call.

## Why this over just reading the raw alert?

Raw Prometheus alerts are terse label/value pairs — useful for machines,
slow for humans under time pressure. This agent does the first-pass
translation a human on-call engineer would otherwise do manually: "what
does this actually mean, and what should I check first?"

## Usage

```bash
python3 agent.py <alert-payload.json>
```

Input matches Prometheus Alertmanager's real webhook JSON schema, so this
can be wired directly as an Alertmanager receiver in a live pipeline.

## Sample run

Tested against a simulated firing of the real `High Pod Restart Rate`
alert rule built in Phase 11 — correctly assessed it as low-impact
(single pod, self-healing) and suggested the right `kubectl describe`
diagnostic command.
