# ChatOps Agent

Answers natural-language questions about Jenkins build failures ("why did
build #X fail?") by reading the build's console log and using a local LLM
(Ollama, llama3.2) via LangChain to summarize the failure in plain English.

## Two modes

- **Live mode**: fetches the console log directly from a running Jenkins
  instance via its REST API (`--build-url`, `--user`, `--token`)
- **Offline/test mode**: reads a saved log file (`--log-file`) — useful
  for testing without a live Jenkins server, or replaying a past failure

## Usage

```bash
# Offline
python3 agent.py --log-file <console-log.txt> --question "Why did this build fail?"

# Live
python3 agent.py --build-url http://<jenkins-ip>:8080/job/<job>/<build-num>/ \
    --user <username> --token <api-token>
```

## Sample run

Tested against a simulated console log reproducing a real recurring
failure from this project's history (SonarQube unreachable under
resource contention). Correctly identified the failing stage, quoted the
exact error line, and suggested a plausible fix.
