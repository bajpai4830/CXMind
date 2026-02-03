from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import os

# Ensure `import app` works when running pytest from different working directories.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Keep tests isolated from any developer/local database.
_tmp_dir = Path(tempfile.mkdtemp(prefix="cxmind_test_db_"))
os.environ.setdefault("CXMIND_DATABASE_URL", f"sqlite:///{(_tmp_dir / 'cxmind_test.db').as_posix()}")
