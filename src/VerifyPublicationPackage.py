"""Compatibility entry; maintained implementation: tools/publication/VerifyPublicationPackage.py."""
from pathlib import Path as _Path
_target = _Path(__file__).resolve().parents[1] / 'tools/publication/VerifyPublicationPackage.py'
exec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), globals())
