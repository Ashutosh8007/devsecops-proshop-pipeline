# Interview Explanation

## The 90-second version

I built a full DevSecOps pipeline from scratch on AWS free tier - Jenkins
for CI, SonarQube for code quality, Trivy for container scanning, and
Docker Hub for image storage. For deployment, I used Helm and ArgoCD to
do GitOps - the cluster state is fully declared in Git, and ArgoCD
auto-syncs and self-heals any drift. I added Prometheus and Grafana for
monitoring with real alert rules, and verified zero-downtime rollouts and
proper GitOps-style rollbacks.

The part I'm most proud of is 5 AI agents I built with LangChain and a
local LLM - they read real pipeline outputs, like actual Trivy scan
results, and reason about what to do next. For example, my security
triage agent read a real scan with 109 vulnerabilities and correctly
flagged the 5 CRITICAL ones with fixes available, then a gatekeeper agent
composed that with the SonarQube result to make a final deploy decision -
it correctly prioritized security over a passing quality gate.

## Likely follow-up questions and honest answers

Why local LLM instead of OpenAI/Claude API?
Cost and self-containment - no API key dependency, runs entirely offline,
good for a portfolio project that shouldn't have ongoing costs. In a
production setting I'd likely use a hosted API for better reasoning
quality and speed, trading off the no-external-dependency property.

How do you know the AI agent's output is trustworthy?
I don't fully - that's an honest limitation. The agents are advisory:
they write a report and a verdict, but a human (or a scripted gate
checking the verdict string) makes the final call. I didn't build in
guardrails against the LLM hallucinating a CVE ID - that would be a real
next step for production use.

What would break this at scale?
Single-node k3s has no real high availability - losing that one node
loses the cluster. SonarQube on a t3.micro needed a swap file to run at
all. I'd move to a managed EKS/GKE cluster and managed SonarQube/Jenkins
alternatives for anything beyond a demo.

Why Helm AND raw manifests in your repo?
The raw manifests are historical - I migrated to Helm partway through and
kept them for reference rather than cleaning up immediately.

Did you test rollback?
Yes - and I found a genuine gotcha: kubectl rollout undo doesn't work on
ArgoCD-managed deployments because ArgoCD applies manifests declaratively
rather than incrementally, so there's no kubectl rollout history to step
through. The correct pattern is git revert plus letting ArgoCD sync -
which I demonstrated end-to-end.
