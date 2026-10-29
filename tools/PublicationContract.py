"""Validate the portable LaTeX and generated-reading publication contract."""
import hashlib
from pathlib import Path
import re

EXPECTED_IDS = {f"{work}_{lang}" for work in ("report", "paper", "automation")
                for lang in ("en", "zh-CN")}


def validate_current_edition(root: Path, index: dict) -> list[str]:
    errors = []
    root = root.resolve()
    if index.get("schema_version") != 3:
        errors.append("current-edition schema_version must be 3")
    documents = index.get("documents", [])
    if not isinstance(documents, list):
        return errors + ["documents must be a list"]
    ids = [row.get("id") for row in documents if isinstance(row, dict)]
    if len(ids) != 6 or set(ids) != EXPECTED_IDS:
        errors.append("current-edition must contain six unique bilingual document IDs")
    if not index.get("run_id") or index.get("source_edition") != index.get("run_id"):
        errors.append("current-edition run_id and source_edition must agree")

    def check_file(relative, digest, label):
        if (not isinstance(relative, str) or not relative or "\\" in relative
                or Path(relative).is_absolute() or re.match(r"^[A-Za-z]:", relative)):
            errors.append(f"{label} must be a file inside the checkout")
            return
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f"{label} must be a file inside the checkout")
            return
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"{label}: SHA256 required")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"{label}: SHA256 differs from the verified build")

    check_file(index.get("source_manifest"), index.get("source_manifest_sha256"), "Source manifest")
    for doc in documents:
        if not isinstance(doc, dict):
            errors.append("Each document must be an object")
            continue
        identity = doc.get("id", "unknown")
        if identity != f"{doc.get('edition')}_{doc.get('language')}":
            errors.append(f"{identity}: edition/language identity mismatch")
        expected_layout = "single" if doc.get("edition") == "report" else "ieee-journal"
        if doc.get("layout") != expected_layout:
            errors.append(f"{identity}: expected layout {expected_layout}")
        check_file(doc.get("main"), doc.get("main_sha256"), f"{identity}: LaTeX main")
        check_file(doc.get("markdown"), doc.get("markdown_sha256"), f"{identity}: Markdown")
        sections, inputs = doc.get("sections"), doc.get("input_hashes")
        if not isinstance(sections, dict) or not sections:
            errors.append(f"{identity}: section hashes required")
            sections = {}
        if not isinstance(inputs, dict) or not inputs:
            errors.append(f"{identity}: complete input hashes required")
            inputs = {}
        for relative, digest in inputs.items():
            check_file(relative, digest, f"{identity}: input {relative}")
        expected = {doc.get("main"): doc.get("main_sha256"), **sections}
        for relative, digest in expected.items():
            if inputs.get(relative) != digest:
                errors.append(f"{identity}: source missing or inconsistent in input hashes: {relative}")
        if any(not isinstance(p, str) or not p.endswith(".tex") for p in sections):
            errors.append(f"{identity}: sections must be LaTeX files")
    return errors
