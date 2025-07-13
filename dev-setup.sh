#!/bin/bash

set -e  # Exit on first error

# === CONFIG ===
VENV_DIR=".venv"
PYTHON=$(which python3)

echo "📦 Checking for virtual environment..."

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "🛠️  Creating virtual environment at $VENV_DIR..."
  uv venv "$VENV_DIR"
else
  echo "✅ Virtual environment already exists."
fi

# Step 2: Activate the virtual environment
echo "🔁 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 3: Install dev tools
echo "📦 Installing dev dependencies..."
uv add --dev black ruff mypy pytest jupyter ipykernel pre-commit

# Step 4: Set up pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

echo "✅ Setup complete!"
