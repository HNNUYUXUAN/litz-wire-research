"""Compatibility entry; maintained implementation: models/geometry/src/TopologyCandidates.py."""
from pathlib import Path as _Path
_target = _Path(__file__).resolve().parents[1] / 'models/geometry/src/TopologyCandidates.py'
exec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), globals())
