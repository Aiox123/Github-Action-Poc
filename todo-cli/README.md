# Todo CLI

A tiny command-line todo manager written in Python. Demonstrates a minimal,
testable Python project layout suitable for use inside the
`Github-Action-Poc` repository.

## Requirements

- Python 3.9+
- (Optional) `pytest` for running the test suite

## Project layout

```
todo-cli/
├── main.py              # Entry point (python main.py <command>)
├── todo/
│   ├── __init__.py
│   ├── cli.py           # argparse-based CLI
│   └── storage.py       # JSON file storage helpers
├── tests/
│   └── test_storage.py
└── README.md
```

Todos are persisted to `todo-cli/todos.json` (created on first add).

## Usage

```bash
# Show help
python main.py --help

# Add tasks
python main.py add "Read the docs"
python main.py add "Ship the PoC"

# List
python main.py list

# Mark done / remove
python main.py done 1
python main.py rm 2
```

## Running tests

```bash
pip install pytest
pytest
```
