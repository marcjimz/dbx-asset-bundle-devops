# MLOps Production Pipeline with Databricks Asset Bundles

A production-ready MLOps pipeline using Databricks Asset Bundles (DAB) with automated CI/CD workflows for multi-environment deployments (DEV, STG, PROD). This project demonstrates best practices for ML model development, training, evaluation, and deployment using GitHub Actions and Databricks.

## Features

### Multi-Environment MLOps Pipeline
- Automated model training, evaluation, and deployment workflows
- Environment-specific configurations (DEV, STG, PROD)
- Unity Catalog integration for centralized model governance
- MLflow experiment tracking and model registry
- Scheduled feature engineering jobs

### CI/CD Automation
- GitHub Actions-powered CI pipeline with comprehensive testing
- Automated security scanning and secret detection
- Code quality checks (Black, Flake8, Pylint)
- Unit test coverage reporting
- Continuous deployment with manual approval gates
- Environment-specific deployment validation

### Production-Ready Architecture
- Databricks Asset Bundle configuration for infrastructure as code
- Parameterized jobs for flexibility across environments
- Integrated security scanning and compliance checks
- Automated testing at multiple levels (unit, integration, smoke)

## Quick Start

### Prerequisites

Before you begin, ensure you have:

1. **Databricks Workspace Access**
   - Databricks workspace (AWS, Azure, or GCP)
   - Workspace URL: `https://adb-<workspace-id>.<region>.<cloud>.databricks.com`
   - Personal access token with permissions for:
     - Workspace read/write
     - Jobs create and run
     - Model Registry access
     - Model Serving access

2. **Unity Catalog Setup**
   - Unity Catalog enabled in your workspace
   - Catalogs created for each environment:
     - `dev_catalog` (DEV)
     - `stg_catalog` (STG)
     - `prod_catalog` (PROD)
   - Schemas created: `ml_models` in each catalog
   - Appropriate permissions granted (USE CATALOG, USE SCHEMA, CREATE MODEL)

3. **Development Tools** (for local testing - optional)
   - Python 3.10 or later
   - Databricks CLI (optional: `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh`)
   - Git and GitHub account with repository access
   - GitHub CLI (optional but recommended: `brew install gh`)

4. **GitHub Repository** (required for CI/CD)
   - Admin access to your GitHub repository
   - Ability to create GitHub environments
   - Ability to add secrets and configure workflows

> **Note**: Local Databricks authentication is **optional** if you're only using GitHub Actions for CI/CD.
> The CI/CD pipelines authenticate using GitHub Secrets, so you can skip steps 4-5 below if you
> only want to run deployments through GitHub Actions.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/dbx-asset-bundle-devops.git
cd dbx-asset-bundle-devops
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Databricks Bundle

Update `databricks.yml` with your workspace details:

```yaml
# Update workspace hosts for each target
targets:
  dev:
    workspace:
      host: https://adb-YOUR-WORKSPACE-ID.cloud.databricks.com
  stg:
    workspace:
      host: https://adb-YOUR-WORKSPACE-ID.cloud.databricks.com
  prod:
    workspace:
      host: https://adb-YOUR-WORKSPACE-ID.cloud.databricks.com
```

### 4. (Optional) Authenticate with Databricks for Local Testing

**Skip this step if you only want to use GitHub Actions for deployments.**

```bash
# Configure Databricks CLI
databricks configure --host https://YOUR-WORKSPACE.databricks.com

# Or use environment variables
export DATABRICKS_HOST="https://YOUR-WORKSPACE.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

### 5. (Optional) Validate and Deploy Locally

**Skip this step if you only want to use GitHub Actions for deployments.**

```bash
# Validate bundle configuration
databricks bundle validate --target dev

# Deploy to DEV environment
databricks bundle deploy --target dev

# Run a training job
databricks bundle run training_job --target dev
```

### 6. Set Up CI/CD with GitHub Actions

**This is the primary deployment method for this example.**

Follow the detailed [CI/CD Setup Guide](#cicd-setup) below to configure GitHub Actions workflows.
All deployments will happen automatically through GitHub Actions once configured.

## Project Structure

```
dbx-asset-bundle-devops/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # CI pipeline: testing, security, quality
│   │   └── cd.yml                    # CD pipeline: multi-env deployment
│   ├── SETUP_GUIDE.md                # Detailed GitHub Actions setup
│   ├── SECRETS_TEMPLATE.md           # Secret configuration reference
│   └── PIPELINE_OVERVIEW.md          # Pipeline architecture details
│
├── src/
│   ├── training.py                   # Model training notebook
│   ├── evaluation.py                 # Model evaluation notebook
│   ├── deployment.py                 # Model deployment notebook
│   └── features/
│       └── feature_engineering.py    # Feature preparation notebook
│
├── tests/
│   ├── test_pipeline.py              # Integration tests
│   └── unit/
│       ├── test_training.py          # Training unit tests
│       └── test_evaluation.py        # Evaluation unit tests
│
├── databricks.yml                    # Databricks Asset Bundle configuration
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── .gitignore                        # Git ignore rules
```

## CI/CD Setup

> **Primary Deployment Method**: This project is designed to be deployed via GitHub Actions.
> Local Databricks authentication is **not required** - all deployments run through CI/CD pipelines
> using GitHub Secrets for authentication.

### Quick Start for CI/CD Only

If you only want to use GitHub Actions (recommended):
1. Configure GitHub Environments (see Step 1 below)
2. Add GitHub Secrets (see Step 2 below)
3. Create a PR to test CI pipeline
4. Create a release tag (e.g., `v0.1.0`) to trigger CD pipeline

**That's it!** No local Databricks CLI setup needed.

---

### Step 1: Create GitHub Environments

Create three environments in your GitHub repository for deployment stages:

**Navigate to**: Repository Settings → Environments

#### DEV Environment
```
Name: development
Protection Rules: None (automatic deployment)
Deployment Branches: All branches
```

#### STG Environment
```
Name: staging
Protection Rules:
  - Required reviewers: 1-2 team members
  - Wait timer: 5 minutes (optional)
Deployment Branches: All branches
```

#### PROD Environment
```
Name: production
Protection Rules:
  - Required reviewers: 2+ senior team members
  - Wait timer: 15 minutes (optional)
  - Deployment branches: Only 'main' branch
Deployment Branches: Selected branches → main
```

### Step 2: Configure Repository Secrets

**Navigate to**: Repository Settings → Secrets and variables → Actions → Repository secrets

Add the following environment-specific secrets:

#### DEV Environment Secrets
```yaml
DATABRICKS_DEV_HOST: "https://adb-XXXXXXX.cloud.databricks.com"
DATABRICKS_DEV_TOKEN: "dapi..." # Generate from User Settings → Access Tokens
```

#### STG Environment Secrets
```yaml
DATABRICKS_STG_HOST: "https://adb-XXXXXXX.cloud.databricks.com"
DATABRICKS_STG_TOKEN: "dapi..."
```

#### PROD Environment Secrets
```yaml
DATABRICKS_PROD_HOST: "https://adb-XXXXXXX.cloud.databricks.com"
DATABRICKS_PROD_TOKEN: "dapi..."
```

**To generate a Databricks token:**
1. Log in to Databricks workspace
2. Click profile icon → User Settings
3. Navigate to Access Tokens tab
4. Click "Generate new token"
5. Set comment: "GitHub Actions CI/CD"
6. Set lifetime: 90 days (or per your policy)
7. Copy token immediately (shown only once!)

### Step 3: Enable GitHub Actions

**Navigate to**: Settings → Actions → General

Configure permissions:
- Actions permissions: Allow all actions and reusable workflows
- Workflow permissions: Read and write permissions
- Allow GitHub Actions to create and approve pull requests: Enabled

Click "Save"

### Step 4: Verify Setup

Run the verification checklist:

```bash
# Test Databricks connection
databricks workspace list --host $DATABRICKS_DEV_HOST --token $DATABRICKS_DEV_TOKEN

# Validate bundle locally
databricks bundle validate --target dev

# Check GitHub secrets (requires gh CLI)
gh secret list
```

For detailed setup instructions, see [.github/SETUP_GUIDE.md](.github/SETUP_GUIDE.md)

## Testing the CI Pipeline

The CI pipeline runs automatically on pull requests and pushes to trigger comprehensive testing.

### Trigger CI Workflow

```bash
# Create a feature branch
git checkout -b test/ci-pipeline

# Make a change
echo "# Test CI" >> test.md
git add test.md
git commit -m "test: CI pipeline validation"

# Push and create PR
git push origin test/ci-pipeline

# Create PR (via GitHub UI or CLI)
gh pr create --title "Test CI Pipeline" --body "Testing CI workflow"
```

### What CI Tests

The CI pipeline includes:

1. **Security Vulnerability Scan**
   - Bandit: Python security issue detection
   - Safety: Known vulnerability checking
   - pip-audit: Dependency vulnerability scanning

2. **Secret Scanning**
   - detect-secrets: Secret pattern detection
   - TruffleHog: Verified secret scanning

3. **Code Quality Checks**
   - Black: Code formatting validation
   - Flake8: PEP8 style compliance
   - Pylint: Code quality analysis

4. **Unit Tests**
   - pytest: Test execution
   - Coverage reporting (XML, HTML, terminal)
   - Minimum coverage threshold validation

5. **Bundle Validation**
   - Databricks bundle syntax validation
   - YAML configuration verification

### Review CI Results

1. Go to **Actions** tab in GitHub
2. Click on the running workflow
3. Review each job status (green checkmark = passed)
4. Download artifacts (security reports, coverage reports)
5. Review any failures and address issues

### CI Artifacts Available

- `bandit-security-report`: Security vulnerability findings
- `secrets-baseline`: Detected secrets analysis
- `coverage-report`: Code coverage HTML and XML reports

## Testing the CD Pipeline (Release Process)

The CD pipeline deploys to DEV, STG, and PROD environments sequentially with approval gates.

### Creating a Release

The CD pipeline triggers on version tags following semantic versioning (`v*.*.*`).

#### Method 1: Git CLI

```bash
# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial production release"

# Push tag to trigger CD
git push origin v1.0.0
```

#### Method 2: GitHub UI

1. Navigate to **Releases** → **Create a new release**
2. Click **Choose a tag**
3. Type new tag: `v1.0.0`
4. Click **Create new tag: v1.0.0 on publish**
5. Add release title: "v1.0.0 - Initial Release"
6. Add release notes describing changes
7. Click **Publish release**

#### Method 3: GitHub CLI

```bash
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "Initial production release with MLOps pipeline"
```

### CD Pipeline Workflow

The deployment follows this sequence:

```
1. Deploy to DEV (automatic)
   ↓
2. Run DEV validation tests (automatic)
   ↓
3. Wait for STG approval (manual review required)
   ↓
4. Deploy to STG (after approval)
   ↓
5. Run STG integration tests (automatic)
   ↓
6. Wait for PROD approval (manual review required)
   ↓
7. Deploy to PROD (after approval)
   ↓
8. Run PROD smoke tests (automatic)
```

### Approving Deployments

When the workflow reaches an approval gate:

1. Go to **Actions** → Select the running CD workflow
2. You'll see a "Review deployments" button
3. Click **Review deployments**
4. Select environment(s) to approve (e.g., "staging" or "production")
5. Add approval comment (optional but recommended)
6. Click **Approve and deploy**

Reviewers will receive notifications when approval is required.

### Monitoring Deployments

**In GitHub:**
1. Navigate to **Actions** → Select workflow run
2. View real-time logs for each environment
3. Check deployment status (In progress, Success, Failed)
4. Review job summaries and artifacts

**In Databricks:**
1. Navigate to **Workflows** → **Jobs**
2. Find jobs prefixed with environment: `dev_`, `stg_`, `prod_`
3. Review job runs and execution logs
4. Check **MLflow** → **Experiments** for training runs
5. Check **Model Registry** for registered models

## What to Expect and Observe

### After CI Pipeline Runs

**Expected Outcomes:**
- All security scans pass with no critical vulnerabilities
- Code quality checks pass (formatting, linting)
- Unit tests pass with coverage above threshold (typically 80%)
- Bundle validation succeeds

**Where to Look:**
- GitHub Actions tab: Overall workflow status
- Artifacts section: Download detailed reports
- Pull request checks: See status of each job
- Coverage report: View code coverage metrics

### After CD Pipeline Runs

**Expected Outcomes in Databricks:**

#### DEV Environment
- Bundle deployed to workspace path: `/Workspace/mlops-production-pipeline/dev`
- Jobs created:
  - `dev_feature_engineering`
  - `dev_model_training`
  - `dev_model_evaluation`
  - `dev_model_deployment`
  - `dev_full_mlops_pipeline`
- Notebooks visible in workspace
- MLflow experiment: `/Shared/mlops-experiments/dev`

#### STG Environment
- Bundle deployed to: `/Workspace/mlops-production-pipeline/stg`
- Similar jobs with `stg_` prefix
- Models registered in Unity Catalog: `stg_catalog.ml_models`
- Integration tests executed successfully

#### PROD Environment
- Bundle deployed to: `/Workspace/mlops-production-pipeline/prod`
- Jobs with `prod_` prefix
- Models in production registry: `prod_catalog.ml_models`
- Production endpoints available

### Databricks Resources Created

For each environment, you'll see:

**Workflows (Jobs):**
```
{environment}_feature_engineering    # Scheduled daily at 2 AM UTC
{environment}_model_training         # On-demand training
{environment}_model_evaluation       # Model quality assessment
{environment}_model_deployment       # Deploy to serving
{environment}_full_mlops_pipeline    # End-to-end pipeline
```

**MLflow Experiments:**
```
/Shared/mlops-experiments/dev
/Shared/mlops-experiments/stg
/Shared/mlops-experiments/prod
```

**Unity Catalog Models:**
```
dev_catalog.ml_models.mlops_model_dev
stg_catalog.ml_models.mlops_model_stg
prod_catalog.ml_models.mlops_model_prod
```

**Workspace Paths:**
```
/Workspace/mlops-production-pipeline/dev/
/Workspace/mlops-production-pipeline/stg/
/Workspace/mlops-production-pipeline/prod/
```

## Testing and Validation Strategy

### Unit Tests

Unit tests validate individual components in isolation.

**Location**: `tests/unit/`

**Running Unit Tests:**

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=term --cov-report=html

# Run specific test file
pytest tests/unit/test_training.py -v
```

**Example Test Structure:**

```python
# tests/unit/test_training.py
import pytest

def test_training_parameters():
    """Test training parameter validation"""
    # Test parameter handling
    assert True

def test_model_logging():
    """Test MLflow logging functionality"""
    # Test model logging
    assert True
```

**Writing New Unit Tests:**

1. Create test file: `tests/unit/test_<module>.py`
2. Import module to test
3. Write test functions prefixed with `test_`
4. Use pytest fixtures for setup/teardown
5. Assert expected behavior
6. Run tests and verify coverage

### Integration Tests (STG Environment)

Integration tests validate end-to-end workflows in the staging environment.

**Location**: `tests/test_pipeline.py`

**What Integration Tests Validate:**

1. **Data Pipeline**
   - Feature engineering job executes successfully
   - Data is written to correct Unity Catalog tables
   - Data quality checks pass

2. **Training Pipeline**
   - Training job runs without errors
   - Model is logged to MLflow
   - Model metrics meet minimum thresholds

3. **Evaluation Pipeline**
   - Model evaluation completes
   - Evaluation metrics are logged
   - Model comparison works correctly

4. **Deployment Pipeline**
   - Model registration succeeds
   - Model transitions to correct stage
   - Deployment completes without errors

**Running Integration Tests:**

```bash
# Run integration tests locally (requires Databricks credentials)
export DATABRICKS_HOST="https://your-workspace.databricks.com"
export DATABRICKS_TOKEN="dapi..."
pytest tests/test_pipeline.py -v --target=stg

# Integration tests run automatically in CD pipeline after STG deployment
```

**Example Integration Test:**

```python
# tests/test_pipeline.py
import pytest
from databricks.sdk import WorkspaceClient

def test_full_pipeline_execution(databricks_client):
    """Test complete MLOps pipeline in staging"""
    # Trigger full pipeline job
    job_run = databricks_client.jobs.run_now(job_id="stg_full_mlops_pipeline")

    # Wait for completion
    result = wait_for_job_completion(job_run.run_id)

    # Assert success
    assert result.state.result_state == "SUCCESS"

    # Validate model was created
    model = databricks_client.model_registry.get_latest_versions(
        name="stg_catalog.ml_models.mlops_model_stg"
    )
    assert len(model) > 0
```

### Deployment Validation

Validate deployments after each environment deployment.

**DEV Validation:**
```bash
# Check bundle deployed successfully
databricks bundle validate --target dev

# List deployed jobs
databricks workspace list /Workspace/mlops-production-pipeline/dev

# Check job exists
databricks jobs list | grep "dev_training_job"
```

**STG Validation:**
```bash
# Run smoke test on STG
databricks jobs run-now --job-id $(databricks jobs list | grep "stg_training_job" | awk '{print $1}')

# Check MLflow experiment
databricks experiments search --filter "name='/Shared/mlops-experiments/stg'"

# Validate model in registry
databricks model-registry get-model --name "stg_catalog.ml_models.mlops_model_stg"
```

**PROD Validation:**
```bash
# Verify production deployment
databricks bundle validate --target prod

# Check production job status
databricks jobs get --job-id $PROD_JOB_ID

# Validate model serving endpoint (if applicable)
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  https://your-workspace.databricks.com/serving-endpoints/mlops-model-prod
```

### Manual Testing Checklist

Before releasing to production, verify:

**DEV Environment:**
- [ ] All jobs visible in Workflows
- [ ] Training job can be run manually
- [ ] MLflow experiment shows training runs
- [ ] Model appears in Unity Catalog
- [ ] Notebooks are accessible in workspace

**STG Environment:**
- [ ] Integration tests pass
- [ ] Model quality metrics meet thresholds
- [ ] Deployment completes without errors
- [ ] Model registry shows correct version
- [ ] No errors in job execution logs

**PROD Environment:**
- [ ] Production jobs created successfully
- [ ] Model deployed to production registry
- [ ] Serving endpoint operational (if applicable)
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented

## Troubleshooting

### Common Issues

#### Issue: CI Pipeline Fails on Unit Tests

**Symptoms:**
- pytest fails with import errors
- Tests can't find source modules

**Solutions:**
```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Run tests from project root
pytest tests/ -v

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
```

#### Issue: Bundle Validation Fails

**Symptoms:**
- `databricks bundle validate` returns errors
- YAML syntax errors

**Solutions:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('databricks.yml'))"

# Check for missing required fields
databricks bundle validate --target dev

# Verify workspace host is correct
grep -A 2 "workspace:" databricks.yml
```

#### Issue: Databricks Authentication Fails

**Symptoms:**
- 401 Unauthorized errors
- Token authentication fails

**Solutions:**
```bash
# Verify token is set correctly
echo $DATABRICKS_TOKEN | wc -c  # Should be ~40+ characters

# Test connection
databricks workspace list --host $DATABRICKS_HOST --token $DATABRICKS_TOKEN

# Regenerate token if expired
# Go to Databricks → User Settings → Access Tokens → Generate new token
```

#### Issue: CD Pipeline Stuck on Approval

**Symptoms:**
- Workflow shows "Waiting for approval"
- No approval button visible

**Solutions:**
1. Check environment reviewers are configured:
   - Settings → Environments → [Environment] → Required reviewers
2. Ensure reviewers have notifications enabled
3. Check if you're one of the designated reviewers
4. Review deployment: Actions → Workflow → Review deployments

#### Issue: Job Fails in Databricks

**Symptoms:**
- Job run shows failed status
- Error in job execution logs

**Solutions:**
```bash
# View job logs in Databricks
# Navigate to: Workflows → Jobs → [Job Name] → Latest Run → Logs

# Common fixes:
# 1. Check cluster configuration (node type, Spark version)
# 2. Verify notebook paths are correct
# 3. Ensure Unity Catalog permissions are granted
# 4. Check parameter values are valid

# Test job manually
databricks jobs run-now --job-id JOB_ID
```

#### Issue: Model Not Appearing in Unity Catalog

**Symptoms:**
- Model training succeeds but model not in registry
- Permission denied errors

**Solutions:**
```sql
-- Grant necessary permissions
GRANT USE CATALOG ON CATALOG dev_catalog TO `user@example.com`;
GRANT USE SCHEMA ON SCHEMA dev_catalog.ml_models TO `user@example.com`;
GRANT CREATE MODEL ON SCHEMA dev_catalog.ml_models TO `user@example.com`;

-- Verify catalog exists
SHOW CATALOGS;

-- Verify schema exists
SHOW SCHEMAS IN dev_catalog;
```

### Getting Help

If you encounter issues not covered here:

1. **Check Documentation:**
   - [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/)
   - [GitHub Actions Documentation](https://docs.github.com/en/actions)
   - [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

2. **Review Logs:**
   - GitHub Actions workflow logs
   - Databricks job execution logs
   - MLflow experiment tracking

3. **Contact Support:**
   - File an issue in the repository
   - Contact your DevOps team
   - Reach out to Databricks support

## Best Practices

### Development Workflow

1. **Branch Strategy:**
   - Create feature branches: `feature/model-improvement`
   - Use descriptive branch names
   - Create PRs for all changes
   - Require reviews before merging

2. **Testing:**
   - Write unit tests for new code
   - Test locally before pushing: `pytest tests/ -v`
   - Ensure coverage stays above 80%
   - Run integration tests in STG before PROD

3. **Version Control:**
   - Use semantic versioning: `v1.2.3`
   - Tag releases only from main branch
   - Write clear commit messages
   - Update CHANGELOG for releases

### Deployment Strategy

1. **Environment Progression:**
   - Always deploy: DEV → STG → PROD
   - Never skip STG testing
   - Validate thoroughly at each stage
   - Document any issues found

2. **Release Process:**
   - Create release notes documenting changes
   - Tag releases with semantic versioning
   - Get required approvals for STG and PROD
   - Monitor deployments closely
   - Have rollback plan ready

3. **Security:**
   - Rotate Databricks tokens every 90 days
   - Never commit secrets to version control
   - Use GitHub encrypted secrets only
   - Review security scan results
   - Keep dependencies updated

### Monitoring and Maintenance

1. **Regular Checks:**
   - Review MLflow experiments weekly
   - Monitor model performance metrics
   - Check job execution success rates
   - Review error logs regularly

2. **Updates:**
   - Keep dependencies up to date
   - Update Databricks runtime versions
   - Review and update CI/CD workflows
   - Refresh documentation

3. **Cleanup:**
   - Archive old experiments
   - Remove deprecated models
   - Clean up unused jobs
   - Manage workspace storage

## Advanced Configuration

### Custom Notifications

Add Slack notifications for deployment events:

```yaml
# In .github/workflows/cd.yml, add step:
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Deployment to ${{ github.event.inputs.environment }} completed"
      }
```

### Code Coverage Integration

Integrate with Codecov for coverage tracking:

```yaml
# In .github/workflows/ci.yml, add step:
- name: Upload to Codecov
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage.xml
```

### Custom Model Serving

Deploy models to serving endpoints:

```python
# In src/deployment.py, add serving logic:
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create serving endpoint
w.serving_endpoints.create(
    name=f"{environment}_model_endpoint",
    config={
        "served_models": [{
            "model_name": model_name,
            "model_version": model_version,
            "workload_size": "Small",
            "scale_to_zero_enabled": True
        }]
    }
)
```

## Additional Resources

### Documentation
- [Databricks Asset Bundles Guide](https://docs.databricks.com/dev-tools/bundles/)
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [GitHub Actions Guide](https://docs.github.com/en/actions)

### Example Projects
- [example/](example/) - Human-in-the-loop LangGraph agent example
- [Databricks Asset Bundle Examples](https://github.com/databricks/bundle-examples)

### Support Files
- [.github/SETUP_GUIDE.md](.github/SETUP_GUIDE.md) - Detailed setup instructions
- [.github/SECRETS_TEMPLATE.md](.github/SECRETS_TEMPLATE.md) - Secret configuration guide
- [.github/PIPELINE_OVERVIEW.md](.github/PIPELINE_OVERVIEW.md) - Pipeline architecture

### Useful Commands

```bash
# Databricks CLI commands
databricks bundle validate --target dev
databricks bundle deploy --target dev
databricks bundle run training_job --target dev
databricks jobs list
databricks workspace list

# GitHub CLI commands
gh pr create
gh release create v1.0.0
gh secret list
gh run list
gh run watch

# Testing commands
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
black src/ tests/
flake8 src/ tests/

# Git workflow
git checkout -b feature/new-model
git add .
git commit -m "feat: add new model training logic"
git push origin feature/new-model
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request with clear description

## License

This project is provided as-is for educational and demonstration purposes.

## Acknowledgments

Built with:
- Databricks Asset Bundles
- GitHub Actions
- MLflow
- Unity Catalog
- pytest

---

**Last Updated**: 2025-10-02
**Maintained By**: MLOps Team
**Questions?** File an issue or contact the DevOps team
