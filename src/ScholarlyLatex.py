"""Compatibility import for the scholarly layout renderer."""
from pathlib import Path
_root=next(p for p in Path(__file__).resolve().parents if (p/'pyproject.toml').is_file())
_target=_root/'tools/publication/ScholarlyLatex.py'
exec(compile(_target.read_text(encoding='utf-8'),str(_target),'exec'),globals())
