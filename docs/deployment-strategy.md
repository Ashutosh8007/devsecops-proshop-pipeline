# Deployment Strategy

## Rolling Updates (Zero-Downtime)

Both `proshop-backend` and `proshop-frontend` Deployments explicitly define
a `RollingUpdate` strategy with `maxSurge: 1` and `maxUnavailable: 0`:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

`maxUnavailable: 0` guarantees the full original replica count stays
available throughout a rollout — Kubernetes only removes an old pod after
a new one is confirmed healthy, so there is no window of reduced capacity.

Verified with a real rollout: bumped frontend replicas from 3 to 4 via a
Git commit, confirmed via `kubectl rollout status` that the deployment
completed successfully with no dropped availability.

## Rollback: the GitOps-correct way

Attempted a native `kubectl rollout undo`, which failed:
This happens because ArgoCD applies the full manifest declaratively on
each sync rather than using incremental `kubectl set image` style updates,
so Kubernetes never accumulates a rollout history to step back through.

**The correct rollback pattern in a GitOps setup is to revert the Git
commit, not to use imperative kubectl commands** — Git is the source of
truth, and ArgoCD's `selfHeal: true` will otherwise just re-apply the
Git-declared state and undo any manual kubectl changes anyway.

Demonstrated: `git revert <commit> --no-edit`, pushed, forced an ArgoCD
sync, and confirmed the cluster returned to 3 frontend replicas — a clean,
auditable rollback with full history preserved in Git.
