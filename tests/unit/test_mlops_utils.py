"""
Unit tests for MLOps utility functions
"""

import pytest
import json
import os
from src.utils.mlops_utils import (
    setup_logging,
    validate_parameters,
    format_metrics,
    create_run_summary,
    save_artifact,
    load_artifact,
    get_environment_config,
    create_notification_message,
    validate_model_metrics,
    calculate_data_quality_score,
    format_table_name,
    extract_run_info,
)


class TestLogging:
    """Test logging configuration"""

    def test_setup_logging(self):
        """Test logger setup"""
        logger = setup_logging("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_logging_level(self):
        """Test logging level configuration"""
        import logging

        logger = setup_logging("test_logger", level=logging.DEBUG)
        assert logger.level == logging.DEBUG


class TestParameterValidation:
    """Test parameter validation"""

    def test_valid_parameters(self):
        """Test validation with all required parameters"""
        params = {
            "catalog": "dev_catalog",
            "schema": "ml_models",
            "model": "test_model",
        }
        required = ["catalog", "schema"]
        assert validate_parameters(params, required) is True

    def test_missing_parameters(self):
        """Test validation with missing parameters"""
        params = {"catalog": "dev_catalog"}
        required = ["catalog", "schema"]

        with pytest.raises(ValueError) as exc_info:
            validate_parameters(params, required)

        assert "Missing required parameters" in str(exc_info.value)

    def test_none_parameters(self):
        """Test validation with None values"""
        params = {"catalog": "dev_catalog", "schema": None}
        required = ["catalog", "schema"]

        with pytest.raises(ValueError):
            validate_parameters(params, required)


class TestMetricsFormatting:
    """Test metrics formatting"""

    def test_format_float_metrics(self):
        """Test formatting float metrics"""
        metrics = {"accuracy": 0.857621, "f1_score": 0.923456}
        formatted = format_metrics(metrics, precision=4)

        assert formatted["accuracy"] == "0.8576"
        assert formatted["f1_score"] == "0.9235"

    def test_format_mixed_metrics(self):
        """Test formatting mixed type metrics"""
        metrics = {"accuracy": 0.85, "model_type": "RandomForest", "epochs": 100}
        formatted = format_metrics(metrics)

        assert formatted["accuracy"] == "0.8500"
        assert formatted["model_type"] == "RandomForest"
        assert formatted["epochs"] == "100"


class TestRunSummary:
    """Test run summary creation"""

    def test_create_run_summary(self):
        """Test run summary creation"""
        run_id = "test_run_123"
        status = "success"
        metrics = {"accuracy": 0.85}
        parameters = {"learning_rate": 0.01}

        summary = create_run_summary(run_id, status, metrics, parameters)

        assert summary["run_id"] == run_id
        assert summary["status"] == status
        assert summary["metrics"] == metrics
        assert summary["parameters"] == parameters
        assert "timestamp" in summary


class TestArtifactOperations:
    """Test artifact save/load operations"""

    def test_save_and_load_artifact(self, tmp_path):
        """Test saving and loading artifacts"""
        data = {"test": "data", "value": 123}
        filepath = tmp_path / "test_artifact.json"

        # Save artifact
        save_artifact(data, str(filepath))
        assert filepath.exists()

        # Load artifact
        loaded_data = load_artifact(str(filepath))
        assert loaded_data == data

    def test_load_nonexistent_artifact(self):
        """Test loading non-existent artifact"""
        with pytest.raises(FileNotFoundError):
            load_artifact("/nonexistent/path/artifact.json")


class TestEnvironmentConfig:
    """Test environment configuration"""

    def test_prod_environment(self):
        """Test production environment detection"""
        config = get_environment_config("prod_catalog")

        assert config["environment"] == "prod"
        assert config["is_production"] is True

    def test_stg_environment(self):
        """Test staging environment detection"""
        config = get_environment_config("stg_catalog")

        assert config["environment"] == "stg"
        assert config["is_production"] is False

    def test_dev_environment(self):
        """Test dev environment detection"""
        config = get_environment_config("dev_catalog")

        assert config["environment"] == "dev"
        assert config["is_production"] is False


class TestNotifications:
    """Test notification message creation"""

    def test_success_notification(self):
        """Test success notification message"""
        message = create_notification_message("Test Title", "success")

        assert "Test Title" in message
        assert "success" in message
        assert "✅" in message

    def test_failed_notification(self):
        """Test failed notification message"""
        message = create_notification_message("Test Failed", "failed")

        assert "Test Failed" in message
        assert "failed" in message
        assert "❌" in message

    def test_notification_with_details(self):
        """Test notification with details"""
        details = {"model": "test_model", "accuracy": 0.85}
        message = create_notification_message("Test Title", "info", details)

        assert "model" in message
        assert "accuracy" in message


class TestModelMetricsValidation:
    """Test model metrics validation"""

    def test_metrics_pass_validation(self):
        """Test metrics that pass validation"""
        metrics = {"accuracy": 0.85, "f1_score": 0.75}
        thresholds = {"accuracy": 0.80, "f1_score": 0.70}

        passed, failed = validate_model_metrics(metrics, thresholds)

        assert passed is True
        assert len(failed) == 0

    def test_metrics_fail_validation(self):
        """Test metrics that fail validation"""
        metrics = {"accuracy": 0.75, "f1_score": 0.65}
        thresholds = {"accuracy": 0.80, "f1_score": 0.70}

        passed, failed = validate_model_metrics(metrics, thresholds)

        assert passed is False
        assert len(failed) == 2

    def test_partial_metrics_validation(self):
        """Test partial metrics validation"""
        metrics = {"accuracy": 0.85, "f1_score": 0.65}
        thresholds = {"accuracy": 0.80, "f1_score": 0.70}

        passed, failed = validate_model_metrics(metrics, thresholds)

        assert passed is False
        assert len(failed) == 1
        assert "f1_score" in failed[0]


class TestDataQualityScore:
    """Test data quality score calculation"""

    def test_perfect_quality(self):
        """Test perfect data quality"""
        score = calculate_data_quality_score(
            total_records=1000, null_count=0, duplicate_count=0, outlier_count=0
        )

        assert score == 100.0

    def test_with_issues(self):
        """Test quality with data issues"""
        score = calculate_data_quality_score(
            total_records=1000, null_count=50, duplicate_count=30, outlier_count=20
        )

        assert score == 90.0

    def test_zero_records(self):
        """Test with zero records"""
        score = calculate_data_quality_score(
            total_records=0, null_count=0, duplicate_count=0, outlier_count=0
        )

        assert score == 0.0


class TestTableNameFormatting:
    """Test table name formatting"""

    def test_format_table_name(self):
        """Test table name formatting"""
        full_name = format_table_name("catalog", "schema", "table")
        assert full_name == "catalog.schema.table"

    def test_format_with_special_names(self):
        """Test formatting with special names"""
        full_name = format_table_name("dev_catalog", "ml_models", "customer_features")
        assert full_name == "dev_catalog.ml_models.customer_features"


class TestRunInfoExtraction:
    """Test run info extraction"""

    def test_extract_valid_json(self):
        """Test extracting valid JSON"""
        output = json.dumps({"status": "success", "run_id": "123"})
        info = extract_run_info(output)

        assert info["status"] == "success"
        assert info["run_id"] == "123"

    def test_extract_invalid_json(self):
        """Test extracting invalid JSON"""
        output = "not valid json"
        info = extract_run_info(output)

        assert info["status"] == "unknown"
        assert info["output"] == output
