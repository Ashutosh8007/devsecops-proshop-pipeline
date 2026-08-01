# Project Structure
devsecops-proshop-pipeline/
agents/ AI agents (LangChain + Ollama, local LLM)
security-triage-agent/ Trivy scan -> AI-ranked vuln triage + GO/NO-GO
deployment-gatekeeper-agent/ Composes security + SonarQube -> final deploy verdict
incident-monitoring-agent/ Prometheus alerts -> plain-English incident summary
code-review-agent/ git diff -> PR-review-style comment
chatops-agent/ why did build X fail -> Jenkins log analysis
terraform/ IaC for 4 EC2 instances (Jenkins, SonarQube, k3s, monitoring)
helm-chart/proshop/ Helm chart for the MERN app (backend, frontend, mongo)
k8s-manifests/ Raw K8s manifests (pre-Helm, kept for reference)
jenkins/ Jenkinsfile and pipeline config
monitoring/prometheus/ Scrape config (node-exporter, kube-state-metrics)
monitoring/grafana/dashboards/ 6 custom + 1 imported dashboard, version-controlled as JSON
docs/ Architecture notes, GitOps verification, deployment strategy
## Why this structure

- agents/ is separated from the core pipeline: each agent is standalone,
  independently runnable, with its own README and sample data.
- helm-chart/ is the real source of truth for what's deployed; ArgoCD
  watches this path directly. k8s-manifests/ is kept only as a historical
  reference from before the Helm migration.
- monitoring/ dashboards are stored as exported JSON so the setup is
  reproducible from git if the monitoring EC2 is ever rebuilt.
