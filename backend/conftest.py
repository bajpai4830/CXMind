from __future__ import annotations

import sys
from pathlib import Path
import os
import uuid

# Ensure `import app` works when running pytest from different working directories.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Keep tests isolated from any developer/local database.
_tmp_root = Path(__file__).resolve().parent / ".tmp"
_tmp_root.mkdir(parents=True, exist_ok=True)
_db_path = _tmp_root / f"cxmind_test_{uuid.uuid4().hex}.db"
os.environ.setdefault("CXMIND_DATABASE_URL", f"sqlite:///{_db_path.as_posix()}")
