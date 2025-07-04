# Contributing to Lightweight Task Runner with DAG Scheduling

Thank you for your interest in contributing to the Lightweight Task Runner! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Setting up the Development Environment

1. Clone the repository:
```bash
git clone <repository-url>
cd "Lightweight Task Runner with DAG Scheduling"
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate
```

4. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -e .[dev]
```

## Development Workflow

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests  
python -m pytest tests/e2e/          # End-to-end tests

# Run with coverage
python -m pytest --cov=task_runner --cov-report=html
```

### Code Style

We use several tools to maintain code quality:

```bash
# Format code with Black
black task_runner/ tests/ examples/

# Lint with flake8
flake8 task_runner/ tests/ examples/

# Type checking with mypy
mypy task_runner/
```

### Testing Your Changes

1. Write tests for new functionality
2. Ensure all existing tests pass
3. Test with example DAGs:
```bash
python -m task_runner.cli run --config examples/simple_dag.json
python -m task_runner.cli run --config examples/complex_dag.json
```

### Documentation

- Update docstrings for new functions and classes
- Update README.md if adding new features
- Add examples for new functionality

## Contribution Guidelines

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes and commit them:
```bash
git commit -m "Add: Brief description of your changes"
```

4. Push to your fork and create a pull request

### Commit Message Format

Use clear, descriptive commit messages:
- `Add: New feature or functionality`
- `Fix: Bug fixes`
- `Update: Changes to existing functionality`
- `Docs: Documentation updates`
- `Test: Test additions or modifications`
- `Refactor: Code restructuring without functional changes`

### Code Review Process

All submissions require review. We use GitHub pull requests for this purpose. Reviewers will check for:

- Code quality and style
- Test coverage
- Documentation updates
- Backward compatibility
- Performance considerations

## Types of Contributions

### Bug Reports

When filing a bug report, please include:
- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant logs or error messages

### Feature Requests

For new features, please provide:
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Potential impact on existing functionality

### Code Contributions

We welcome contributions in the following areas:

#### Core Features
- New task types
- Enhanced scheduling algorithms
- Performance optimizations
- Error handling improvements

#### Utilities
- New visualization options
- Additional configuration formats
- Monitoring and metrics
- Integration tools

#### Documentation
- API documentation
- Usage examples
- Tutorials and guides
- Performance benchmarks

#### Testing
- Additional test cases
- Performance tests
- Integration tests
- Example DAGs

## Development Guidelines

### Architecture Principles

1. **Modularity**: Keep components loosely coupled
2. **Extensibility**: Design for easy extension and customization
3. **Simplicity**: Favor simple, understandable solutions
4. **Performance**: Consider performance implications
5. **Reliability**: Ensure robust error handling

### Code Quality Standards

- Write clear, readable code
- Add comprehensive docstrings
- Include type hints where appropriate
- Handle errors gracefully
- Write meaningful tests
- Follow existing patterns and conventions

### Adding New Task Types

To add a new task type:

1. Extend the `Task` class or create a new task implementation
2. Update configuration validation
3. Add corresponding tests
4. Update documentation and examples
5. Consider backward compatibility

### Adding New Features

When adding new features:

1. Design for configurability
2. Maintain backward compatibility
3. Add comprehensive tests
4. Document the feature thoroughly
5. Consider performance impact

## Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Reach out to maintainers for guidance

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- GitHub contributor statistics

Thank you for contributing to the Lightweight Task Runner with DAG Scheduling!
