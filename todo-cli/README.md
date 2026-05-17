# Todo CLI & API

A layered Python todo manager that demonstrates a more realistic project
structure inside `Github-Action-Poc`. Exposes both a CLI and a REST API
sharing the same service / repository core.

## Architecture

```
todo-cli/
├── pyproject.toml
├── main.py                     # `python main.py <cmd>` compatibility entry
├── todo/
│   ├── __init__.py
│   ├── config.py               # Settings (TODO_DATA_FILE override)
│   ├── models.py               # TodoItem domain dataclass
│   ├── repositories/
│   │   ├── base.py             # TodoRepository ABC
│   │   └── json_repo.py        # JSON file implementation
│   ├── services.py             # TodoService (business rules + id gen)
│   ├── cli.py                  # argparse CLI
│   └── api.py                  # FastAPI HTTP interface
└── tests/
    ├── conftest.py
    ├── unit/                   # models / repository / service
    └── integration/            # CLI / API end-to-end
```

Data is persisted to `todo-cli/todos.json` by default, or to any path
specified via the `TODO_DATA_FILE` environment variable.

## Requirements

- Python ≥ 3.10
- Runtime: `fastapi`, `uvicorn`
- Dev: `pytest`, `pytest-cov`, `httpx`, `ruff`

## Setup

```bash
cd todo-cli
pip install -e ".[dev]"
```

## CLI usage

```bash
python main.py --help
python main.py add "Read the docs"
python main.py add "Ship the PoC"
python main.py list
python main.py done 1
python main.py rm 2
```

Or, after `pip install -e .`, use the `todo` entry point directly:

```bash
todo add "Hello"
todo list
```

## REST API usage

```bash
uvicorn todo.api:app --reload
# then:
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/todos -H 'Content-Type: application/json' -d '{"title":"hi"}'
curl http://localhost:8000/todos
```

Interactive docs: http://localhost:8000/docs

## Quality gates

```bash
ruff check .
pytest --cov
```

`pyproject.toml` enforces:
- coverage `fail_under = 80`
- ruff rule sets `E, F, I, B, UP, SIM`
