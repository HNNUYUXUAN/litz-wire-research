"""Read shared scholarly identities from the publication source manifest."""
from pathlib import Path
import json
ROOT=next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
def bank(source_manifest="manuscript/publication.json"):
    path=ROOT/source_manifest
    return json.loads(path.read_text(encoding="utf-8-sig"))
