#!/usr/bin/env python3
"""
Incident/Monitoring Agent (LangChain + Ollama)
--------------------------------------------------
Reads a Prometheus/Alertmanager webhook payload and uses a local LLM to
translate raw alert data into a plain-English incident summary with
likely root cause and suggested next action — the kind of first-pass
triage a human on-call engineer would otherwise do manually.

Usage:
    python3 agent.py <alert-payload.json>
"""

import json
import sys
from datetime import datetime, UTC

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

MODEL_NAME = "llama3.2"


def load_alert_payload(path):
    with open(path) as f:
        return json.load(f)


def summarize_alerts(payload):
    alerts = payload.get("alerts", [])
    summaries = []
    for a in alerts:
        summaries.append({
            "name": a.get("labels", {}).get("alertname", "unknown"),
            "status": a.get("status", "unknown"),
            "severity": a.get("labels", {}).get("severity", "unknown"),
            "namespace": a.get("labels", {}).get("namespace", "unknown"),
            "pod": a.get("labels", {}).get("pod", "unknown"),
            "description": a.get("annotations", {}).get("description", ""),
            "starts_at": a.get("startsAt", "unknown"),
        })
    return summaries


def build_llm_prompt(alert_summaries):
    system_prompt = (
        "You are an on-call incident triage assistant for a Kubernetes "
        "platform. You receive raw Prometheus alert data and translate it "
        "into a plain-English summary a human engineer can quickly act on. "
        "Suggest a likely root cause and one concrete next diagnostic step. "
        "Be concise — this is meant to be read in under 15 seconds during "
        "an active incident."
    )

    alerts_text = "\n\n".join(
        f"Alert: {a['name']}\n"
        f"Status: {a['status']} | Severity: {a['severity']}\n"
        f"Namespace: {a['namespace']} | Pod: {a['pod']}\n"
        f"Description: {a['description']}\n"
        f"Started: {a['starts_at']}"
        for a in alert_summaries
    )

    user_prompt = f"""The following alert(s) fired:

{alerts_text}

Write:
1. A one-sentence plain-English summary of what's happening.
2. The most likely root cause (1-2 sentences, general Kubernetes knowledge is fine).
3. One concrete diagnostic command or step the engineer should run next.
4. A severity call: "IMPACT: LOW" / "IMPACT: MEDIUM" / "IMPACT: HIGH" based on
   whether this affects a single pod (usually low, since Kubernetes self-heals)
   vs. a systemic issue.
"""
    return system_prompt, user_prompt


def run_incident_agent(alert_summaries):
    llm = ChatOllama(model=MODEL_NAME, temperature=0.2)
    system_prompt, user_prompt = build_llm_prompt(alert_summaries)

    print(f"\nAsking {MODEL_NAME} to triage the incident... (may take a bit on CPU)\n")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def write_incident_report(llm_output, out_path="incident-report.md"):
    lines = [
        "# Incident Report (AI-assisted)",
        "",
        f"**Generated:** {datetime.now(UTC).isoformat()}",
        f"**Model:** {MODEL_NAME} (via Ollama, local inference)",
        "",
        "## AI Analysis",
        "",
        llm_output,
    ]
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Incident report written to {out_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py <alert-payload.json>")
        sys.exit(1)

    payload = load_alert_payload(sys.argv[1])
    alert_summaries = summarize_alerts(payload)

    print(f"\n{'='*70}")
    print(f"INCIDENT/MONITORING AGENT")
    print(f"Generated: {datetime.now(UTC).isoformat()}")
    print(f"{'='*70}\n")
    print(f"Alerts received: {len(alert_summaries)}\n")

    llm_output = run_incident_agent(alert_summaries)

    print("-" * 70)
    print("INCIDENT ANALYSIS:")
    print("-" * 70)
    print(llm_output)
    print()

    write_incident_report(llm_output)


if __name__ == "__main__":
    main()
