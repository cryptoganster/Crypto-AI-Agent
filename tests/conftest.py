"""Pytest configuration and fixtures.

Este archivo configura pytest para que pueda encontrar el módulo 'src'
agregando el directorio raíz del proyecto al Python path.

Nota: Se eliminaron tests obsoletos que referenciaban módulos que ya no existen:
- tests/unit/test_fix_imports.py (script fix_imports.py ya cumplió su propósito)
- tests/pbt/test_fix_imports_properties.py (script fix_imports.py ya cumplió su propósito)
- tests/integration/test_application_structure.py (lifecycle_manager.py fue eliminado en refactoring)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
