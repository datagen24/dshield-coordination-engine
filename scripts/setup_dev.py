#!/usr/bin/env python3
"""Development environment setup script."""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("Error: Python 3.11+ is required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def install_uv():
    """Install uv package manager if not present."""
    try:
        result = run_command("uv --version", check=False)
        if result.returncode == 0:
            print("✓ uv is already installed")
            return
    except FileNotFoundError:
        pass
    
    print("Installing uv...")
    run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("✓ uv installed successfully")


def setup_environment():
    """Set up the development environment."""
    print("Setting up DShield Coordination Engine development environment...")
    
    # Check Python version
    check_python_version()
    
    # Install uv
    install_uv()
    
    # Install dependencies
    print("Installing dependencies...")
    run_command("uv sync --dev")
    
    # Create necessary directories
    print("Creating directories...")
    directories = [
        "logs",
        "config",
        "data",
        "models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")
    
    # Copy environment file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        run_command(f"cp {env_example} {env_file}")
        print("✓ Created .env file")
        print("⚠️  Please edit .env file with your configuration")
    
    # Install pre-commit hooks
    print("Installing pre-commit hooks...")
    run_command("pre-commit install")
    print("✓ Pre-commit hooks installed")
    
    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Run 'docker-compose up -d' to start services")
    print("3. Run 'pytest' to run tests")
    print("4. Run 'uvicorn services.api.main:app --reload' to start the API")


def main():
    """Main setup function."""
    setup_environment()


if __name__ == "__main__":
    main() 