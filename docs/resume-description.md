# Resume Description

## Short version (1 line)

Built an end-to-end DevSecOps pipeline (Jenkins, Docker, Kubernetes/Helm,
ArgoCD, SonarQube, Trivy, Prometheus/Grafana) with 5 custom AI agents
(LangChain + local LLM) for automated security triage and deployment
gating.

## Bullet version (for a resume Projects section)

DevSecOps CI/CD Pipeline with AI-Assisted Security Gating - Personal Project

- Designed and provisioned a multi-instance AWS infrastructure (Terraform)
  running Jenkins, SonarQube, k3s, and a monitoring stack across 4 EC2
  instances, with security groups scoped per service.
- Built a CI/CD pipeline (Jenkins) with automated code quality gates
  (SonarQube), container vulnerability scanning (Trivy - found and
  triaged 109 real CVEs), and Docker Hub image publishing.
- Implemented GitOps continuous deployment with ArgoCD (auto-sync,
  self-heal), deploying a Helm-packaged MERN-stack app to Kubernetes;
  verified zero-downtime rolling updates and a Git-based rollback flow.
- Built full observability with Prometheus and Grafana: 7 dashboards,
  a working alert rule, and a live self-healing verification test.
- Designed 5 autonomous AI agents (Python, LangChain, local LLM via
  Ollama) that read pipeline outputs and reason about next actions:
  security triage with GO/NO-GO verdicts, deployment gatekeeping,
  incident summarization from live alerts, AI code review, and a
  ChatOps assistant for diagnosing failed builds from raw logs.
