"""Compatibility entry; maintained implementation: tools/research/FreezePreManuscriptCompute.py."""
from pathlib import Path as _Path
_target = _Path(__file__).resolve().parents[1] / 'tools/research/FreezePreManuscriptCompute.py'
exec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), globals())
