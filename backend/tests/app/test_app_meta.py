def test_app_package_has_version():
    """Quick check that `app` package exposes a version string in its __init__.
    This test adjusts sys.path so `backend/` is importable and then imports `app`.
    """
    import importlib
    import sys
    from pathlib import Path

    # Ensure backend/ is on sys.path so `import app` works
    repo_root = Path(__file__).resolve().parents[2]
    backend_path = str(repo_root / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    app = importlib.import_module("app")
    assert hasattr(app, "__version__"), "app package should define __version__"
    assert isinstance(app.__version__, str) and app.__version__, "__version__ should be a non-empty string"
