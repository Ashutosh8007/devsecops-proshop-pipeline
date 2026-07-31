#!/usr/bin/env python3
"""
Code Review Agent (LangChain + Ollama)
------------------------------------------
Reads a git diff and (optionally) SonarQube metrics, and uses a local LLM
to write a PR-review-style comment: what looks risky, what's good practice,
and what the author should double-check before merging.

Usage:
    python3 agent.py <diff-file.txt> [sonarqube-metrics.json]
"""

import json
import sys
from datetime import datetime, UTC

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

MODEL_NAME = "llama3.2"
MAX_DIFF_CHARS = 6000


def load_diff(path):
    with open(path) as f:
        content = f.read()
    if len(content) > MAX_DIFF_CHARS:
        content = content[:MAX_DIFF_CHARS] + "\n\n... [diff truncated for length] ..."
    return content


def load_sonarqube_metrics(path):
    if not path:
        return None
    with open(path) as f:
        return json.load(f)


def build_llm_prompt(diff_text, sq_metrics):
    system_prompt = (
        "You are a senior software engineer performing a code review. "
        "You review git diffs and write a concise, constructive PR comment. "
        "Point out real risks (security, error handling, edge cases), "
        "acknowledge good practices you see, and suggest concrete "
        "improvements. Do not nitpick formatting. Be direct but respectful, "
        "the way a helpful senior colleague would comment on a PR."
    )

    sq_context = ""
    if sq_metrics:
        status = sq_metrics.get("projectStatus", {})
        sq_context = "\n\nSonarQube quality gate status: " + status.get("status", "unknown")

    user_prompt = "Review this code diff and write a PR comment:\n\n```diff\n" + diff_text + "\n```" + sq_context + """

Write:
1. A one-sentence overall impression.
2. Specific risks or concerns (bullet points, cite the actual code if relevant).
3. Anything done well (if applicable).
4. A recommendation: "RECOMMENDATION: APPROVE", "RECOMMENDATION: APPROVE WITH COMMENTS", or "RECOMMENDATION: REQUEST CHANGES"
"""
    return system_prompt, user_prompt


def run_code_review(diff_text, sq_metrics):
    llm = ChatOllama(model=MODEL_NAME, temperature=0.2)
    system_prompt, user_prompt = build_llm_prompt(diff_text, sq_metrics)

    print("\nAsking " + MODEL_NAME + " to review the diff... (may take a bit on CPU)\n")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def write_review_file(llm_output, out_path="review-comment.md"):
    lines = [
        "# Code Review (AI-assisted)",
        "",
        "**Generated:** " + datetime.now(UTC).isoformat(),
        "**Model:** " + MODEL_NAME + " (via Ollama, local inference)",
        "",
        llm_output,
    ]
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print("Review written to " + out_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py <diff-file.txt> [sonarqube-metrics.json]")
        sys.exit(1)

    diff_text = load_diff(sys.argv[1])
    sq_metrics = load_sonarqube_metrics(sys.argv[2]) if len(sys.argv) > 2 else None

    print("\n" + "=" * 70)
    print("CODE REVIEW AGENT")
    print("Generated: " + datetime.now(UTC).isoformat())
    print("=" * 70 + "\n")

    llm_output = run_code_review(diff_text, sq_metrics)

    print("-" * 70)
    print("REVIEW COMMENT:")
    print("-" * 70)
    print(llm_output)
    print()

    write_review_file(llm_output)


if __name__ == "__main__":
    main()
