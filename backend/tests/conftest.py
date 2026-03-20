"""
Pytest configuration file to ensure app module imports work correctly.
This automatically adds the backend directory to the Python path.
"""
import sys
from pathlib import Path

# Add the parent directory (backend root) to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
