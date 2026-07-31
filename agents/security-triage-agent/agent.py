#!/usr/bin/env python3
"""
Security Triage Agent (LangChain + Ollama)
--------------------------------------------
Parses a Trivy JSON vulnerability scan report, extracts CRITICAL/HIGH
findings, and uses a local LLM (via Ollama) to reason about which
vulnerabilities are most urgent and produce a human-readable triage
summary with a GO/NO-GO style recommendation.

Usage:
    python3 agent.py <path-to-trivy-report.json> [--create-issue]

Requires:
    - Ollama running locally with the llama3.2 model pulled
    - GITHUB_TOKEN and GITHUB_REPO env vars set (only if --create-issue is used)
"""

import json
import sys
import os
from collections import defaultdict
from datetime import datetime

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
SEVERITY_WEIGHT = {s: i for i, s in enumerate(SEVERITY_ORDER)}
MODEL_NAME = "llama3.2"


def load_report(path):
    with open(path) as f:
        return json.load(f)


def extract_findings(data):
    """Extract and rank all vulnerabilities across scan targets."""
    findings = []
    for result in data.get("Results", []):
        target = result.get("Target", "unknown")
        for vuln in result.get("Vulnerabilities", []):
            findings.append({
                "target": target,
                "id": vuln.get("VulnerabilityID"),
                "pkg": vuln.get("PkgName"),
                "installed_version": vuln.get("InstalledVersion"),
                "fixed_version": vuln.get("FixedVersion", "not available"),
                "severity": vuln.get("Severity", "UNKNOWN"),
                "title": vuln.get("Title", vuln.get("VulnerabilityID")),
            })
    findings.sort(key=lambda f: SEVERITY_WEIGHT.get(f["severity"], 99))

    counts = defaultdict(int)
    for f in findings:
        counts[f["severity"]] += 1

    return findings, counts


def build_llm_prompt(findings, counts, artifact_name):
    """Constructs the prompt sent to the LLM for reasoning."""
    top_priority = [f for f in findings if f["severity"] in ("CRITICAL", "HIGH")]

    findings_text = "\n".join(
        f"- [{f['severity']}] {f['id']} in package '{f['pkg']}' "
        f"(installed: {f['installed_version']}, fix available: {f['fixed_version']}) "
        f"on target '{f['target']}': {f['title']}"
        for f in top_priority[:30]  # cap to keep prompt reasonable for a local model
    )

    system_prompt = (
        "You are a security triage assistant for a DevSecOps pipeline. "
        "You review vulnerability scan findings and help engineers decide "
        "what to fix first. Be concise, practical, and avoid alarmism. "
        "Focus on exploitability and whether a fix is actually available."
    )

    user_prompt = f"""Artifact scanned: {artifact_name}

Severity counts: {dict(counts)}

Top CRITICAL/HIGH findings:
{findings_text if findings_text else "None."}

Based on this, write:
1. A 2-3 sentence overall risk assessment.
2. The top 3 findings an engineer should fix FIRST, with a one-line reason each.
3. A single verdict line at the end: either "VERDICT: GO" (safe to deploy) or
   "VERDICT: NO-GO" (should not deploy until fixed) — base this on whether
   there are CRITICAL vulnerabilities with an available fix that are being ignored.
"""
    return system_prompt, user_prompt


def run_llm_triage(findings, counts, artifact_name):
    llm = ChatOllama(model=MODEL_NAME, temperature=0.2)
    system_prompt, user_prompt = build_llm_prompt(findings, counts, artifact_name)

    print(f"\nAsking {MODEL_NAME} to reason over {len(findings)} findings... (this may take a bit on CPU)\n")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def print_summary(findings, counts, artifact_name, llm_output):
    print(f"\n{'='*70}")
    print(f"SECURITY TRIAGE REPORT (AI-assisted)")
    print(f"Artifact: {artifact_name}")
    print(f"Generated: {datetime.now(datetime.UTC).isoformat()}Z")
    print(f"{'='*70}\n")

    print("Severity breakdown:")
    for sev in SEVERITY_ORDER:
        if counts.get(sev):
            print(f"  {sev:10s}: {counts[sev]}")
    print(f"  {'TOTAL':10s}: {sum(counts.values())}\n")

    print("-" * 70)
    print("LLM TRIAGE ANALYSIS:")
    print("-" * 70)
    print(llm_output)
    print()


def write_markdown_report(counts, artifact_name, llm_output, out_path="triage-report.md"):
    lines = [
        f"# Security Triage Report (AI-assisted)",
        f"",
        f"**Artifact:** `{artifact_name}`  ",
        f"**Generated:** {datetime.now(datetime.UTC).isoformat()}Z  ",
        f"**Model:** {MODEL_NAME} (via Ollama, local inference)",
        f"",
        f"## Severity Breakdown",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
    ]
    for sev in SEVERITY_ORDER:
        if counts.get(sev):
            lines.append(f"| {sev} | {counts[sev]} |")
    lines.append(f"| **Total** | **{sum(counts.values())}** |")
    lines.append("")
    lines.append("## AI Triage Analysis")
    lines.append("")
    lines.append(llm_output)

    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))
    print(f"Markdown report written to {out_path}")


def create_github_issue(counts, artifact_name, llm_output):
    import urllib.request
    import urllib.error

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        print("GITHUB_TOKEN / GITHUB_REPO not set — skipping issue creation.")
        return

    if "VERDICT: NO-GO" not in llm_output:
        print("Agent verdict was not NO-GO — skipping issue creation (no action needed).")
        return

    body = f"**Automated AI security triage flagged this build as NO-GO.**\n\n{llm_output}"
    payload = json.dumps({
        "title": f"[Security Triage Agent] NO-GO verdict for {artifact_name}",
        "body": body,
        "labels": ["security", "automated", "no-go"]
    }).encode()

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"GitHub issue created: {result.get('html_url')}")
    except urllib.error.HTTPError as e:
        print(f"Failed to create issue: {e.code} {e.read().decode()}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py <trivy-report.json> [--create-issue]")
        sys.exit(1)

    report_path = sys.argv[1]
    create_issue_flag = "--create-issue" in sys.argv

    data = load_report(report_path)
    artifact_name = data.get("ArtifactName", "unknown artifact")

    findings, counts = extract_findings(data)
    llm_output = run_llm_triage(findings, counts, artifact_name)

    print_summary(findings, counts, artifact_name, llm_output)
    write_markdown_report(counts, artifact_name, llm_output)

    if create_issue_flag:
        create_github_issue(counts, artifact_name, llm_output)


if __name__ == "__main__":
    main()
