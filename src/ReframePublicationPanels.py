"""Compatibility entry; maintained implementation: tools/publication/ReframePublicationPanels.py."""
from pathlib import Path as _Path
_target = _Path(__file__).resolve().parents[1] / 'tools/publication/ReframePublicationPanels.py'
exec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), globals())
