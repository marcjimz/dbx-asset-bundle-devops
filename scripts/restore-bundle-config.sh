#!/bin/bash
# Script to restore original databricks.yml from backup
# Usage: ./scripts/restore-bundle-config.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUNDLE_CONFIG="${PROJECT_ROOT}/databricks.yml"
BACKUP_CONFIG="${BUNDLE_CONFIG}.bak"

if [ -f "$BACKUP_CONFIG" ]; then
    mv "$BACKUP_CONFIG" "$BUNDLE_CONFIG"
    echo "♻️  Restored original databricks.yml from backup"
else
    echo "ℹ️  No backup found, nothing to restore"
fi

# Clean up any temp files
rm -f "${BUNDLE_CONFIG}.tmp"
