# Databricks notebook source
"""
Model Evaluation and Selection Pipeline

This notebook evaluates models from MLflow experiments and selects the best
performing model based on metrics, then transitions it to the appropriate stage.
"""

# COMMAND ----------

import logging
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType
import pandas as pd
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "dev_catalog", "Unity Catalog")
dbutils.widgets.text("schema", "ml_models", "Schema Name")
dbutils.widgets.text("experiment_path", "/Shared/mlops-experiments/dev", "MLflow Experiment Path")
dbutils.widgets.text("model_name", "mlops_model_dev", "Model Name")
dbutils.widgets.text("metric_name", "f1_score", "Primary Metric")
dbutils.widgets.text("min_metric_value", "0.6", "Minimum Metric Value")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
experiment_path = dbutils.widgets.get("experiment_path")
model_name = dbutils.widgets.get("model_name")
metric_name = dbutils.widgets.get("metric_name")
min_metric_value = float(dbutils.widgets.get("min_metric_value"))

logger.info(f"Evaluating models for: {catalog}.{schema}.{model_name}")
logger.info(f"Primary metric: {metric_name} (minimum: {min_metric_value})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Initialize MLflow Client

# COMMAND ----------

# Set MLflow experiment
mlflow.set_experiment(experiment_path)

# Set registry URI for Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# Initialize MLflow client
client = MlflowClient()

# Get experiment
experiment = mlflow.get_experiment_by_name(experiment_path)
if experiment is None:
    raise ValueError(f"Experiment not found: {experiment_path}")

experiment_id = experiment.experiment_id
logger.info(f"Using experiment: {experiment_path} (ID: {experiment_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Search and Compare Models

# COMMAND ----------

def get_best_run(experiment_id, metric_name, min_metric_value):
    """
    Search for the best model run based on specified metric.

    Args:
        experiment_id: MLflow experiment ID
        metric_name: Name of metric to optimize
        min_metric_value: Minimum acceptable metric value

    Returns:
        best_run: MLflow run object
        best_metrics: Dictionary of metrics for best run
    """
    logger.info(f"Searching for best model in experiment {experiment_id}")

    # Search for all runs in the experiment
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=100,
        order_by=[f"metrics.{metric_name} DESC"]
    )

    if not runs:
        raise ValueError(f"No runs found in experiment {experiment_id}")

    logger.info(f"Found {len(runs)} runs in experiment")

    # Filter runs by minimum metric value
    valid_runs = [
        run for run in runs
        if run.data.metrics.get(metric_name, 0) >= min_metric_value
    ]

    if not valid_runs:
        logger.warning(f"No runs meet minimum {metric_name} threshold of {min_metric_value}")
        logger.warning(f"Using best available run")
        valid_runs = runs

    # Get best run
    best_run = valid_runs[0]
    best_metrics = best_run.data.metrics

    logger.info(f"Selected best run: {best_run.info.run_id}")
    logger.info(f"Best run {metric_name}: {best_metrics.get(metric_name, 'N/A')}")

    return best_run, best_metrics

# Get best run
best_run, best_metrics = get_best_run(experiment_id, metric_name, min_metric_value)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Compare Top Models

# COMMAND ----------

def compare_top_models(experiment_id, top_n=5):
    """
    Compare top N models from the experiment.

    Args:
        experiment_id: MLflow experiment ID
        top_n: Number of top models to compare

    Returns:
        DataFrame with model comparison
    """
    logger.info(f"Comparing top {top_n} models")

    # Get top runs
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=top_n,
        order_by=[f"metrics.{metric_name} DESC"]
    )

    # Extract metrics for comparison
    comparison_data = []
    for run in runs:
        metrics = run.data.metrics
        params = run.data.params

        comparison_data.append({
            "run_id": run.info.run_id,
            "run_name": run.data.tags.get("mlflow.runName", "N/A"),
            "accuracy": metrics.get("accuracy", None),
            "precision": metrics.get("precision", None),
            "recall": metrics.get("recall", None),
            "f1_score": metrics.get("f1_score", None),
            "roc_auc": metrics.get("roc_auc", None),
            "cv_f1_mean": metrics.get("cv_f1_mean", None),
            "start_time": datetime.fromtimestamp(run.info.start_time / 1000).isoformat()
        })

    comparison_df = pd.DataFrame(comparison_data)
    return comparison_df

# Compare top models
comparison_df = compare_top_models(experiment_id, top_n=5)
logger.info("Top models comparison:")
print(comparison_df.to_string())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Validate Model Quality

# COMMAND ----------

def validate_model_quality(metrics, thresholds):
    """
    Validate that model meets quality thresholds.

    Args:
        metrics: Dictionary of model metrics
        thresholds: Dictionary of minimum metric thresholds

    Returns:
        validation_passed: Boolean indicating if validation passed
        validation_results: Dictionary with validation details
    """
    logger.info("Validating model quality...")

    validation_results = {}
    validation_passed = True

    for metric, min_value in thresholds.items():
        actual_value = metrics.get(metric, 0)
        passed = actual_value >= min_value

        validation_results[metric] = {
            "actual": actual_value,
            "threshold": min_value,
            "passed": passed
        }

        if not passed:
            validation_passed = False
            logger.warning(f"Validation failed for {metric}: {actual_value} < {min_value}")
        else:
            logger.info(f"Validation passed for {metric}: {actual_value} >= {min_value}")

    return validation_passed, validation_results

# Define quality thresholds
quality_thresholds = {
    "accuracy": 0.65,
    "f1_score": min_metric_value,
    "roc_auc": 0.65
}

validation_passed, validation_results = validate_model_quality(best_metrics, quality_thresholds)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Register and Transition Model

# COMMAND ----------

def register_best_model(run_id, model_name, validation_passed):
    """
    Register the best model and transition to appropriate stage.

    Args:
        run_id: MLflow run ID
        model_name: Full model name (catalog.schema.model)
        validation_passed: Whether model passed validation

    Returns:
        model_version: Registered model version
    """
    logger.info(f"Registering model from run {run_id}")

    try:
        # Get the latest version of the model
        full_model_name = f"{catalog}.{schema}.{model_name}"

        # The model should already be registered during training
        # Get all versions
        versions = client.search_model_versions(f"name='{full_model_name}'")

        if not versions:
            logger.error(f"No versions found for model {full_model_name}")
            raise ValueError(f"Model {full_model_name} not found in registry")

        # Find the version from this run
        model_version = None
        for version in versions:
            if version.run_id == run_id:
                model_version = version
                break

        if model_version is None:
            logger.error(f"No model version found for run {run_id}")
            raise ValueError(f"Model version not found for run {run_id}")

        logger.info(f"Found model version: {model_version.version}")

        # Transition to appropriate stage based on validation
        if validation_passed:
            # Archive current production model if exists
            try:
                prod_versions = [v for v in versions if v.current_stage == "Production"]
                for pv in prod_versions:
                    client.transition_model_version_stage(
                        name=full_model_name,
                        version=pv.version,
                        stage="Archived",
                        archive_existing_versions=False
                    )
                    logger.info(f"Archived previous production version {pv.version}")
            except Exception as e:
                logger.warning(f"Could not archive previous versions: {e}")

            # Transition new model to staging or production based on environment
            target_stage = "Staging" if "dev" in catalog.lower() else "Production"

            try:
                client.transition_model_version_stage(
                    name=full_model_name,
                    version=model_version.version,
                    stage=target_stage,
                    archive_existing_versions=False
                )
                logger.info(f"Transitioned model version {model_version.version} to {target_stage}")
            except Exception as e:
                logger.warning(f"Could not transition model stage: {e}")
                logger.info("Model is registered but stage transition skipped")

            # Add description
            try:
                description = f"Model trained on {datetime.now().strftime('%Y-%m-%d')}. "
                description += f"F1 Score: {best_metrics.get('f1_score', 'N/A'):.4f}, "
                description += f"Accuracy: {best_metrics.get('accuracy', 'N/A'):.4f}"

                client.update_model_version(
                    name=full_model_name,
                    version=model_version.version,
                    description=description
                )
            except Exception as e:
                logger.warning(f"Could not update model description: {e}")

        else:
            logger.warning("Model did not pass validation - not transitioning to production")

        return model_version

    except Exception as e:
        logger.error(f"Error registering model: {e}")
        raise

# Register the best model
model_version = register_best_model(best_run.info.run_id, model_name, validation_passed)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Save Evaluation Report

# COMMAND ----------

# Create evaluation report
evaluation_report = {
    "evaluation_date": datetime.now().isoformat(),
    "experiment_path": experiment_path,
    "model_name": f"{catalog}.{schema}.{model_name}",
    "best_run_id": best_run.info.run_id,
    "model_version": model_version.version if model_version else None,
    "metrics": {k: float(v) if isinstance(v, (int, float)) else v for k, v in best_metrics.items()},
    "validation_passed": validation_passed,
    "validation_results": validation_results,
    "quality_thresholds": quality_thresholds
}

# Log evaluation report as artifact to the best run
with mlflow.start_run(run_id=best_run.info.run_id):
    with open('/tmp/evaluation_report.json', 'w') as f:
        json.dump(evaluation_report, f, indent=2)
    mlflow.log_artifact('/tmp/evaluation_report.json')

    # Log validation metrics
    mlflow.log_metric("validation_passed", 1 if validation_passed else 0)

logger.info("Evaluation report saved")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Evaluation Summary

# COMMAND ----------

print("=" * 80)
print("MODEL EVALUATION SUMMARY")
print("=" * 80)
print(f"Experiment: {experiment_path}")
print(f"Model Name: {catalog}.{schema}.{model_name}")
print(f"Best Run ID: {best_run.info.run_id}")
print(f"Model Version: {model_version.version if model_version else 'N/A'}")
print("-" * 80)
print("METRICS:")
for metric, value in best_metrics.items():
    if isinstance(value, (int, float)):
        print(f"  {metric}: {value:.4f}")
    else:
        print(f"  {metric}: {value}")
print("-" * 80)
print("VALIDATION RESULTS:")
for metric, result in validation_results.items():
    status = "PASS" if result["passed"] else "FAIL"
    print(f"  {metric}: {result['actual']:.4f} >= {result['threshold']:.4f} [{status}]")
print("-" * 80)
print(f"Overall Validation: {'PASSED' if validation_passed else 'FAILED'}")
print("=" * 80)

# COMMAND ----------

# Output for job orchestration
dbutils.notebook.exit({
    "status": "success",
    "best_run_id": best_run.info.run_id,
    "model_version": model_version.version if model_version else None,
    "model_name": f"{catalog}.{schema}.{model_name}",
    "validation_passed": validation_passed,
    "primary_metric": best_metrics.get(metric_name, 0)
})
