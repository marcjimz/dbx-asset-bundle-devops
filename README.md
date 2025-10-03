# MLOps Production Pipeline - Databricks Asset Bundles

> ⚠️ **DEVELOPMENT STATUS WARNING**
>
> **This asset bundle deployment is currently in development and pending testing.**
> **Use at your own risk. Not recommended for production use.**
>
> - Bundle validation: ✅ Passing
> - CI/CD workflows: ✅ Configured (auth-only mode)
> - Deployment testing: ⏳ Pending
> - Integration tests: ⏳ Not implemented
>
> See [CD_DEPLOYMENT_INSTRUCTIONS.md](CD_DEPLOYMENT_INSTRUCTIONS.md) for enabling full deployment.

Production-ready MLOps pipeline using Databricks Asset Bundles with automated CI/CD for DEV, STG, and PROD environments.

## Features

- 🔄 **Multi-environment pipeline** (DEV/STG/PROD) with user vs production scoping
- 🤖 **Automated CI/CD** via GitHub Actions with quality gates
- 🔒 **Security scanning** (Bandit, Safety, TruffleHog, detect-secrets)
- 📊 **Unity Catalog** integration for model governance
- 🧪 **Comprehensive testing** (unit tests, coverage reporting)
- 🚀 **MLflow tracking** for experiments and model registry

## Quick Start

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- GitHub repository with admin access
- Python 3.10+
- Databricks CLI (optional for local testing)

**Required Catalogs:**
```sql
-- Create in Databricks SQL
CREATE CATALOG IF NOT EXISTS dev_catalog;
CREATE CATALOG IF NOT EXISTS stg_catalog;
CREATE CATALOG IF NOT EXISTS prod_catalog;

CREATE SCHEMA IF NOT EXISTS dev_catalog.ml_models;
CREATE SCHEMA IF NOT EXISTS stg_catalog.ml_models;
CREATE SCHEMA IF NOT EXISTS prod_catalog.ml_models;
```

### Setup

**1. Clone and install:**
```bash
git clone <your-repo>
cd dbx-asset-bundle-devops
pip install -r requirements.txt
```

**2. Configure GitHub Environments:**

Create three environments in **Settings → Environments**:

| Environment | Protection Rules | Reviewers |
|-------------|------------------|-----------|
| `development` | None | N/A |
| `staging` | Required reviewers | 1-2 people |
| `production` | Required reviewers | 2+ people |

**3. Add GitHub Secrets:**

**Repository Secrets** (Settings → Secrets → Actions):
```
DATABRICKS_HOST       # For CI validation
DATABRICKS_TOKEN      # For CI validation
```

**Environment Secrets** (per environment):
```
DATABRICKS_DEV_HOST / DATABRICKS_DEV_TOKEN
DATABRICKS_STG_HOST / DATABRICKS_STG_TOKEN
DATABRICKS_PROD_HOST / DATABRICKS_PROD_TOKEN
```

**4. Test CI:**
```bash
git checkout -b test/ci-pipeline
echo "# Test" >> test.md
git commit -am "test: CI pipeline"
git push origin test/ci-pipeline
# Create PR and verify CI passes
```

**5. Test CD (Auth-only mode):**
```bash
git checkout main
git tag v0.0.1-test
git push origin v0.0.1-test
# Verify authentication in GitHub Actions
```

## Project Structure

```
.
├── .github/workflows/
│   ├── ci.yml                 # CI: security, quality, tests
│   └── cd.yml                 # CD: multi-env deployment (auth-only)
├── src/
│   ├── training.py            # Model training
│   ├── evaluation.py          # Model evaluation
│   ├── deployment.py          # Model deployment
│   └── features/              # Feature engineering
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests (placeholder)
├── databricks.yml             # Bundle configuration
├── requirements.txt
└── README.md
```

## Resource Scoping (User vs Production)

The bundle automatically scopes resources based on target:

| Target | Mode | Path | Resource Prefix | Use Case |
|--------|------|------|----------------|----------|
| **dev** | `development` | `/Workspace/Users/{user}/.bundle/...` | `{username}` | Personal dev |
| **stg** | `production` | `/Workspace/.bundle/mlops-production-pipeline/stg` | `stg` | Team testing |
| **prod** | `production` | `/Workspace/Production/.bundle/mlops-production-pipeline` | `prod` | Production |

**Example - User john.doe@company.com:**
```bash
# Deploy to dev
databricks bundle deploy -t dev

# Creates:
# - Path: /Workspace/Users/john.doe@company.com/.bundle/mlops-production-pipeline/dev
# - Jobs: john_model_training, john_feature_engineering
# - Model: mlops_model_john
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details.

## CI/CD Pipeline

### CI Pipeline (Pull Requests)

Runs on every PR:
```
Security Scan → Secret Scan → Code Quality → Unit Tests → Bundle Validation
```

**What's checked:**
- 🔒 Security vulnerabilities (Bandit, Safety, pip-audit)
- 🔑 Secret detection (TruffleHog, detect-secrets)
- ✨ Code quality (Black, Flake8, Pylint)
- 🧪 Unit tests (pytest with coverage)
- ✅ Bundle syntax validation

### CD Pipeline (Releases)

Triggered by version tags (e.g., `v1.0.0`):
```
Quality Gates → Deploy DEV → Deploy STG (approval) → Deploy PROD (approval)
```

**Current Status:** ⚠️ **Auth-only mode** (deployments disabled)

- Validates credentials ✅
- Tests authentication ✅
- **Does not deploy resources** ❌

To enable deployment, see [CD_DEPLOYMENT_INSTRUCTIONS.md](CD_DEPLOYMENT_INSTRUCTIONS.md).

## Running Locally (Optional)

**Validate bundle:**
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

databricks bundle validate -t dev
```

**Deploy to dev:**
```bash
databricks bundle deploy -t dev
```

**Run training job:**
```bash
databricks bundle run training_job -t dev
```

## Testing

**Unit tests:**
```bash
pytest tests/unit/ -v --cov=src --cov-report=term
```

**Integration tests:**
See [tests/integration/README.md](tests/integration/README.md) (not yet implemented).

## Troubleshooting

**Bundle validation fails:**
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('databricks.yml'))"

# Validate bundle
databricks bundle validate -t dev
```

**Authentication fails:**
```bash
# Test connection
databricks workspace list --host $DATABRICKS_HOST --token $DATABRICKS_TOKEN

# Regenerate token: User Settings → Access Tokens
```

**CD stuck on approval:**
1. Go to Actions → Select workflow
2. Click "Review deployments"
3. Select environment and approve

## Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - User vs production scoping
- [CD_DEPLOYMENT_INSTRUCTIONS.md](CD_DEPLOYMENT_INSTRUCTIONS.md) - Enable full deployment
- [tests/integration/README.md](tests/integration/README.md) - Integration test guide

## Resources Created (When Enabled)

Per environment, creates:

**Jobs:**
- `{prefix}_feature_engineering`
- `{prefix}_model_training`
- `{prefix}_model_evaluation`
- `{prefix}_model_deployment`
- `{prefix}_full_mlops_pipeline`

**Models:**
- `{catalog}.ml_models.mlops_model_{env}`

**Experiments:**
- Dev: `/Users/{user}/mlops-experiments`
- Stg/Prod: `/Shared/mlops-experiments/{env}`

## Best Practices

**Development:**
- Create feature branches for changes
- Run tests locally before pushing
- Create PRs for code review
- Never commit secrets

**Deployment:**
- Always progress: DEV → STG → PROD
- Test thoroughly in staging
- Get required approvals
- Monitor deployments closely

**Security:**
- Rotate tokens every 90 days
- Use GitHub encrypted secrets
- Review security scan results
- Keep dependencies updated

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests for changes
4. Ensure CI passes
5. Submit PR with description

## License

Provided as-is for educational purposes.

---

**Status:** 🚧 In Development | **Use at your own risk**
