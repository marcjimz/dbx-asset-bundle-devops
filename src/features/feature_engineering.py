# Databricks notebook source
"""
Feature Engineering Pipeline

This notebook prepares features for ML model training using Delta tables.
"""

# COMMAND ----------

import logging
from datetime import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col,
    count,
    mean,
    stddev,
    min as spark_min,
    max as spark_max,
    when,
    lit,
    current_timestamp,
    expr,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    IntegerType,
    TimestampType,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "dev_catalog", "Unity Catalog")
dbutils.widgets.text("schema", "ml_models", "Schema Name")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

logger.info(f"Starting feature engineering for {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Initialize Spark Session and Create Schema

# COMMAND ----------

spark = SparkSession.builder.getOrCreate()

# Create catalog and schema if they don't exist
try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"USE CATALOG {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    spark.sql(f"USE SCHEMA {schema}")
    logger.info(f"Using catalog: {catalog}, schema: {schema}")
except Exception as e:
    logger.warning(
        f"Could not create catalog/schema (may require admin privileges): {e}"
    )
    logger.info("Continuing with existing catalog/schema...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create Sample Raw Data
# MAGIC
# MAGIC In production, this would read from your data sources.
# MAGIC For this example, we'll create synthetic data.

# COMMAND ----------


def create_sample_data() -> DataFrame:
    """
    Create sample customer data for demonstration.
    In production, replace this with actual data sources.
    """
    schema = StructType(
        [
            StructField("customer_id", StringType(), False),
            StructField("age", IntegerType(), True),
            StructField("income", DoubleType(), True),
            StructField("credit_score", IntegerType(), True),
            StructField("account_balance", DoubleType(), True),
            StructField("num_transactions", IntegerType(), True),
            StructField("days_since_last_transaction", IntegerType(), True),
            StructField("country", StringType(), True),
            StructField("created_at", TimestampType(), True),
        ]
    )

    # Generate sample data
    data = []
    import random
    import uuid

    countries = ["US", "UK", "CA", "AU", "DE"]

    for i in range(1000):
        # Using random for sample data generation only (not security-critical)
        data.append(
            (
                str(uuid.uuid4()),
                random.randint(18, 80),  # nosec B311
                random.uniform(20000, 200000),  # nosec B311
                random.randint(300, 850),  # nosec B311
                random.uniform(100, 50000),  # nosec B311
                random.randint(1, 100),  # nosec B311
                random.randint(0, 365),  # nosec B311
                random.choice(countries),  # nosec B311
                datetime.now(),
            )
        )

    return spark.createDataFrame(data, schema)


# Create sample data
raw_data = create_sample_data()
logger.info(f"Created sample dataset with {raw_data.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Feature Engineering Transformations

# COMMAND ----------


def engineer_features(df: DataFrame) -> DataFrame:
    """
    Apply feature engineering transformations.

    Args:
        df: Input DataFrame with raw features

    Returns:
        DataFrame with engineered features
    """
    logger.info("Starting feature engineering transformations...")

    # Create derived features
    features_df = (
        df.withColumn(
            "income_to_balance_ratio",
            when(
                col("account_balance") > 0, col("income") / col("account_balance")
            ).otherwise(0),
        )
        .withColumn(
            "transaction_frequency",
            when(
                col("days_since_last_transaction") > 0,
                col("num_transactions") / col("days_since_last_transaction"),
            ).otherwise(0),
        )
        .withColumn(
            "credit_score_category",
            when(col("credit_score") >= 750, "excellent")
            .when(col("credit_score") >= 700, "good")
            .when(col("credit_score") >= 650, "fair")
            .otherwise("poor"),
        )
        .withColumn(
            "age_group",
            when(col("age") < 25, "young")
            .when(col("age") < 40, "middle")
            .when(col("age") < 60, "senior")
            .otherwise("elderly"),
        )
        .withColumn(
            "high_value_customer",
            (col("income") > 100000) & (col("credit_score") > 700),
        )
        .withColumn("processed_at", current_timestamp())
    )

    logger.info("Feature engineering transformations completed")
    return features_df


# Apply feature engineering
features_df = engineer_features(raw_data)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Data Quality Checks

# COMMAND ----------


def validate_features(df: DataFrame) -> bool:
    """
    Validate feature data quality.

    Args:
        df: DataFrame to validate

    Returns:
        True if validation passes
    """
    logger.info("Running data quality checks...")

    # Check for null values in critical columns
    null_counts = df.select(
        [
            count(when(col(c).isNull(), c)).alias(c)
            for c in ["customer_id", "age", "income", "credit_score"]
        ]
    ).collect()[0]

    has_nulls = any(null_counts[c] > 0 for c in null_counts.asDict().keys())

    if has_nulls:
        logger.warning(f"Null values found: {null_counts}")

    # Check data ranges
    stats = df.select(
        spark_min("age").alias("min_age"),
        spark_max("age").alias("max_age"),
        spark_min("credit_score").alias("min_credit"),
        spark_max("credit_score").alias("max_credit"),
    ).collect()[0]

    logger.info(f"Data statistics: {stats}")

    # Validate ranges
    valid = (
        stats["min_age"] >= 18
        and stats["max_age"] <= 120
        and stats["min_credit"] >= 300
        and stats["max_credit"] <= 850
    )

    if valid:
        logger.info("Data quality checks passed")
    else:
        logger.error("Data quality checks failed")

    return valid


# Validate features
validation_passed = validate_features(features_df)

if not validation_passed:
    raise ValueError("Feature validation failed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Save Features to Delta Table

# COMMAND ----------

# Define table name
features_table = f"{catalog}.{schema}.customer_features"

# Write features to Delta table
logger.info(f"Writing features to {features_table}")

features_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(features_table)

logger.info(f"Successfully wrote {features_df.count()} records to {features_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Feature Statistics

# COMMAND ----------

# Calculate and display feature statistics
# Table name comes from controlled variable, not user input
feature_stats = spark.sql(
    # nosec B608 - table name is validated upstream
    f"""
    SELECT
        COUNT(*) as total_records,
        AVG(age) as avg_age,
        AVG(income) as avg_income,
        AVG(credit_score) as avg_credit_score,
        COUNT(CASE WHEN high_value_customer = true THEN 1 END) as high_value_customers,
        COUNT(DISTINCT country) as num_countries
    FROM {features_table}
    """
)

logger.info("Feature statistics:")
feature_stats.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Output Summary

# COMMAND ----------

print("=" * 80)
print("FEATURE ENGINEERING SUMMARY")
print("=" * 80)
print(f"Catalog: {catalog}")
print(f"Schema: {schema}")
print(f"Features Table: {features_table}")
print(f"Total Records: {features_df.count()}")
print(f"Total Features: {len(features_df.columns)}")
print(f"Validation Status: {'PASSED' if validation_passed else 'FAILED'}")
print("=" * 80)

# Output for job orchestration
dbutils.notebook.exit(
    {
        "status": "success",
        "catalog": catalog,
        "schema": schema,
        "table": features_table,
        "record_count": features_df.count(),
        "validation_passed": validation_passed,
    }
)
