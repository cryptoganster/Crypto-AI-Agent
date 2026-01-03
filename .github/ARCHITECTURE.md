# 🏗️ CI/CD Architecture

Diagrama de la arquitectura de CI/CD implementada.

## 📊 Flujo General

```
┌─────────────────────────────────────────────────────────────────┐
│                     Developer Workflow                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Feature Branch  │
                    │  feat/new-thing  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Create PR to   │
                    │      master      │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CI Pipeline (Parallel)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Code Quality │  │  Unit Tests  │  │ Integration  │         │
│  │              │  │              │  │    Tests     │         │
│  │ • Black      │  │ • pytest     │  │ • PostgreSQL │         │
│  │ • isort      │  │ • coverage   │  │ • Redis      │         │
│  │ • flake8     │  │ • 90%+ cov   │  │ • Playwright │         │
│  │ • mypy       │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Property    │  │   Security   │  │    Build     │         │
│  │    Tests     │  │    Scan      │  │    Check     │         │
│  │              │  │              │  │              │         │
│  │ • Hypothesis │  │ • Safety     │  │ • python -m  │         │
│  │ • PBT        │  │ • Bandit     │  │   build      │         │
│  │              │  │              │  │ • twine      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  PR Checks   │  │  Dependency  │                            │
│  │              │  │    Review    │                            │
│  │ • Title      │  │              │                            │
│  │ • Size       │  │ • Vulns      │                            │
│  │ • Breaking   │  │ • Licenses   │                            │
│  │ • Docs       │  │              │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  All Checks Pass │
                    │   + 1 Approval   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Merge to       │
                    │     master       │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CD Pipeline (Sequential)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Build Docker Image                                     │  │
│  │    • Multi-stage build                                    │  │
│  │    • Push to ghcr.io                                      │  │
│  │    • Tag: master-<sha>                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2. Deploy to Staging                                      │  │
│  │    • Pull image from registry                             │  │
│  │    • Update staging environment                           │  │
│  │    • Run smoke tests                                      │  │
│  │    • Notify team                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3. Run Database Migrations                                │  │
│  │    • alembic upgrade head                                 │  │
│  │    • Verify migrations                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Staging Ready   │
                    └──────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│              Production Deploy (Tag v*.*.*)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Tag Created (v1.0.0)                                   │  │
│  │    • Triggers production workflow                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2. Build Docker Image                                     │  │
│  │    • Tag: v1.0.0, 1.0, latest                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3. Deploy to Production                                   │  │
│  │    • Requires manual approval (1-2 reviewers)            │  │
│  │    • Wait timer: 5 minutes                               │  │
│  │    • Pull image from registry                            │  │
│  │    • Update production environment                        │  │
│  │    • Run smoke tests                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4. Create GitHub Release                                  │  │
│  │    • Release notes                                        │  │
│  │    • Changelog                                            │  │
│  │    • Artifacts                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔒 Security Scanning

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ CodeQL Analysis (Weekly + PR)                            │  │
│  │                                                           │  │
│  │  • Python security patterns                              │  │
│  │  • SQL injection detection                               │  │
│  │  • XSS vulnerabilities                                   │  │
│  │  • Hardcoded credentials                                 │  │
│  │  • Path traversal                                        │  │
│  │                                                           │  │
│  │  Results → Security tab                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Dependency Scanning (PR + Push)                          │  │
│  │                                                           │  │
│  │  • Safety check (known vulnerabilities)                  │  │
│  │  • License compliance                                    │  │
│  │  • Dependency review                                     │  │
│  │  • Dependabot alerts                                     │  │
│  │                                                           │  │
│  │  Results → Security tab                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Secret Scanning (Push)                                   │  │
│  │                                                           │  │
│  │  • API keys                                              │  │
│  │  • Passwords                                             │  │
│  │  • Tokens                                                │  │
│  │  • Private keys                                          │  │
│  │                                                           │  │
│  │  Push protection enabled                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🛡️ Branch Protection

```
┌─────────────────────────────────────────────────────────────────┐
│                    Master Branch Protection                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Restrictions                                              │  │
│  │  ✅ No direct pushes                                     │  │
│  │  ✅ No force pushes                                      │  │
│  │  ✅ No deletions                                         │  │
│  │  ✅ Require linear history                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Pull Request Requirements                                 │  │
│  │  ✅ 1+ approvals required                                │  │
│  │  ✅ Dismiss stale reviews                                │  │
│  │  ✅ Code owners review                                   │  │
│  │  ✅ Conversation resolution                              │  │
│  │  ✅ Up-to-date branch                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Required Status Checks (8)                                │  │
│  │  ✅ code-quality                                         │  │
│  │  ✅ unit-tests                                           │  │
│  │  ✅ integration-tests                                    │  │
│  │  ✅ property-tests                                       │  │
│  │  ✅ security                                             │  │
│  │  ✅ build                                                │  │
│  │  ✅ pr-title                                             │  │
│  │  ✅ dependency-review                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Commit Requirements                                       │  │
│  │  ✅ Signed commits (GPG)                                 │  │
│  │  ✅ Conventional Commits format                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Dashboard                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ GitHub Actions                                            │  │
│  │  • Workflow runs                                         │  │
│  │  • Success/failure rates                                 │  │
│  │  • Duration trends                                       │  │
│  │  • Resource usage                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Code Coverage (Codecov)                                   │  │
│  │  • Overall coverage: 80%+                                │  │
│  │  • Domain layer: 90%+                                    │  │
│  │  • Application layer: 85%+                               │  │
│  │  • Infrastructure layer: 70%+                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Security Alerts                                           │  │
│  │  • Dependabot alerts                                     │  │
│  │  • CodeQL findings                                       │  │
│  │  • Secret scanning alerts                                │  │
│  │  • Vulnerability severity                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Deployment Status                                         │  │
│  │  • Staging: ✅ Healthy                                   │  │
│  │  • Production: ✅ Healthy                                │  │
│  │  • Last deploy: 2 hours ago                              │  │
│  │  • Uptime: 99.9%                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Rollback Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Rollback Process                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Detect Issue                                           │  │
│  │    • Monitoring alerts                                    │  │
│  │    • User reports                                         │  │
│  │    • Smoke tests fail                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2. Quick Rollback (< 5 min)                              │  │
│  │    • Revert to previous Docker image                     │  │
│  │    • kubectl rollout undo deployment/app                 │  │
│  │    • Verify health checks                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3. Database Rollback (if needed)                         │  │
│  │    • alembic downgrade -1                                │  │
│  │    • Verify data integrity                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4. Post-Rollback                                          │  │
│  │    • Notify team                                          │  │
│  │    • Create incident report                              │  │
│  │    • Plan fix                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📈 Metrics & KPIs

### CI/CD Performance

- **Build Time**: < 15 minutes
- **Test Coverage**: > 80%
- **Success Rate**: > 95%
- **Mean Time to Deploy**: < 30 minutes
- **Deployment Frequency**: Multiple per day

### Quality Metrics

- **Code Quality Score**: A+
- **Security Vulnerabilities**: 0 critical
- **Technical Debt**: < 5%
- **Documentation Coverage**: > 90%

### Reliability Metrics

- **Uptime**: 99.9%
- **Mean Time to Recovery**: < 1 hour
- **Failed Deployments**: < 5%
- **Rollback Rate**: < 2%

---

**Última actualización**: 2024-01-03
