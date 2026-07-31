# GitOps with ArgoCD

ArgoCD continuously monitors the `helm-chart/proshop` path in this repository
and automatically syncs Kubernetes manifests to the k3s cluster — no manual
`kubectl apply` needed for deployed changes. Auto-sync is configured with
`prune: true` and `selfHeal: true`, so ArgoCD both applies new changes and
corrects any manual drift on the cluster.

Verified: bumped `proshop-backend` replicas from 2 to 3 in
`helm-chart/proshop/values.yaml` via a Git commit and push; ArgoCD
auto-detects and applies the change without any manual kubectl commands.


