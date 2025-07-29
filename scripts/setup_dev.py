#!/usr/bin/env python3
"""Development environment setup script."""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=True, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Check if Python version is compatible."""
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def install_uv():
    """Install uv if not already installed."""
    try:
        run_command("uv --version", check=False)
        print("✓ uv is already installed")
        return
    except FileNotFoundError:
        pass

    print("Installing uv...")
    run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")


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
    directories = ["logs", "config", "data", "models"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")

    # Copy environment file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")

    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        run_command("cp env.example .env")
        print("✓ Created .env file")
        print("⚠️  Please edit .env file with your configuration")

    # Install pre-commit hooks
    print("Installing pre-commit hooks...")
    run_command("pre-commit install")
    print("✓ Pre-commit hooks installed")

    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start services: docker-compose up -d")
    print("3. Run tests: pytest")
    print("4. Start development: uvicorn services.api.main:app --reload")


def main():
    """Main setup function."""
    setup_environment()


if __name__ == "__main__":
    main()
