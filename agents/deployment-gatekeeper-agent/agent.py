#!/usr/bin/env python3
"""
Deployment Gatekeeper Agent (LangChain + Ollama)
---------------------------------------------------
Composes signals from multiple pipeline stages — Security Triage Agent
verdict + SonarQube quality gate status — and uses a local LLM to reason
about a final GO/NO-GO deployment decision. This is where individual
agents in the pipeline start acting as inputs to each other, rather than
standalone scripts.

Usage:
    python3 agent.py <triage-report.md> <sonarqube-status.json>
"""

import json
import sys
import re
from datetime import datetime, UTC

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

MODEL_NAME = "llama3.2"


def load_triage_report(path):
    with open(path) as f:
        return f.read()


def extract_triage_verdict(triage_text):
    """Pull the GO/NO-GO verdict line out of the triage agent's markdown output."""
    match = re.search(r"VERDICT:\s*(GO|NO-GO)", triage_text)
    return match.group(1) if match else "UNKNOWN"


def load_sonarqube_status(path):
    with open(path) as f:
        return json.load(f)


def summarize_sonarqube(sq_data):
    status = sq_data.get("projectStatus", {})
    overall = status.get("status", "UNKNOWN")
    conditions = status.get("conditions", [])
    failed = [c for c in conditions if c.get("status") != "OK"]
    return {
        "overall_status": overall,
        "total_conditions": len(conditions),
        "failed_conditions": failed,
    }


def build_llm_prompt(triage_text, triage_verdict, sq_summary):
    system_prompt = (
        "You are a deployment gatekeeper agent in a DevSecOps pipeline. "
        "You receive results from two upstream checks — a security triage "
        "agent and a SonarQube code quality gate — and must make a single "
        "final GO/NO-GO deployment decision. Security concerns should "
        "generally outweigh code quality concerns, since a security issue "
        "can be actively exploited while a quality issue is a longer-term "
        "maintenance risk. Be concise and decisive."
    )

    sq_conditions_text = "\n".join(
        f"- {c['metricKey']}: {c['status']} (actual: {c.get('actualValue')}, threshold: {c.get('comparator')} {c.get('errorThreshold')})"
        for c in sq_summary["failed_conditions"]
    ) or "All conditions passed."

    user_prompt = f"""You are reviewing a deployment candidate with two upstream reports:

## 1. Security Triage Agent Verdict
Verdict extracted: {triage_verdict}

Full triage summary:
{triage_text}

## 2. SonarQube Quality Gate
Overall status: {sq_summary['overall_status']}
Conditions checked: {sq_summary['total_conditions']}
Failed conditions:
{sq_conditions_text}

## Your task
Write:
1. A 2-3 sentence summary reconciling both signals.
2. Which signal is driving your final decision, and why.
3. A single final line: "FINAL VERDICT: GO" or "FINAL VERDICT: NO-GO"
"""
    return system_prompt, user_prompt


def run_gatekeeper(triage_text, triage_verdict, sq_summary):
    llm = ChatOllama(model=MODEL_NAME, temperature=0.2)
    system_prompt, user_prompt = build_llm_prompt(triage_text, triage_verdict, sq_summary)

    print(f"\nAsking {MODEL_NAME} to reconcile security + quality signals... (may take a bit on CPU)\n")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def write_gate_decision_file(llm_output, out_path="gate-decision.txt"):
    """Writes a simple parseable file a Jenkins pipeline stage could check,
    e.g. `if grep -q 'FINAL VERDICT: NO-GO' gate-decision.txt; then exit 1; fi`
    """
    with open(out_path, "w") as f:
        f.write(llm_output)
    print(f"Gate decision written to {out_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 agent.py <triage-report.md> <sonarqube-status.json>")
        sys.exit(1)

    triage_path, sq_path = sys.argv[1], sys.argv[2]

    triage_text = load_triage_report(triage_path)
    triage_verdict = extract_triage_verdict(triage_text)

    sq_data = load_sonarqube_status(sq_path)
    sq_summary = summarize_sonarqube(sq_data)

    print(f"\n{'='*70}")
    print(f"DEPLOYMENT GATEKEEPER AGENT")
    print(f"Generated: {datetime.now(UTC).isoformat()}")
    print(f"{'='*70}\n")
    print(f"Upstream signals:")
    print(f"  Security Triage Verdict : {triage_verdict}")
    print(f"  SonarQube Quality Gate  : {sq_summary['overall_status']} "
          f"({len(sq_summary['failed_conditions'])} failed / {sq_summary['total_conditions']} conditions)\n")

    llm_output = run_gatekeeper(triage_text, triage_verdict, sq_summary)

    print("-" * 70)
    print("GATEKEEPER DECISION:")
    print("-" * 70)
    print(llm_output)
    print()

    write_gate_decision_file(llm_output)

    if "FINAL VERDICT: NO-GO" in llm_output:
        print("Exiting with non-zero status (would block a real pipeline stage).")
        sys.exit(1)
    else:
        print("Exiting 0 (would allow pipeline to proceed).")
        sys.exit(0)


if __name__ == "__main__":
    main()
