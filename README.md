# Collective Fragmentsblock

Aurora fragment block: reusable content fragments referenced live from central fragment documents

## Features

- Compatible with Plone 6.0+

## Installation

Add `collective.fragmentsblock` to your project's dependencies:

```python
# In your pyproject.toml
dependencies = [
    "collective.fragmentsblock",
    # ...
]
```

Then activate the addon in your Plone site's control panel or via GenericSetup.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/collective/collective.fragmentsblock.git
cd collective.fragmentsblock

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[test]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=collective.fragmentsblock --cov-report=html
```

## License

GPL-2.0-or-later

## Author

Maik Derstappen <md@derico.de>
