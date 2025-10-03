# Databricks notebook source
"""
Model Training Pipeline

This notebook trains a machine learning model using features from Delta tables
and logs the model and metrics to MLflow with Unity Catalog integration.
"""

# COMMAND ----------

import logging
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from pyspark.sql import SparkSession
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from datetime import datetime
import json
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "dev_catalog", "Unity Catalog")
dbutils.widgets.text("schema", "ml_models", "Schema Name")
dbutils.widgets.text(
    "experiment_path", "/Shared/mlops-experiments/dev", "MLflow Experiment Path"
)
dbutils.widgets.text("model_name", "mlops_model_dev", "Model Name")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
experiment_path = dbutils.widgets.get("experiment_path")
model_name = dbutils.widgets.get("model_name")

logger.info(f"Training model: {model_name}")
logger.info(f"Using catalog: {catalog}, schema: {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Set up MLflow Experiment

# COMMAND ----------

# Set MLflow experiment
mlflow.set_experiment(experiment_path)
logger.info(f"Using MLflow experiment: {experiment_path}")

# Set registry URI for Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Training Data

# COMMAND ----------

spark = SparkSession.builder.getOrCreate()

# Load features from Delta table
features_table = f"{catalog}.{schema}.customer_features"
logger.info(f"Loading features from {features_table}")

try:
    features_df = spark.table(features_table)
    logger.info(f"Loaded {features_df.count()} records from features table")
except Exception as e:
    logger.error(f"Error loading features table: {e}")
    raise

# Show sample data
logger.info("Sample features:")
features_df.select(
    "customer_id", "age", "income", "credit_score", "high_value_customer"
).show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Prepare Training Data

# COMMAND ----------


def prepare_training_data(df):
    """
    Prepare features and target variable for training.

    Args:
        df: Spark DataFrame with features

    Returns:
        X: Feature matrix (pandas DataFrame)
        y: Target variable (pandas Series)
    """
    logger.info("Preparing training data...")

    # Select feature columns
    feature_columns = [
        "age",
        "income",
        "credit_score",
        "account_balance",
        "num_transactions",
        "days_since_last_transaction",
        "income_to_balance_ratio",
        "transaction_frequency",
    ]

    # Target variable
    target_column = "high_value_customer"

    # Convert to pandas
    pdf = df.select(*feature_columns, target_column).toPandas()

    # Handle any missing values
    pdf = pdf.fillna(0)

    # Separate features and target
    X = pdf[feature_columns]
    y = pdf[target_column].astype(int)

    logger.info(f"Training data prepared: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Target distribution: {y.value_counts().to_dict()}")

    return X, y, feature_columns


X, y, feature_columns = prepare_training_data(features_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Train Model with MLflow Tracking

# COMMAND ----------


def train_model(X, y, feature_names):
    """
    Train a Random Forest model with hyperparameters and MLflow tracking.

    Args:
        X: Feature matrix
        y: Target variable
        feature_names: List of feature names

    Returns:
        model: Trained model
        metrics: Dictionary of evaluation metrics
    """
    logger.info("Starting model training...")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info(f"Training set: {X_train.shape[0]} samples")
    logger.info(f"Test set: {X_test.shape[0]} samples")

    # Model hyperparameters
    params = {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42,
        "n_jobs": -1,
    }

    # Train model
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    logger.info("Model training completed")

    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_pred_proba),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }

    # Cross-validation score
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1")
    metrics["cv_f1_mean"] = cv_scores.mean()
    metrics["cv_f1_std"] = cv_scores.std()

    logger.info(f"Model metrics: {metrics}")

    # Feature importance
    feature_importance = dict(zip(feature_names, model.feature_importances_))
    logger.info(
        f"Top 5 important features: {sorted(
            feature_importance.items(), key=lambda x: x[1],
            reverse=True)[:5]}"
    )

    return (
        model,
        metrics,
        X_test,
        y_test,
        y_pred,
        y_pred_proba,
        feature_importance,
        params,
    )


# Train the model
model, metrics, X_test, y_test, y_pred, y_pred_proba, feature_importance, params = (
    train_model(X, y, feature_columns)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Log Model and Artifacts to MLflow

# COMMAND ----------

# Start MLflow run
with mlflow.start_run(
    run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
) as run:
    run_id = run.info.run_id
    logger.info(f"MLflow Run ID: {run_id}")

    # Log parameters
    mlflow.log_params(params)
    mlflow.log_param("catalog", catalog)
    mlflow.log_param("schema", schema)
    mlflow.log_param("feature_count", len(feature_columns))

    # Log metrics
    mlflow.log_metrics(metrics)

    # Log feature importance
    for feature, importance in feature_importance.items():
        mlflow.log_metric(f"feature_importance_{feature}", importance)

    # Create model signature
    signature = infer_signature(X, model.predict(X))

    # Log model to MLflow with Unity Catalog
    logger.info("Logging model to MLflow...")
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        signature=signature,
        input_example=X.head(5),
        registered_model_name=f"{catalog}.{schema}.{model_name}",
    )

    # Log confusion matrix as artifact using secure temporary file
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title("Confusion Matrix")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")

    # Save to secure temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        confusion_matrix_path = f.name
    plt.savefig(confusion_matrix_path)
    mlflow.log_artifact(confusion_matrix_path)
    plt.close()
    os.unlink(confusion_matrix_path)  # Clean up

    # Log classification report using secure temporary file
    class_report = classification_report(y_test, y_pred, output_dict=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        class_report_path = f.name
        json.dump(class_report, f, indent=2)
    mlflow.log_artifact(class_report_path)
    os.unlink(class_report_path)  # Clean up

    # Log feature importance plot using secure temporary file
    plt.figure(figsize=(10, 6))
    sorted_importance = sorted(
        feature_importance.items(), key=lambda x: x[1], reverse=True
    )
    features, importances = zip(*sorted_importance)
    plt.barh(features, importances)
    plt.xlabel("Importance")
    plt.title("Feature Importance")
    plt.tight_layout()

    # Save to secure temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        feature_importance_path = f.name
    plt.savefig(feature_importance_path)
    mlflow.log_artifact(feature_importance_path)
    plt.close()
    os.unlink(feature_importance_path)  # Clean up

    # Add tags
    mlflow.set_tags(
        {
            "model_type": "RandomForestClassifier",
            "environment": catalog.replace("_catalog", ""),
            "use_case": "customer_value_prediction",
            "training_date": datetime.now().isoformat(),
        }
    )

    logger.info(f"Model logged successfully to run {run_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Training Summary

# COMMAND ----------

print("=" * 80)
print("MODEL TRAINING SUMMARY")
print("=" * 80)
print(f"MLflow Run ID: {run_id}")
print(f"Model Name: {catalog}.{schema}.{model_name}")
print(f"Experiment: {experiment_path}")
print("-" * 80)
print("METRICS:")
for metric, value in metrics.items():
    print(f"  {metric}: {value:.4f}")
print("-" * 80)
print("TOP FEATURES:")
for feature, importance in sorted(
    feature_importance.items(), key=lambda x: x[1], reverse=True
)[:5]:
    print(f"  {feature}: {importance:.4f}")
print("=" * 80)

# COMMAND ----------

# Output for job orchestration
dbutils.notebook.exit(
    {
        "status": "success",
        "run_id": run_id,
        "model_name": f"{catalog}.{schema}.{model_name}",
        "accuracy": metrics["accuracy"],
        "f1_score": metrics["f1_score"],
        "experiment_path": experiment_path,
    }
)
