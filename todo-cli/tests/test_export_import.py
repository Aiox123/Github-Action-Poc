import argparse
import json

import todo.cli as cli
from todo.repositories.json_repo import JsonTodoRepository
from todo.services import TodoService


def test_export_and_import_overwrite(tmp_path):
    data_file = tmp_path / "data.json"
    repo = JsonTodoRepository(data_file)
    service = TodoService(repo)

    # Create two items
    service.add("task one")
    service.add("task two")

    export_file = tmp_path / "export.json"
    # Call CLI handler for export
    args = argparse.Namespace(file=str(export_file))
    rc = cli._cmd_export(args, service)
    assert rc == 0
    assert export_file.exists()

    # Overwrite repository to ensure import --overwrite restores original
    repo.replace_all([])
    args_imp = argparse.Namespace(file=str(export_file), mode="overwrite")
    rc2 = cli._cmd_import(args_imp, service)
    assert rc2 == 0

    with export_file.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    # Compare repository contents to exported payload
    items = [i.to_dict() for i in service.list()]
    assert items == raw


def test_import_validation_failure_cli(tmp_path, capsys):
    data_file = tmp_path / "data.json"
    repo = JsonTodoRepository(data_file)
    service = TodoService(repo)

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"id": 1, "done": False}]), encoding="utf-8")

    args = argparse.Namespace(file=str(bad), mode="merge")
    rc = cli._cmd_import(args, service)
    captured = capsys.readouterr()
    assert rc == 1
    assert "title" in captured.err or "缺失" in captured.err
