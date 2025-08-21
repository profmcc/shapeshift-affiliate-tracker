# Contributing to ShapeShift Affiliate Listener

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.11+
- Git
- Basic understanding of blockchain and DeFi concepts

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/shapeshift-listener.git`
3. Install dependencies: `pip install -r requirements.txt`
4. Install dev dependencies: `pip install -r requirements.txt[dev]`
5. Copy `.env.example` to `.env` and configure your API keys

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clear, documented code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Code Quality Standards
We use several tools to maintain code quality:

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .

# Run tests
pytest
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add new affiliate protocol support"
```

Use conventional commit messages:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### 5. Push and Create a Pull Request
```bash
git push origin feature/your-feature-name
```

## Code Standards

### Python Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public functions
- Keep functions focused and single-purpose

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Implement proper logging
- Handle edge cases gracefully

### Testing
- Write unit tests for new functionality
- Aim for >80% code coverage
- Test both success and failure scenarios
- Use fixtures for common test data

## Project Structure

```
src/
├── shapeshift_listener/
│   ├── __init__.py
│   ├── core/           # Core functionality
│   ├── listeners/      # Protocol-specific listeners
│   ├── common/         # Shared utilities
│   └── cli.py          # Command-line interface
tests/                  # Test files
docs/                   # Documentation
config/                 # Configuration files
```

## Adding New Protocols

### 1. Create Listener Class
```python
from shapeshift_listener.core.base import BaseListener

class NewProtocolListener(BaseListener):
    def __init__(self, config):
        super().__init__(config)
    
    async def process_block(self, block_number: int):
        # Implementation here
        pass
```

### 2. Add Configuration
Update `config/shapeshift_config.yaml` with protocol-specific settings.

### 3. Add Tests
Create comprehensive tests for the new listener.

### 4. Update Documentation
Add protocol information to relevant documentation.

## Reporting Issues

### Bug Reports
Include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces

### Feature Requests
Include:
- Description of the desired feature
- Use case and benefits
- Implementation suggestions (if any)
- Priority level

## Getting Help

- **Documentation**: Check the docs/ directory
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Review**: Ask for help in pull request reviews

## Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog**: Update `CHANGELOG.md` with new features/fixes
3. **Tests**: Ensure all tests pass
4. **Documentation**: Update documentation as needed
5. **Tag**: Create a git tag for the release
6. **Publish**: Release to PyPI

## Code of Conduct

- Be respectful and inclusive
- Focus on technical discussions
- Help others learn and grow
- Constructive feedback is welcome
- Harassment will not be tolerated

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to ShapeShift Affiliate Listener! 🚀

