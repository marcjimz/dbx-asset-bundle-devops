# GitHub Actions CI/CD Workflows

This directory contains the CI/CD pipeline workflows for the Databricks Asset Bundle MLOps project.

## Overview

The CI/CD pipeline consists of two main workflows:

1. **CI Pipeline** (`ci.yml`) - Continuous Integration for quality assurance
2. **CD Pipeline** (`cd.yml`) - Continuous Deployment for release management

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CI PIPELINE                             │
│  Trigger: PR & commits to all branches                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Security Scanning (Bandit, Safety)                          │
│  2. Secret Scanning (detect-secrets, TruffleHog)                │
│  3. Unit Tests (pytest with coverage)                           │
│  4. Code Quality (Black, Flake8, Pylint, MyPy)                  │
│  5. Bundle Validation (Databricks CLI)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         CD PIPELINE                             │
│  Trigger: Release tags (v*.*.*)                                 │
├─────────────────────────────────────────────────────────────────┤
│  1. DEV Deploy (Automatic)                                      │
│     ├─ Bundle deployment                                        │
│     ├─ Model training                                           │
│     ├─ Model registration                                       │
│     └─ Model serving deployment                                 │
│                                                                  │
│  2. DEV Integration Tests                                       │
│     ├─ Integration test suite                                   │
│     ├─ Endpoint testing                                         │
│     └─ Performance validation                                   │
│                                                                  │
│  3. STG Deploy (Manual Approval ✋)                             │
│     ├─ Bundle deployment                                        │
│     ├─ Model promotion from DEV                                 │
│     └─ Model serving deployment                                 │
│                                                                  │
│  4. STG Integration Tests                                       │
│     ├─ Comprehensive integration tests                          │
│     ├─ Smoke tests                                              │
│     ├─ Performance/load tests                                   │
│     └─ Metrics validation                                       │
│                                                                  │
│  5. PROD Deploy (Manual Approval ✋)                            │
│     ├─ Backup creation                                          │
│     ├─ Bundle deployment                                        │
│     ├─ Model promotion from STG                                 │
│     ├─ Canary deployment (10% traffic)                          │
│     ├─ Canary monitoring                                        │
│     └─ Full rollout (100% traffic)                              │
│                                                                  │
│  6. Post-Deployment Validation                                  │
│     ├─ Production smoke tests                                   │
│     ├─ Release notes update                                     │
│     └─ Deployment notifications                                 │
└─────────────────────────────────────────────────────────────────┘
```

## CI Pipeline Details

### Triggers
- **Pull Requests**: All PRs to any branch
- **Push**: All commits to any branch (excluding release tags)

### Stages

#### 1. Security Scanning
- **Bandit**: Python security vulnerability scanner
- **Safety**: Dependency vulnerability checker
- Reports uploaded as artifacts (30-day retention)

#### 2. Secret Scanning
- **detect-secrets**: Baseline secret detection
- **TruffleHog**: Deep secret scanning (placeholder)
- Baseline file uploaded as artifact

#### 3. Unit Tests
- **Framework**: pytest
- **Python versions**: 3.9, 3.10, 3.11 (matrix)
- **Features**: Coverage reports, parallel execution, timeouts
- **Coverage**: XML, HTML, and terminal reports
- **Artifacts**: Test results and coverage reports

#### 4. Code Quality & Linting
- **Black**: Code formatting check
- **isort**: Import sorting check
- **Flake8**: PEP 8 compliance and code smell detection
- **Pylint**: Advanced code analysis
- **MyPy**: Static type checking
- **SonarQube**: Code quality analysis (placeholder)

#### 5. Bundle Validation
- **Databricks CLI**: Bundle syntax and structure validation
- Runs after security and secret scanning

## CD Pipeline Details

### Triggers
- **Release Tags**: `v*.*.*` (semantic versioning)
  - Example: `v1.2.3`, `v2.0.0-beta.1`

### Release Strategy

#### Semantic Versioning
- **Format**: `vMAJOR.MINOR.PATCH[-PRERELEASE]`
- **Examples**:
  - `v1.0.0` - Stable release
  - `v1.2.3-alpha.1` - Pre-release (alpha)
  - `v2.0.0-beta.2` - Pre-release (beta)
  - `v1.5.0-rc.1` - Release candidate

#### Creating a Release
```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Or create via GitHub UI
# Releases > Create a new release > Choose a tag > Create tag: v1.0.0
```

### Deployment Stages

#### Stage 1: DEV Environment (Automatic)
- **Approval**: None (automatic deployment)
- **Steps**:
  1. Bundle validation and deployment
  2. Model training pipeline execution
  3. Model registration to MLflow Registry
  4. Model serving endpoint deployment
- **MLOps Flow**: Train → Register → Deploy

#### Stage 2: DEV Integration Tests
- **Purpose**: Validate DEV deployment
- **Tests**:
  - Integration test suite
  - Model endpoint testing
  - Performance metrics validation
- **Failure**: Stops progression to STG

#### Stage 3: STG Environment (Manual Approval)
- **Approval**: Required via GitHub Environment protection
- **Steps**:
  1. Bundle validation and deployment
  2. Model promotion from DEV to STG
  3. Model serving endpoint deployment
- **MLOps Flow**: Promote → Deploy

#### Stage 4: STG Integration Tests
- **Purpose**: Comprehensive validation before PROD
- **Tests**:
  - Full integration test suite (including slow tests)
  - Smoke tests
  - Performance/load testing
  - Production-ready metrics validation
- **Failure**: Stops progression to PROD

#### Stage 5: PROD Environment (Manual Approval)
- **Approval**: Required via GitHub Environment protection
- **Strategy**: Canary deployment for safety
- **Steps**:
  1. Create backup/snapshot for rollback
  2. Bundle validation and deployment
  3. Model promotion from STG to PROD
  4. Canary deployment (10% traffic)
  5. Monitor canary metrics
  6. Complete rollout (100% traffic)
- **MLOps Flow**: Backup → Promote → Canary → Monitor → Rollout

#### Stage 6: Post-Deployment
- **Purpose**: Final validation and notifications
- **Steps**:
  1. Production smoke tests
  2. Release notes update
  3. Team notifications (Slack, Email, PagerDuty)

### Rollback Procedure

If a deployment fails, the rollback job provides instructions:

```bash
# Manual rollback to previous stable version
python scripts/rollback.py --env production --to-version v1.0.0

# Or re-deploy stable version
git tag -f v1.0.0
git push origin v1.0.0 --force

# Immediate model rollback
databricks model-serving update-endpoint \
  --name prod-endpoint \
  --model-version <stable-version>
```

## Environment Configuration

### GitHub Environments

Configure these environments in GitHub repository settings:

#### 1. Development (`dev`)
- **Protection Rules**: None (automatic deployment)
- **Required Secrets**: See [Secrets Configuration](#secrets-configuration)
- **Reviewers**: Not required

#### 2. Staging (`staging`)
- **Protection Rules**:
  - Required reviewers: 1-2 team members
  - Wait timer: Optional (e.g., 5 minutes)
- **Required Secrets**: See [Secrets Configuration](#secrets-configuration)
- **Reviewers**: DevOps team, ML engineers

#### 3. Production (`production`)
- **Protection Rules**:
  - Required reviewers: 2+ senior team members
  - Wait timer: Optional (e.g., 15 minutes)
  - Deployment branches: `main` only
- **Required Secrets**: See [Secrets Configuration](#secrets-configuration)
- **Reviewers**: Senior DevOps, ML Lead, Product Owner

### Secrets Configuration

#### Repository Secrets (Global)
Add these in: **Settings → Secrets and variables → Actions → Repository secrets**

```yaml
# Databricks Authentication
DATABRICKS_HOST: "https://adb-XXXXX.azuredatabricks.net"
DATABRICKS_TOKEN: "dapi..."
DATABRICKS_WORKSPACE_ID: "XXXXX"

# Code Quality (Optional)
CODECOV_TOKEN: "..."
SONAR_TOKEN: "..."
```

#### Environment-Specific Secrets

##### DEV Environment Secrets
```yaml
# Model Configuration
DEV_MODEL_NAME: "langgraph_human_interrupt_model_dev"
DEV_ENDPOINT_NAME: "langgraph-human-interrupt-dev"
DEV_ENDPOINT_URL: "https://adb-XXXXX.azuredatabricks.net/serving-endpoints/..."

# Job IDs
DEV_TRAINING_JOB_ID: "123456789"
```

##### STG Environment Secrets
```yaml
# Model Configuration
STG_MODEL_NAME: "langgraph_human_interrupt_model_staging"
STG_ENDPOINT_NAME: "langgraph-human-interrupt-staging"
STG_ENDPOINT_URL: "https://adb-XXXXX.azuredatabricks.net/serving-endpoints/..."

# Job IDs
STG_TRAINING_JOB_ID: "123456790"
```

##### PROD Environment Secrets
```yaml
# Model Configuration
PROD_MODEL_NAME: "langgraph_human_interrupt_model_prod"
PROD_ENDPOINT_NAME: "langgraph-human-interrupt-prod"
PROD_ENDPOINT_URL: "https://adb-XXXXX.azuredatabricks.net/serving-endpoints/..."

# Job IDs
PROD_TRAINING_JOB_ID: "123456791"

# Shared Model Name (for promotions)
MODEL_NAME: "langgraph_human_interrupt_model"
```

### Setting Up Secrets

#### Via GitHub UI:
1. Navigate to **Repository Settings**
2. Go to **Secrets and variables → Actions**
3. Add **Repository secrets** (global)
4. Add **Environment secrets** for each environment:
   - Click on **Environment** tab
   - Create environments: `dev`, `staging`, `production`
   - Add secrets specific to each environment

#### Via GitHub CLI:
```bash
# Repository secrets
gh secret set DATABRICKS_HOST -b "https://adb-XXXXX.azuredatabricks.net"
gh secret set DATABRICKS_TOKEN -b "dapi..."

# Environment secrets
gh secret set DEV_MODEL_NAME -b "model_dev" -e dev
gh secret set STG_MODEL_NAME -b "model_staging" -e staging
gh secret set PROD_MODEL_NAME -b "model_prod" -e production
```

## MLOps Pipeline Integration

The CD workflow includes MLOps stages for each environment:

### Model Training
```bash
# Executed in DEV deployment
databricks jobs run-now --job-id $DEV_TRAINING_JOB_ID
```

### Model Registration
```python
# Register model to MLflow Registry
import mlflow
mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="langgraph_human_interrupt_model_dev"
)
```

### Model Promotion
```python
# Promote model from DEV to STG
client = MlflowClient()
client.copy_model_version(
    src_model_name="model_dev",
    src_model_version="1",
    dst_model_name="model_staging"
)
```

### Model Serving Deployment
```bash
# Deploy model to serving endpoint
databricks model-serving update-endpoint \
  --name endpoint-name \
  --model-name model-name \
  --model-version version
```

## Monitoring and Observability

### Workflow Artifacts
- **Security Reports**: 30-day retention
- **Test Results**: 30-day retention
- **Coverage Reports**: 30-day retention
- **Lint Reports**: 30-day retention

### Accessing Artifacts
1. Go to **Actions** tab
2. Select the workflow run
3. Scroll to **Artifacts** section
4. Download required artifacts

### Notifications (Placeholder Implementation)
The workflows include placeholders for:
- **Slack**: Team channel notifications
- **Email**: Stakeholder notifications
- **PagerDuty**: On-call team updates

To implement:
1. Add notification secrets (webhook URLs, API tokens)
2. Uncomment placeholder sections
3. Customize notification messages

## Best Practices

### For Developers
1. **Before Merging**:
   - Ensure CI pipeline passes
   - Review security scan results
   - Check code coverage metrics
   - Address linting issues

2. **Creating Releases**:
   - Follow semantic versioning
   - Use meaningful release notes
   - Tag from `main` branch only
   - Test DEV deployment before STG approval

3. **Code Quality**:
   - Run linters locally before commit
   - Maintain >80% code coverage
   - Fix security vulnerabilities promptly
   - Keep dependencies updated

### For Reviewers
1. **STG Approval**:
   - Verify DEV integration tests passed
   - Review model performance metrics
   - Check deployment logs for errors
   - Ensure no security issues

2. **PROD Approval**:
   - Verify STG integration tests passed
   - Review canary deployment plan
   - Ensure backup created
   - Confirm rollback procedure ready
   - Validate with team before approval

### For Operations
1. **Monitoring**:
   - Track workflow success rates
   - Monitor deployment duration
   - Review artifact storage usage
   - Check secret rotation schedule

2. **Maintenance**:
   - Update dependencies quarterly
   - Review and update security tools
   - Optimize workflow performance
   - Archive old workflow runs

## Troubleshooting

### Common Issues

#### CI Pipeline Failures
**Issue**: Security scan fails
- **Solution**: Review Bandit/Safety reports, fix vulnerabilities, update dependencies

**Issue**: Unit tests fail
- **Solution**: Check test logs, run tests locally, fix failing tests

**Issue**: Linting fails
- **Solution**: Run `black .` and `isort .`, fix remaining issues

#### CD Pipeline Failures
**Issue**: Bundle validation fails
- **Solution**: Check `databricks.yml` syntax, validate target configuration

**Issue**: DEV deployment fails
- **Solution**: Verify Databricks secrets, check bundle configuration, review logs

**Issue**: Integration tests fail
- **Solution**: Check endpoint availability, verify test data, review test logs

**Issue**: PROD deployment stuck
- **Solution**: Check approval requirements, verify reviewer availability

### Getting Help
1. Review workflow logs in GitHub Actions
2. Check artifact reports for detailed errors
3. Consult Databricks CLI documentation
4. Contact DevOps team for infrastructure issues

## Workflow Customization

### Adding New Stages
1. Edit `ci.yml` or `cd.yml`
2. Add new job following existing patterns
3. Update `needs` dependencies
4. Add required secrets if needed
5. Test in feature branch

### Modifying Environments
1. Update environment names in workflow
2. Create corresponding GitHub environments
3. Add environment-specific secrets
4. Configure protection rules
5. Update documentation

### Integration with External Tools
- **Slack**: Add webhook URL secret, uncomment notification steps
- **Jira**: Add API token, link release to issues
- **Datadog**: Add API key, send metrics
- **PagerDuty**: Add integration key, trigger incidents

## Security Considerations

1. **Secrets Management**:
   - Rotate secrets regularly (quarterly minimum)
   - Use environment-specific secrets
   - Never log secrets in workflow output
   - Use GitHub encrypted secrets only

2. **Access Control**:
   - Limit repository access
   - Configure branch protection rules
   - Require approvals for PROD
   - Enable audit logging

3. **Vulnerability Management**:
   - Monitor security scan results
   - Apply security patches promptly
   - Keep dependencies updated
   - Review and approve dependency updates

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [Semantic Versioning](https://semver.org/)

## Support

For issues or questions:
1. Open a GitHub issue in this repository
2. Contact the DevOps team
3. Refer to internal MLOps documentation
4. Check Databricks support portal

---

**Last Updated**: 2025-10-02
**Maintained By**: DevOps & MLOps Team
