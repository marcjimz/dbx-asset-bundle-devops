# Databricks Asset Bundle - Deployment Guide

## Resource Scoping: User vs Production Context

This bundle is configured to automatically scope resources based on the deployment target:

### 🧑‍💻 Development (User-Scoped)

**When you deploy locally or work on a feature branch:**

```bash
databricks bundle deploy --target dev
```

**What happens:**
- **Workspace Path**: `/Workspace/Users/your.email@company.com/.bundle/mlops-production-pipeline/dev`
- **Job Names**: `john_feature_engineering`, `john_model_training`, etc.
- **Model Names**: `mlops_model_john`
- **Experiments**: `/Users/your.email@company.com/mlops-experiments`

**Key Features:**
- ✅ Each developer has isolated resources
- ✅ No conflicts between team members
- ✅ Safe to experiment and test
- ✅ Automatic cleanup when you destroy your bundle

**Example:**
```bash
# User: john.doe@company.com
databricks bundle deploy -t dev

# Creates:
# - Job: john_full_mlops_pipeline
# - Model: mlops_model_john
# - Path: /Workspace/Users/john.doe@company.com/.bundle/mlops-production-pipeline/dev
```

---

### 🧪 Staging (Shared Team Context)

**When CI/CD deploys to staging:**

```bash
databricks bundle deploy --target stg
```

**What happens:**
- **Workspace Path**: `/Workspace/.bundle/mlops-production-pipeline/stg`
- **Job Names**: `stg_feature_engineering`, `stg_model_training`, etc.
- **Model Names**: `mlops_model_stg`
- **Experiments**: `/Shared/mlops-experiments/staging`

**Key Features:**
- ✅ Shared team environment
- ✅ Integration testing before production
- ✅ No user-scoping (global names)
- ✅ Accessible to entire team

---

### 🚀 Production (Global Production Context)

**When CI/CD deploys to production:**

```bash
databricks bundle deploy --target prod
```

**What happens:**
- **Workspace Path**: `/Workspace/Production/.bundle/mlops-production-pipeline`
- **Job Names**: `prod_feature_engineering`, `prod_model_training`, etc.
- **Model Names**: `mlops_model_prod`
- **Experiments**: `/Shared/mlops-experiments/production`
- **Git Tracking**: Locked to `main` branch with full traceability

**Key Features:**
- ✅ Production-grade isolation
- ✅ Read-only for most users
- ✅ Service principal authentication
- ✅ Git source control for rollback
- ✅ Audit trail for compliance

---

## Variable Substitution Patterns

### User Context Variables

```yaml
# Automatically resolves to current user
${workspace.current_user.userName}     # → john.doe@company.com
${workspace.current_user.short_name}   # → john
```

### Development Target Example

```yaml
dev:
  workspace:
    root_path: /Workspace/Users/${workspace.current_user.userName}/.bundle/${bundle.name}/${bundle.target}
  variables:
    resource_prefix: "${workspace.current_user.short_name}"
    model_name: "mlops_model_${workspace.current_user.short_name}"
```

### Production Target Example

```yaml
prod:
  workspace:
    root_path: /Workspace/Production/.bundle/${bundle.name}
  variables:
    resource_prefix: "prod"
    model_name: "mlops_model_prod"
```

---

## Workflow Examples

### Local Development

```bash
# 1. Work on your feature branch
git checkout -b feature/new-model

# 2. Make changes to your code
# 3. Deploy to your personal workspace
databricks bundle deploy -t dev

# 4. Test your changes
databricks bundle run training_job -t dev

# 5. Destroy when done (optional)
databricks bundle destroy -t dev
```

### CI/CD Deployment

```bash
# CI validates on every PR
databricks bundle validate -t dev

# CD deploys on merge to main
databricks bundle deploy -t stg   # Staging first
databricks bundle deploy -t prod  # Then production
```

---

## Environment Variables

### Development (Local)
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-personal-access-token"
```

### CI/CD (GitHub Secrets)
- `DATABRICKS_HOST` - For CI validation
- `DATABRICKS_TOKEN` - For CI validation
- `DATABRICKS_DEV_HOST` + `DATABRICKS_DEV_TOKEN` - For dev deployment
- `DATABRICKS_STG_HOST` + `DATABRICKS_STG_TOKEN` - For staging deployment
- `DATABRICKS_PROD_HOST` + `DATABRICKS_PROD_TOKEN` - For production deployment

---

## Resource Naming Convention

| Environment | Prefix | Example Job Name | Example Model |
|-------------|--------|------------------|---------------|
| Dev (User: john) | `john` | `john_model_training` | `mlops_model_john` |
| Dev (User: sarah) | `sarah` | `sarah_model_training` | `mlops_model_sarah` |
| Staging | `stg` | `stg_model_training` | `mlops_model_stg` |
| Production | `prod` | `prod_model_training` | `mlops_model_prod` |

---

## Best Practices

### ✅ DO

- Use `dev` target for local development and testing
- Create feature branches for new work
- Deploy to your user-scoped workspace for experimentation
- Test thoroughly before creating a PR
- Use `stg` and `prod` only via CI/CD

### ❌ DON'T

- Don't manually deploy to `prod` target locally
- Don't share credentials between environments
- Don't hardcode resource names (use variables)
- Don't deploy to staging/prod without code review

---

## Troubleshooting

### "Resource already exists"
- Check if you're using the right target (dev vs stg vs prod)
- In dev, each user gets their own resources automatically

### "Permission denied"
- Production requires service principal or admin access
- Development should use your personal PAT

### "Workspace path not found"
- User folders are created automatically
- Production folders may need admin provisioning

---

## Additional Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/)
- [CI/CD Best Practices](https://docs.databricks.com/repos/ci-cd-techniques-with-repos.html)
- [Variable Substitution Reference](https://docs.databricks.com/dev-tools/bundles/settings.html)
