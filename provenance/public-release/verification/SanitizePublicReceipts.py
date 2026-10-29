"""Write portable public receipt copies while preserving raw originals and hashes."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


def raw_sha(content):
    return hashlib.sha256(content).hexdigest()


def map_string(value, mappings):
    is_file_uri = value.startswith("file:")
    candidate = unquote(urlsplit(value).path).lstrip("/") if is_file_uri else value
    normalized = candidate.replace("\\", "/")
    for original, token in sorted(mappings, key=lambda item: -len(item[0])):
        prefix = original.replace("\\", "/").rstrip("/")
        if normalized.casefold() == prefix.casefold() or normalized.casefold().startswith(prefix.casefold() + "/"):
            suffix = normalized[len(prefix):]
            return "file://" + token + quote(suffix, safe="/") if is_file_uri else token + suffix
    return value


def transform(value, mappings):
    if isinstance(value, dict):
        return {key: transform(item, mappings) for key, item in value.items()}
    if isinstance(value, list):
        return [transform(item, mappings) for item in value]
    return map_string(value, mappings) if isinstance(value, str) else value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acceptance-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.acceptance_root.resolve()
    cli = json.loads((root / "cli restoration acceptance/cli-restoration-verification.json").read_text(encoding="utf-8"))
    source = json.loads((root / "source-verification.json").read_text(encoding="utf-8"))
    if source["status"] != "passed" or cli["status"] != "passed":
        raise ValueError("Only completed successful acceptance receipts may be prepared for publication")
    mappings = [(str(root), "${ACCEPTANCE_ROOT}"), (cli["python"]["base_prefix"], "${PYTHON_BASE}")]
    specs = ["source-verification.json", "cli restoration acceptance/cli-restoration-verification.json"]
    if (root / "pip-install-report.json").is_file():
        specs.append("pip-install-report.json")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for relative in specs:
        raw = (root / relative).read_bytes()
        value = transform(json.loads(raw.decode("utf-8")), mappings)
        public = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        name = Path(relative).name
        (output / name).write_bytes(public)
        records.append({"raw_relative_path": relative, "raw_sha256": raw_sha(raw), "raw_bytes": len(raw),
                        "public_path": name, "public_sha256": raw_sha(public), "public_bytes": len(public)})
    manifest = {"schema_version": 1, "source_commit": source["source_commit"],
        "source_tag": source["tag"], "receipt_status": "passed", "hash_basis": "exact raw file bytes",
        "transformation": {"kind": "recursive JSON string prefix substitution only",
            "rules": [
                {"token": "${ACCEPTANCE_ROOT}", "source": "absolute --acceptance-root path"},
                {"token": "${PYTHON_BASE}", "source": "raw CLI receipt python.base_prefix"}],
            "path_matching": "case-insensitive path prefixes; either slash convention; paths below prefix only",
            "file_uris": "decode the path for matching, substitute prefix, percent-encode the remaining URI path",
            "serialization": "UTF-8, JSON ensure_ascii=false, indent=2, final LF",
            "preserved": "all source/download/file hashes, counts, statuses, header names and public HTTPS URLs",
            "hash_references": "embedded receipt SHA-256 fields continue to identify the original raw receipts"},
        "artifacts": records,
        "scope": "Post-publication acceptance materials; verification helpers and these receipts are not asserted to be in the rc.3 source tag."}
    (output / "portable-receipts-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "receipts": len(records), "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
