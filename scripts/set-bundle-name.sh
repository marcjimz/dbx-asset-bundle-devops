#!/bin/bash
# Script to set bundle name dynamically based on branch
# Usage: ./scripts/set-bundle-name.sh [branch-name]
#
# This creates a temporary databricks.yml with the branch-specific bundle name

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUNDLE_CONFIG="${PROJECT_ROOT}/databricks.yml"

# Get branch name from argument or git
if [ -n "$1" ]; then
    BRANCH_NAME="$1"
else
    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
fi

# Sanitize branch name for Databricks
# Convert to lowercase, replace special chars with hyphens, limit to 30 chars
SANITIZED=$(echo "$BRANCH_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | cut -c1-30)

# Determine bundle name
if [[ "$BRANCH_NAME" == "main" || "$BRANCH_NAME" == "develop" ]]; then
    BUNDLE_NAME="mlops-production-pipeline"
    echo "Using main branch bundle name: $BUNDLE_NAME"
else
    BUNDLE_NAME="mlops-production-pipeline-${SANITIZED}"
    echo "Using feature branch bundle name: $BUNDLE_NAME"
fi

# Update bundle name in databricks.yml
if [ -f "$BUNDLE_CONFIG" ]; then
    # Create backup
    cp "$BUNDLE_CONFIG" "${BUNDLE_CONFIG}.bak"

    # Update the name field
    sed -i.tmp "s/name: mlops-production-pipeline$/name: ${BUNDLE_NAME}/" "$BUNDLE_CONFIG"
    rm -f "${BUNDLE_CONFIG}.tmp"

    echo "✅ Updated bundle name in databricks.yml"
    echo "📦 Bundle: $BUNDLE_NAME"
    echo "📂 Backup: ${BUNDLE_CONFIG}.bak"
else
    echo "❌ Error: databricks.yml not found at $BUNDLE_CONFIG"
    exit 1
fi

# Export for use in other scripts
export BUNDLE_NAME
echo "BUNDLE_NAME=${BUNDLE_NAME}" >> "${GITHUB_OUTPUT:-/dev/null}"
