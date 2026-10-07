"""Read shared scholarly identities from the publication source manifest."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def bank(source_manifest="manuscript/publication.json"):
    path=ROOT/source_manifest
    return json.loads(path.read_text(encoding="utf-8-sig"))
