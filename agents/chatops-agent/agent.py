#!/usr/bin/env python3
"""
ChatOps Agent (LangChain + Ollama)
---------------------------------------
Answers natural-language questions about Jenkins build failures. Fetches
the console log via Jenkins' REST API (live mode) or reads a saved log
file (offline/test mode), and uses a local LLM to summarize what went
wrong in plain English.

Usage:
    Live mode (Jenkins running):
        python3 agent.py --build-url http://<jenkins-ip>:8080/job/<job>/<build-num>/ \\
            --user <username> --token <api-token>

    Offline/test mode (saved log file):
        python3 agent.py --log-file <path-to-console-log.txt>
"""

import sys
import argparse
from datetime import datetime, UTC

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

MODEL_NAME = "llama3.2"
MAX_LOG_CHARS = 8000  # keep prompt reasonable; we care most about the tail of the log


def fetch_console_log_live(build_url, user, token):
    import urllib.request
    import base64

    log_url = build_url.rstrip("/") + "/consoleText"
    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    req = urllib.request.Request(log_url, headers={"Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode(errors="replace")


def load_console_log_file(path):
    with open(path) as f:
        return f.read()


def trim_log(log_text):
    """Keep the tail of the log — failures usually appear near the end,
    and local models handle shorter context better."""
    if len(log_text) > MAX_LOG_CHARS:
        return "... [earlier log truncated] ...\n" + log_text[-MAX_LOG_CHARS:]
    return log_text


def build_llm_prompt(log_text, question):
    system_prompt = (
        "You are a ChatOps assistant for a Jenkins CI/CD pipeline. "
        "Engineers ask you why a build failed, and you read the raw "
        "console log and explain it in plain English. Point to the "
        "specific stage or command that failed, quote the key error line, "
        "and suggest one likely fix. Be concise — engineers are asking "
        "this to save time, not read another wall of text."
    )

    user_prompt = f"""Question: {question}

Jenkins console log (tail):
{log_text}

Answer:
1. Which stage/step failed (name it specifically).
2. The key error line, quoted.
3. Most likely cause and one suggested fix.
"""
    return system_prompt, user_prompt


def run_chatops_agent(log_text, question):
    llm = ChatOllama(model=MODEL_NAME, temperature=0.2)
    system_prompt, user_prompt = build_llm_prompt(log_text, question)

    print("\nAsking " + MODEL_NAME + " to analyze the build log... (may take a bit on CPU)\n")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return response.content


def write_answer_file(llm_output, out_path="chatops-answer.md"):
    lines = [
        "# ChatOps Agent Answer",
        "",
        "**Generated:** " + datetime.now(UTC).isoformat(),
        "**Model:** " + MODEL_NAME + " (via Ollama, local inference)",
        "",
        llm_output,
    ]
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print("Answer written to " + out_path)


def main():
    parser = argparse.ArgumentParser(description="ChatOps agent for Jenkins build failures")
    parser.add_argument("--build-url", help="Jenkins build URL (live mode)")
    parser.add_argument("--user", help="Jenkins username (live mode)")
    parser.add_argument("--token", help="Jenkins API token (live mode)")
    parser.add_argument("--log-file", help="Path to a saved console log (offline/test mode)")
    parser.add_argument("--question", default="Why did this build fail?",
                         help="Natural-language question to ask about the build")
    args = parser.parse_args()

    if args.log_file:
        log_text = load_console_log_file(args.log_file)
    elif args.build_url and args.user and args.token:
        log_text = fetch_console_log_live(args.build_url, args.user, args.token)
    else:
        print("Provide either --log-file (offline) or --build-url --user --token (live)")
        sys.exit(1)

    log_text = trim_log(log_text)

    print("\n" + "=" * 70)
    print("CHATOPS AGENT")
    print("Generated: " + datetime.now(UTC).isoformat())
    print("=" * 70 + "\n")
    print("Question: " + args.question + "\n")

    llm_output = run_chatops_agent(log_text, args.question)

    print("-" * 70)
    print("ANSWER:")
    print("-" * 70)
    print(llm_output)
    print()

    write_answer_file(llm_output)


if __name__ == "__main__":
    main()
