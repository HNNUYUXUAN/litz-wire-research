"""Compatibility entry; maintained implementation: adapters/ansys/ansys_native3d.py."""
from pathlib import Path as _Path
_target = _Path(__file__).resolve().parents[1] / 'adapters/ansys/ansys_native3d.py'
exec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), globals())
