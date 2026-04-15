"""Support running modules through the top-level ``src`` package."""

from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent
package_root_str = str(PACKAGE_ROOT)

if package_root_str not in sys.path:
    sys.path.insert(0, package_root_str)
