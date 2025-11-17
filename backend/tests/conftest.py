import sys
from pathlib import Path

# Ensure backend/ is importable for tests
repo_root = Path(__file__).resolve().parents[2]
backend_path = str(repo_root / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
