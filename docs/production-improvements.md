# What I'd Do Differently for Production

This project was built under AWS free-tier constraints (single-node k3s,
t2/t3.micro instances, 15-day time budget). Honest list of what I'd
change for a real production deployment:

## Infrastructure
- Replace single-node k3s with a managed multi-node cluster (EKS/GKE) for
  actual high availability.
- Use Elastic IPs or a load balancer instead of auto-assigned public IPs.
- Move SonarQube and Jenkins to managed/hosted alternatives, or at least
  larger instances - the swap-file workaround for SonarQube on a
  1GB-RAM box is a demo-scale hack, not production-appropriate.

## Security
- Rotate the ArgoCD admin password (currently the auto-generated initial
  password, exposed once during setup).
- Move secrets to a proper secrets manager (AWS Secrets Manager / Vault)
  instead of Kubernetes Secrets alone.
- Tighten security group rules - several were opened to 0.0.0.0/0 during
  development for convenience; these should be scoped to specific
  IPs/VPNs in production.

## Deployment
- Add real canary or blue-green deployment support (e.g. Argo Rollouts)
  instead of relying solely on rolling updates.
- Populate CHANGE-CAUSE annotations on deployments for a more useful
  kubectl rollout history output.

## AI Agents
- Add guardrails against LLM hallucination (validate that any CVE ID the
  agent cites actually exists in the source Trivy report).
- Move from CLI scripts to actual Jenkinsfile pipeline stages, so agents
  run automatically on every build.
- Consider a hosted LLM API for better reasoning quality/speed if cost
  and external dependency are acceptable tradeoffs.

## Housekeeping
- Remove the legacy k8s-manifests/ raw YAML folder now that Helm is the
  actual source of truth.
