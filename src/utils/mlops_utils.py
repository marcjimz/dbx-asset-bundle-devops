"""
MLOps Utility Functions

Common utility functions used across MLOps pipelines for logging,
monitoring, and data validation.
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for MLOps pipeline.

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(name)
    return logger


def validate_parameters(params: Dict[str, Any], required: List[str]) -> bool:
    """
    Validate that required parameters are present.

    Args:
        params: Dictionary of parameters
        required: List of required parameter keys

    Returns:
        True if all required parameters are present

    Raises:
        ValueError: If required parameters are missing
    """
    missing = [key for key in required if key not in params or params[key] is None]

    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

    return True


def format_metrics(metrics: Dict[str, float], precision: int = 4) -> Dict[str, str]:
    """
    Format metric values for display.

    Args:
        metrics: Dictionary of metric name to value
        precision: Decimal precision (default: 4)

    Returns:
        Dictionary of formatted metric strings
    """
    return {
        name: f"{value:.{precision}f}" if isinstance(value, (int, float)) else str(value)
        for name, value in metrics.items()
    }


def create_run_summary(
    run_id: str,
    status: str,
    metrics: Dict[str, Any],
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a standardized run summary.

    Args:
        run_id: MLflow run ID
        status: Run status (success, failed, etc.)
        metrics: Dictionary of metrics
        parameters: Dictionary of parameters

    Returns:
        Run summary dictionary
    """
    return {
        "run_id": run_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "parameters": parameters
    }


def save_artifact(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data as JSON artifact.

    Args:
        data: Dictionary to save
        filepath: Path to save the artifact
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_artifact(filepath: str) -> Dict[str, Any]:
    """
    Load JSON artifact.

    Args:
        filepath: Path to load the artifact from

    Returns:
        Loaded dictionary
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def get_environment_config(catalog: str) -> Dict[str, Any]:
    """
    Determine environment configuration from catalog name.

    Args:
        catalog: Unity Catalog name

    Returns:
        Environment configuration dictionary
    """
    if "prod" in catalog.lower():
        environment = "prod"
        log_level = logging.WARNING
    elif "stg" in catalog.lower() or "staging" in catalog.lower():
        environment = "stg"
        log_level = logging.INFO
    else:
        environment = "dev"
        log_level = logging.DEBUG

    return {
        "environment": environment,
        "log_level": log_level,
        "is_production": environment == "prod"
    }


def create_notification_message(
    title: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create standardized notification message.

    Args:
        title: Notification title
        status: Status (success, failed, warning)
        details: Additional details to include

    Returns:
        Formatted notification message
    """
    status_emoji = {
        "success": "✅",
        "failed": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }

    emoji = status_emoji.get(status.lower(), "")
    message = f"{emoji} {title}\n"
    message += f"Status: {status}\n"
    message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    if details:
        message += "\nDetails:\n"
        for key, value in details.items():
            message += f"  {key}: {value}\n"

    return message


def validate_model_metrics(
    metrics: Dict[str, float],
    thresholds: Dict[str, float]
) -> tuple[bool, List[str]]:
    """
    Validate model metrics against thresholds.

    Args:
        metrics: Dictionary of metric values
        thresholds: Dictionary of minimum threshold values

    Returns:
        Tuple of (validation_passed, failed_metrics)
    """
    failed_metrics = []

    for metric_name, threshold in thresholds.items():
        metric_value = metrics.get(metric_name, 0)

        if metric_value < threshold:
            failed_metrics.append(
                f"{metric_name}: {metric_value:.4f} < {threshold:.4f}"
            )

    validation_passed = len(failed_metrics) == 0

    return validation_passed, failed_metrics


def calculate_data_quality_score(
    total_records: int,
    null_count: int,
    duplicate_count: int,
    outlier_count: int
) -> float:
    """
    Calculate data quality score.

    Args:
        total_records: Total number of records
        null_count: Number of records with null values
        duplicate_count: Number of duplicate records
        outlier_count: Number of outlier records

    Returns:
        Data quality score (0-100)
    """
    if total_records == 0:
        return 0.0

    issues = null_count + duplicate_count + outlier_count
    clean_records = total_records - issues

    quality_score = (clean_records / total_records) * 100

    return min(100.0, max(0.0, quality_score))


def format_table_name(catalog: str, schema: str, table: str) -> str:
    """
    Format fully qualified table name.

    Args:
        catalog: Catalog name
        schema: Schema name
        table: Table name

    Returns:
        Fully qualified table name
    """
    return f"{catalog}.{schema}.{table}"


def extract_run_info(run_output: str) -> Dict[str, Any]:
    """
    Extract information from notebook run output.

    Args:
        run_output: JSON string from dbutils.notebook.exit()

    Returns:
        Parsed run information
    """
    try:
        return json.loads(run_output)
    except json.JSONDecodeError:
        return {"status": "unknown", "output": run_output}
