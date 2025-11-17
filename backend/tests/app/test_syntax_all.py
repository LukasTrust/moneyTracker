import ast
from pathlib import Path


def test_all_python_files_parse_without_execution():
    """Parse every .py file under backend/app with ast to ensure syntax validity without importing/executing them."""
    # Determine repository root robustly: walk upwards until we find a directory containing backend/app
    current = Path(__file__).resolve()
    repo_root = None
    for parent in current.parents:
        candidate = parent / "backend" / "app"
        if candidate.exists() and candidate.is_dir():
            repo_root = parent
            break

    assert repo_root is not None, "Could not locate repository root containing backend/app"
    app_dir = repo_root / "backend" / "app"

    py_files = sorted(app_dir.rglob("*.py"))
    assert py_files, "No python files found under app/"

    for path in py_files:
        # read and parse source to avoid running top-level code
        src = path.read_text(encoding="utf-8")
        try:
            ast.parse(src, filename=str(path))
        except SyntaxError as e:
            raise AssertionError(f"Syntax error in {path}: {e}")
