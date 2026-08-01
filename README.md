# DevSecOps CI/CD Pipeline with AI-Assisted Security Gating

An end-to-end DevSecOps pipeline built from scratch on AWS free tier —
covering CI/CD, container security scanning, GitOps deployment, full
observability, and five autonomous AI agents that read real pipeline
output and make GO/NO-GO decisions.

Deployed application: **ProShop** — a MERN-stack e-commerce app
(React + Redux frontend, Node.js/Express backend, MongoDB).

---

## Highlights

- Full CI/CD pipeline: Jenkins, Docker, SonarQube, Trivy, Docker Hub
- GitOps continuous deployment with ArgoCD (auto-sync, self-heal) —
  verified live with a real zero-downtime rollout and rollback demo
- Full observability: Prometheus + Grafana, 7 dashboards, a working
  alert rule, and a live self-healing verification test
- 109 real vulnerabilities found and triaged by Trivy on the backend image
- 5 autonomous AI agents (Python, LangChain, local LLM via Ollama) that
  reason over real pipeline data — not scripted rules

---

## Architecture
Developer
|
v
GitHub --push--> Jenkins CI
|
+--------+--------+
v v
SonarQube Trivy
(quality gate) (vuln scanning)
| |
+--------+--------+
v
Docker Hub push
v
ArgoCD sync
(GitOps, self-heal)
v
k3s (Kubernetes)
v
Prometheus + Grafana
(metrics + alerts)
---

## Infrastructure

Provisioned entirely with Terraform across 4 AWS EC2 instances, each
scoped with its own security group:

| Instance      | Purpose                                  | Notes                          |
|---------------|-------------------------------------------|---------------------------------|
| Jenkins       | CI engine, Docker builds, Trivy scanning   | t2/t3.micro                    |
| SonarQube     | Code quality gate                          | t2/t3.micro + 2GB swap file    |
| k3s           | Lightweight Kubernetes, app + ArgoCD       | t3.small                       |
| Monitoring    | Prometheus + Grafana                       | t2/t3.micro                    |

Public IPs are dynamic (no Elastic IPs, to stay within free tier), so the
security group's allowed CIDR is updated via `terraform.tfvars` each
session before `terraform apply`.

---

## CI/CD Pipeline (Jenkins)

1. **Checkout** — pull latest from GitHub
2. **Build** — Docker image build (backend + frontend)
3. **SonarQube analysis** — static code quality gate
4. **Trivy scan** — container vulnerability scan (OS packages + Node deps)
5. **Docker Hub push** — versioned + `latest` tags
6. **Version tagging** and **secrets handling** via Kubernetes Secrets

---

## GitOps Deployment (ArgoCD + Helm)

- App is packaged as a Helm chart (`helm-chart/proshop`) — backend,
  frontend, and MongoDB Deployments, Services, a PVC, and a Secret.
- ArgoCD watches the chart directly from GitHub with `automated: true`,
  `prune: true`, `selfHeal: true` — the cluster state is always a live
  reflection of what's committed to Git.
- **Verified live**: bumped replica counts via a Git commit, watched
  ArgoCD auto-sync and Kubernetes scale up with zero dropped availability.
- **Deployment strategy**: explicit `RollingUpdate` with `maxSurge: 1`,
  `maxUnavailable: 0` on both Deployments — guarantees the full replica
  count stays available throughout every rollout.
- **Rollback, done the GitOps-correct way**: `kubectl rollout undo`
  does **not** work on ArgoCD-managed deployments (ArgoCD applies
  manifests declaratively, so there's no kubectl rollout history to
  step through). The correct pattern — `git revert` + ArgoCD sync — was
  demonstrated end-to-end and is documented in
  [`docs/deployment-strategy.md`](docs/deployment-strategy.md).

---

## Security

- **Trivy** scanned the backend image and found **109 vulnerabilities**
  (5 CRITICAL, 48 HIGH, 27 MEDIUM, 29 LOW) across OS packages (Alpine)
  and Node.js dependencies.
- The Security Triage Agent (see below) read this real scan and
  correctly flagged the 5 CRITICAL findings — including a real
  `mongoose` CVE — with a **NO-GO** verdict.
- Secrets (DB credentials) are stored as Kubernetes Secrets, not
  hardcoded in manifests.

---

## Monitoring & Observability

- **Prometheus** scrapes `node-exporter` and `kube-state-metrics` via
  NodePort — the original bearer-token/service-account scrape approach
  was broken for an external Prometheus instance and was replaced with
  static NodePort targets (see `monitoring/prometheus/prometheus.yml`).
- **Grafana** dashboards (version-controlled as JSON in
  `monitoring/grafana/dashboards/`):
  - Node Exporter Full (host-level CPU/mem/disk/network)
  - Pods by Phase
  - Container Restarts
  - Deployment Status
  - Namespace Overview
  - Node Resource Requests vs Capacity
  - PVC/Storage
- A real **alert rule** (`High Pod Restart Rate`) was built and verified
  evaluating correctly against live cluster metrics.
- **Self-healing was tested live**: deleted a pod, confirmed the
  Deployment controller recreated it automatically within seconds —
  proof the desired-state reconciliation loop works.

---

## AI Agents (`agents/`)

Five standalone Python agents, each using **LangChain + Ollama**
(local `llama3.2` model — no external API dependency, no ongoing cost).
Each has its own README and sample data so it can be run and understood
independently.

| Agent | What it does |
|---|---|
| [`security-triage-agent`](agents/security-triage-agent/) | Reads a Trivy JSON scan, ranks findings by severity, and writes a reasoned GO/NO-GO verdict — not just a sorted list. |
| [`deployment-gatekeeper-agent`](agents/deployment-gatekeeper-agent/) | Composes the security triage verdict with a SonarQube quality gate result into one final deployment decision — correctly prioritizes security over passing code quality. |
| [`incident-monitoring-agent`](agents/incident-monitoring-agent/) | Reads a Prometheus/Alertmanager webhook payload and translates it into a plain-English incident summary with a likely root cause and next diagnostic step. |
| [`code-review-agent`](agents/code-review-agent/) | Reads a real `git diff` and writes a PR-review-style comment — found genuine issues (missing input validation, missing error handling) in this project's own code. |
| [`chatops-agent`](agents/chatops-agent/) | Answers "why did this build fail?" by reading a Jenkins console log and identifying the failing stage, the exact error line, and a likely fix. |

Two agents compose together: **security-triage** and **code-review**
both feed into **deployment-gatekeeper**, which reasons about conflicts
between them rather than applying a hardcoded rule.

---

## Repository Structure

See [`docs/project-structure.md`](docs/project-structure.md) for the
full breakdown and rationale.
devsecops-proshop-pipeline/
├── agents/ 5 AI agents (LangChain + Ollama)
├── terraform/ AWS infrastructure as code
├── helm-chart/proshop/ Helm chart (source of truth for ArgoCD)
├── k8s-manifests/ Raw manifests (pre-Helm, historical reference)
├── jenkins/ Jenkinsfile
├── monitoring/ Prometheus config + Grafana dashboards (JSON)
└── docs/ Architecture notes, GitOps + deployment write-ups
---

## Documentation

- [`docs/project-structure.md`](docs/project-structure.md) — folder layout and rationale
- [`docs/gitops.md`](docs/gitops.md) — ArgoCD verification notes
- [`docs/deployment-strategy.md`](docs/deployment-strategy.md) — rolling updates + rollback
- [`docs/resume-description.md`](docs/resume-description.md) — resume-ready bullets
- [`docs/interview-explanation.md`](docs/interview-explanation.md) — how to talk through this project, with honest answers to likely follow-ups
- [`docs/production-improvements.md`](docs/production-improvements.md) — what I'd change for real production use

---

## What I'd do differently at scale

Full honest list in [`docs/production-improvements.md`](docs/production-improvements.md),
but the short version: managed multi-node Kubernetes instead of
single-node k3s, Elastic IPs instead of dynamic ones, a secrets manager
instead of raw Kubernetes Secrets, and guardrails against LLM
hallucination in the AI agents before trusting them unsupervised.

---

## Status

Infrastructure has been torn down (`terraform destroy`) after project
completion to avoid ongoing AWS costs. All code, configs, dashboards,
and documentation remain in this repository and are fully reproducible
by re-running `terraform apply`.
