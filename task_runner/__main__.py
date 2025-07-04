"""
Main entry point for the task runner CLI.
Allows running the CLI with: python -m task_runner
"""

from .cli.main import cli

if __name__ == '__main__':
    cli()
