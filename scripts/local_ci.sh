#!/bin/bash

# Local CI script that mirrors the GitHub Actions pipeline
# Run this before pushing to ensure all checks pass locally

set -e  # Exit on any error

echo "🔍 Running local CI checks (mirroring GitHub Actions pipeline)..."
echo "================================================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "📦 Installing core dependencies..."
uv sync --dev

echo "🧹 Running linting checks..."
echo "Running ruff check..."
uv run ruff check .
echo "Running ruff format check..."
uv run ruff format --check .
echo "Running mypy..."
uv run mypy services agents tools

echo "🧪 Running tests..."
uv run pytest --cov=services --cov=agents --cov=tools --cov-report=xml --cov-report=html

echo "✅ All local CI checks passed!"
echo "🚀 Ready to push to GitHub"
