import ast
from pathlib import Path
import pytest


def _category_from_path(p: Path):
    parts = p.parts
    # Expect path like .../backend/app/<category>/file.py
    try:
        idx = parts.index('app')
        return parts[idx + 1] if len(parts) > idx + 1 else None
    except ValueError:
        return None


@pytest.mark.parametrize("py_path", sorted([str(p) for p in Path(__file__).resolve().parents[2].joinpath('backend', 'app').rglob('*.py')]))
def test_structural_expectations(py_path):
    """Run lightweight structural checks on each module using AST (no imports).

    Rules (heuristics):
    - routers: must define a top-level name `router` (Assign target)
    - models/schemas: must define at least one ClassDef
    - services: must define at least one FunctionDef or ClassDef
    - database.py: must define `engine` (Assign) and `get_db` (FunctionDef)
    - main.py: must assign `app` (Assign)
    - others: must contain at least one top-level statement
    """
    path = Path(py_path)
    src = path.read_text(encoding='utf-8')
    tree = ast.parse(src, filename=str(path))

    category = _category_from_path(path)

    # Skip package __init__ files - they may intentionally be empty or re-export symbols
    if path.name == "__init__.py":
        return

    def has_assign_named(name):
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == name:
                        return True
        return False

    def has_function(name=None):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if name is None or node.name == name:
                    return True
        return False

    def has_class():
        return any(isinstance(n, ast.ClassDef) for n in tree.body)

    def has_function_or_class():
        return any(isinstance(n, (ast.FunctionDef, ast.ClassDef)) for n in tree.body)

    # Router files
    if category == 'routers':
        assert has_assign_named('router'), f"Router file {path} should define top-level 'router'"
        return

    # Models and schemas should define classes
    if category in ('models', 'schemas'):
        assert has_class(), f"{category} file {path} should define at least one class"
        return

    # Services should have functions or classes
    if category == 'services':
        assert has_function_or_class(), f"service file {path} should define functions or classes"
        return

    # database expectations
    if path.name == 'database.py':
        assert has_assign_named('engine'), "database.py should assign 'engine'"
        assert has_function('get_db'), "database.py should define function 'get_db'"
        return

    # main expectations
    if path.name == 'main.py':
        assert has_assign_named('app'), "main.py should assign 'app' (FastAPI instance)"
        return

    # fallback: ensure file isn't empty (has at least one top-level statement)
    assert len(tree.body) > 0, f"File {path} appears empty"
