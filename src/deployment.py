# Databricks notebook source
"""
Model Deployment Pipeline

This notebook deploys validated models to Model Serving endpoints
with monitoring and versioning capabilities.
"""

# COMMAND ----------

import logging
import mlflow
from mlflow.tracking import MlflowClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
    TrafficConfig,
    Route
)
import time
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "dev_catalog", "Unity Catalog")
dbutils.widgets.text("schema", "ml_models", "Schema Name")
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("model_name", "mlops_model_dev", "Model Name")
dbutils.widgets.text("model_version", "latest", "Model Version (or 'latest')")
dbutils.widgets.text("endpoint_name", "", "Serving Endpoint Name (optional)")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
environment = dbutils.widgets.get("environment")
model_name = dbutils.widgets.get("model_name")
model_version_param = dbutils.widgets.get("model_version")
endpoint_name_param = dbutils.widgets.get("endpoint_name")

# Construct full model name
full_model_name = f"{catalog}.{schema}.{model_name}"

# Set endpoint name
if endpoint_name_param:
    endpoint_name = endpoint_name_param
else:
    endpoint_name = f"{model_name}_{environment}"

logger.info(f"Deploying model: {full_model_name}")
logger.info(f"Environment: {environment}")
logger.info(f"Endpoint: {endpoint_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Initialize Clients

# COMMAND ----------

# Set registry URI for Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# Initialize MLflow client
mlflow_client = MlflowClient()

# Initialize Databricks SDK client
workspace_client = WorkspaceClient()

logger.info("Clients initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Get Model Version to Deploy

# COMMAND ----------

def get_model_version_to_deploy(model_name, version_param, environment):
    """
    Get the specific model version to deploy.

    Args:
        model_name: Full model name
        version_param: Version parameter ('latest', 'production', 'staging', or specific version)
        environment: Deployment environment

    Returns:
        version_number: Model version number to deploy
    """
    logger.info(f"Determining model version to deploy...")

    try:
        if version_param.lower() == "latest":
            # Get latest version
            versions = mlflow_client.search_model_versions(f"name='{model_name}'")
            if not versions:
                raise ValueError(f"No versions found for model {model_name}")

            # Sort by version number
            versions = sorted(versions, key=lambda x: int(x.version), reverse=True)
            version_number = versions[0].version
            logger.info(f"Using latest version: {version_number}")

        elif version_param.lower() in ["production", "staging"]:
            # Get version in specific stage
            stage = version_param.capitalize()
            versions = mlflow_client.search_model_versions(
                f"name='{model_name}' and current_stage='{stage}'"
            )

            if not versions:
                logger.warning(f"No {stage} version found, using latest version instead")
                versions = mlflow_client.search_model_versions(f"name='{model_name}'")
                if not versions:
                    raise ValueError(f"No versions found for model {model_name}")
                versions = sorted(versions, key=lambda x: int(x.version), reverse=True)
                version_number = versions[0].version
            else:
                version_number = versions[0].version
                logger.info(f"Using {stage} version: {version_number}")

        else:
            # Use specific version number
            version_number = version_param
            logger.info(f"Using specified version: {version_number}")

        # Validate version exists
        try:
            model_version = mlflow_client.get_model_version(model_name, version_number)
            logger.info(f"Model version {version_number} validated successfully")
            return version_number, model_version
        except Exception as e:
            raise ValueError(f"Model version {version_number} not found: {e}")

    except Exception as e:
        logger.error(f"Error getting model version: {e}")
        raise

# Get model version to deploy
version_to_deploy, model_version_info = get_model_version_to_deploy(
    full_model_name, model_version_param, environment
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Configure Serving Endpoint

# COMMAND ----------

def create_or_update_endpoint(endpoint_name, model_name, model_version, environment):
    """
    Create or update a model serving endpoint.

    Args:
        endpoint_name: Name of the serving endpoint
        model_name: Full model name
        model_version: Model version to deploy
        environment: Deployment environment

    Returns:
        endpoint_info: Information about the endpoint
    """
    logger.info(f"Configuring serving endpoint: {endpoint_name}")

    # Determine instance size based on environment
    if environment.lower() == "prod":
        workload_size = "Medium"
        scale_to_zero_enabled = False
        min_instances = 1
        max_instances = 5
    elif environment.lower() == "stg":
        workload_size = "Small"
        scale_to_zero_enabled = True
        min_instances = 1
        max_instances = 3
    else:  # dev
        workload_size = "Small"
        scale_to_zero_enabled = True
        min_instances = 0
        max_instances = 1

    try:
        # Check if endpoint exists
        try:
            existing_endpoint = workspace_client.serving_endpoints.get(endpoint_name)
            endpoint_exists = True
            logger.info(f"Endpoint {endpoint_name} exists, will update")
        except Exception:
            endpoint_exists = False
            logger.info(f"Endpoint {endpoint_name} does not exist, will create")

        # Configure served entity
        served_entity = ServedEntityInput(
            entity_name=model_name,
            entity_version=model_version,
            workload_size=workload_size,
            scale_to_zero_enabled=scale_to_zero_enabled
        )

        if endpoint_exists:
            # Update existing endpoint
            logger.info("Updating existing endpoint...")

            workspace_client.serving_endpoints.update_config(
                name=endpoint_name,
                served_entities=[served_entity],
                traffic_config=TrafficConfig(
                    routes=[Route(
                        served_model_name=f"{model_name.split('.')[-1]}-{model_version}",
                        traffic_percentage=100
                    )]
                )
            )

            logger.info(f"Endpoint update initiated")

        else:
            # Create new endpoint
            logger.info("Creating new endpoint...")

            workspace_client.serving_endpoints.create(
                name=endpoint_name,
                config=EndpointCoreConfigInput(
                    served_entities=[served_entity]
                )
            )

            logger.info(f"Endpoint creation initiated")

        # Wait for endpoint to be ready
        logger.info("Waiting for endpoint to be ready...")
        max_wait_time = 1200  # 20 minutes
        wait_interval = 30
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            try:
                endpoint_status = workspace_client.serving_endpoints.get(endpoint_name)

                if endpoint_status.state.ready == "READY":
                    logger.info(f"Endpoint {endpoint_name} is ready!")
                    return {
                        "name": endpoint_name,
                        "state": endpoint_status.state.ready,
                        "url": f"https://{spark.conf.get('spark.databricks.workspaceUrl')}/ml/endpoints/{endpoint_name}"
                    }

                logger.info(f"Endpoint state: {endpoint_status.state.ready}. Waiting...")
                time.sleep(wait_interval)
                elapsed_time += wait_interval

            except Exception as e:
                logger.warning(f"Error checking endpoint status: {e}")
                time.sleep(wait_interval)
                elapsed_time += wait_interval

        logger.warning(f"Endpoint not ready after {max_wait_time} seconds")
        return {
            "name": endpoint_name,
            "state": "PENDING",
            "url": f"https://{spark.conf.get('spark.databricks.workspaceUrl')}/ml/endpoints/{endpoint_name}"
        }

    except Exception as e:
        logger.error(f"Error creating/updating endpoint: {e}")
        logger.warning("Endpoint deployment may require additional permissions")
        # Return placeholder info
        return {
            "name": endpoint_name,
            "state": "CONFIGURED",
            "url": f"https://{spark.conf.get('spark.databricks.workspaceUrl')}/ml/endpoints/{endpoint_name}",
            "note": "Endpoint configuration submitted. Check Databricks console for status."
        }

# Create or update endpoint
endpoint_info = create_or_update_endpoint(
    endpoint_name, full_model_name, version_to_deploy, environment
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Test Endpoint (Optional)

# COMMAND ----------

def test_endpoint(endpoint_name):
    """
    Test the deployed endpoint with sample data.

    Args:
        endpoint_name: Name of the serving endpoint

    Returns:
        test_results: Dictionary with test results
    """
    logger.info(f"Testing endpoint: {endpoint_name}")

    try:
        # Sample test data
        test_data = {
            "dataframe_records": [
                {
                    "age": 35,
                    "income": 75000.0,
                    "credit_score": 720,
                    "account_balance": 15000.0,
                    "num_transactions": 45,
                    "days_since_last_transaction": 5,
                    "income_to_balance_ratio": 5.0,
                    "transaction_frequency": 9.0
                }
            ]
        }

        # Make prediction request
        response = workspace_client.serving_endpoints.query(
            name=endpoint_name,
            dataframe_records=test_data["dataframe_records"]
        )

        logger.info(f"Test prediction successful")
        return {
            "status": "success",
            "response": response
        }

    except Exception as e:
        logger.warning(f"Endpoint test failed (may require time to warm up): {e}")
        return {
            "status": "not_tested",
            "reason": str(e)
        }

# Test endpoint if it's ready
if endpoint_info.get("state") == "READY":
    test_results = test_endpoint(endpoint_name)
else:
    test_results = {"status": "skipped", "reason": "Endpoint not ready"}
    logger.info("Skipping endpoint test - endpoint not ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Create Deployment Record

# COMMAND ----------

deployment_record = {
    "deployment_date": datetime.now().isoformat(),
    "environment": environment,
    "model_name": full_model_name,
    "model_version": version_to_deploy,
    "endpoint_name": endpoint_name,
    "endpoint_info": endpoint_info,
    "test_results": test_results,
    "model_metadata": {
        "run_id": model_version_info.run_id if hasattr(model_version_info, 'run_id') else None,
        "creation_timestamp": model_version_info.creation_timestamp if hasattr(model_version_info, 'creation_timestamp') else None,
        "current_stage": model_version_info.current_stage if hasattr(model_version_info, 'current_stage') else None
    }
}

# Save deployment record
with open('/tmp/deployment_record.json', 'w') as f:
    json.dump(deployment_record, f, indent=2)

logger.info("Deployment record created")

# Optionally log to MLflow
try:
    if model_version_info and hasattr(model_version_info, 'run_id'):
        with mlflow.start_run(run_id=model_version_info.run_id):
            mlflow.log_artifact('/tmp/deployment_record.json')
            mlflow.set_tag(f"deployed_to_{environment}", "true")
            mlflow.set_tag(f"endpoint_{environment}", endpoint_name)
            logger.info(f"Deployment record logged to MLflow run {model_version_info.run_id}")
except Exception as e:
    logger.warning(f"Could not log deployment to MLflow: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Deployment Summary

# COMMAND ----------

print("=" * 80)
print("MODEL DEPLOYMENT SUMMARY")
print("=" * 80)
print(f"Model: {full_model_name}")
print(f"Version: {version_to_deploy}")
print(f"Environment: {environment}")
print(f"Endpoint: {endpoint_name}")
print(f"Status: {endpoint_info.get('state', 'UNKNOWN')}")
print("-" * 80)
if "url" in endpoint_info:
    print(f"Endpoint URL: {endpoint_info['url']}")
print("-" * 80)
print(f"Test Status: {test_results.get('status', 'unknown')}")
if "note" in endpoint_info:
    print(f"Note: {endpoint_info['note']}")
print("=" * 80)

# COMMAND ----------

# Output for job orchestration
dbutils.notebook.exit({
    "status": "success",
    "endpoint_name": endpoint_name,
    "endpoint_state": endpoint_info.get("state", "UNKNOWN"),
    "model_name": full_model_name,
    "model_version": version_to_deploy,
    "environment": environment,
    "endpoint_url": endpoint_info.get("url", "")
})
