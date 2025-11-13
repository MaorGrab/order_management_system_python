#!/usr/bin/env bash
set -euo pipefail

echo "Simulating deployment for build $GITHUB_SHA..."
mkdir -p deploy_artifacts
echo "Deployed build $GITHUB_SHA on $(date)" > deploy_artifacts/deploy.log
echo "✅ Simulation complete. (No actual infrastructure used.)"
