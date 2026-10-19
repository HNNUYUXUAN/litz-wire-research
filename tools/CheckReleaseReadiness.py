"""Audit registered release assets against an offline GitHub metadata snapshot.

No network, credentials, solver or download is used. Exit 0 means local manifest
and API metadata checks passed; publication conditions are reported separately.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

CATALOG = "data/catalog.json"
PUBLICATIONS = "provenance/editorial/online-assets.json"
SUPPLEMENTAL = "provenance/maintenance/supplemental-assets.json"
HEX = re.compile(r"[0-9a-f]{64}")


def read(path):
    content = Path(path).read_bytes()
    return json.loads(content.decode("utf-8-sig")), {
        "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
        "hash_basis": "raw-bytes"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def asset_id(url, repository):
    match = re.fullmatch(r"https://api\.github\.com/repos/" + re.escape(repository)
                         + r"/releases/assets/([1-9][0-9]*)", url or "")
    return int(match[1]) if match else None


def digest(value):
    if isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-fA-F]{64}", value):
        return value[7:].lower()
    return None


def audit(catalog, publications, snapshot, supplemental=None):
    require(snapshot.get("schema_version") == 1, "snapshot.schema_version must be 1")
    require(isinstance(snapshot.get("captured_at"), str), "snapshot.captured_at is required")
    captured = datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00"))
    require(captured.tzinfo is not None, "snapshot.captured_at must include a time zone")
    repository = catalog["repository"]
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "Invalid repository identity")
    remote = snapshot["repository"]
    require(isinstance(remote, dict), "snapshot.repository must be a GitHub repository object")
    releases = snapshot["releases"]
    require(isinstance(releases, list), "snapshot.releases must be a list")
    if releases and all(isinstance(page, list) for page in releases):
        releases = [release for page in releases for release in page]
    require(all(isinstance(release, dict) for release in releases), "Invalid releases page shape")
    require(isinstance(catalog.get("private"), bool), "data catalog private must be boolean")
    require(isinstance(remote.get("private"), bool), "repository private must be boolean")
    require(publications.get("artifacts"), "No publication assets are registered")
    require(catalog.get("datasets"), "No evidence datasets are registered")
    checks = []

    def check(identifier, passed, **details):
        checks.append({"id": identifier, "status": "passed" if passed else "failed", **details})

    check("repository_identity", remote.get("full_name") == repository,
          expected=repository, observed=remote.get("full_name"))
    expected = []
    for dataset_name, dataset in sorted(catalog["datasets"].items()):
        require(dataset.get("parts"), "Dataset has no parts: " + dataset_name)
        tag = dataset.get("source_version", catalog["tag"])
        for part in dataset["parts"]:
            identity = asset_id(part.get("url"), repository)
            check("part_api_url/" + dataset_name + "/" + part["name"], identity is not None)
            expected.append({"kind": "evidence_part", "dataset": dataset_name, "tag": tag,
                             "name": part["name"], "bytes": part["bytes"],
                             "sha256": part["sha256"], "asset_id": identity})
    for item in publications["artifacts"]:
        expected.append({"kind": "publication", "tag": publications["release_tag"],
                         "name": item["name"], "bytes": item["bytes"],
                         "sha256": item["sha256"], "asset_id": None})
    if supplemental is not None:
        require(isinstance(supplemental, dict) and isinstance(supplemental.get("artifacts"), list),
                "Supplemental manifest must contain an artifacts list")
        require(isinstance(supplemental.get("release_tag"), str) and supplemental["release_tag"],
                "Supplemental manifest release_tag is required")
        for item in supplemental["artifacts"]:
            expected.append({"kind": "supplemental", "tag": supplemental["release_tag"],
                             "name": item["name"], "bytes": item["bytes"],
                             "sha256": item["sha256"], "asset_id": None})
    for item in expected:
        require(isinstance(item["name"], str) and item["name"] and "/" not in item["name"]
                and "\\" not in item["name"], "Invalid asset name")
        require(isinstance(item["bytes"], int) and not isinstance(item["bytes"], bool)
                and item["bytes"] > 0, "Invalid asset byte count")
        require(isinstance(item["sha256"], str) and HEX.fullmatch(item["sha256"]), "Invalid asset SHA256")
    keys = [(item["tag"], item["name"]) for item in expected]
    check("unique_manifest_asset_names", len(keys) == len(set(keys)))
    required_tags = sorted({item["tag"] for item in expected})
    assets_checked = []
    matched = []
    conditions = [{"id": "repository_public", "status": "satisfied" if remote["private"] is False else "pending",
                   "observed_private": remote["private"]},
                  {"id": "catalog_anonymous_download_mode", "status": "satisfied" if catalog["private"] is False else "pending",
                   "observed_private": catalog["private"]}]
    for tag in required_tags:
        found = [release for release in releases if release.get("tag_name") == tag]
        check("release_identity/" + tag, len(found) == 1, matches=len(found))
        release = found[0] if len(found) == 1 else {}
        published = release.get("draft") is False and bool(release.get("published_at"))
        conditions.append({"id": "release_published/" + tag,
                           "status": "satisfied" if published else "pending",
                           "observed_draft": release.get("draft"),
                           "observed_published_at": release.get("published_at")})
        for item in (item for item in expected if item["tag"] == tag):
            candidates = [asset for asset in release.get("assets", []) if asset.get("name") == item["name"]]
            errors = []
            observed = {}
            if len(candidates) != 1:
                errors.append("asset_missing" if not candidates else "duplicate_asset_name")
            else:
                asset = candidates[0]
                observed = {key: asset.get(key) for key in ("id", "name", "size", "digest", "state")}
                if not isinstance(asset.get("id"), int) or isinstance(asset.get("id"), bool) or asset["id"] <= 0:
                    errors.append("invalid_asset_id")
                if item["asset_id"] is not None and asset.get("id") != item["asset_id"]:
                    errors.append("asset_id_mismatch")
                if asset.get("size") != item["bytes"]:
                    errors.append("size_mismatch")
                actual_digest = digest(asset.get("digest"))
                if actual_digest is None:
                    errors.append("api_sha256_missing")
                elif actual_digest != item["sha256"]:
                    errors.append("sha256_mismatch")
                if asset.get("state") != "uploaded":
                    errors.append("asset_not_uploaded")
                if asset.get("url") and asset_id(asset["url"], repository) != asset.get("id"):
                    errors.append("api_asset_url_mismatch")
                if not errors:
                    matched.append((item, asset))
            assets_checked.append({"expected": item, "observed": observed,
                                   "status": "failed" if errors else "passed", "errors": errors})
    check("all_registered_assets_match_api_metadata",
          len(assets_checked) == len(expected) and all(row["status"] == "passed" for row in assets_checked),
          expected_count=len(expected), matched_count=sum(row["status"] == "passed" for row in assets_checked))

    # Receipts are supplied evidence. This audit does not perform HTTP requests.
    receipts = snapshot.get("anonymous_receipts", [])
    require(isinstance(receipts, list), "anonymous_receipts must be a list")
    require(all(isinstance(receipt, dict) for receipt in receipts), "anonymous_receipts entries must be objects")
    anonymous = []
    for item, asset in matched:
        matches = [receipt for receipt in receipts if receipt.get("asset_id") == asset["id"]
                   and receipt.get("release_tag") == item["tag"]]
        errors = []
        if len(matches) != 1:
            errors.append("missing_receipt" if not matches else "duplicate_receipts")
        else:
            receipt = matches[0]
            if receipt.get("authentication") != "none" or receipt.get("method") != "GET" or receipt.get("scope") != "full-body":
                errors.append("not_anonymous_full_body_get")
            if receipt.get("status") != 200:
                errors.append("http_status_not_200")
            if receipt.get("sha256") != item["sha256"] or receipt.get("bytes") != item["bytes"]:
                errors.append("receipt_content_identity_mismatch")
            url = receipt.get("url", "")
            parsed = urlparse(url)
            if (not url or url != asset.get("browser_download_url") or parsed.scheme != "https"
                    or parsed.netloc != "github.com" or parsed.query or parsed.fragment
                    or not parsed.path.startswith("/" + repository + "/releases/download/")):
                errors.append("receipt_download_url_mismatch")
            try:
                checked_at = receipt.get("checked_at", "")
                if not isinstance(checked_at, str):
                    raise ValueError("Receipt timestamp is not text")
                checked = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
                if checked.tzinfo is None or checked > captured:
                    errors.append("receipt_time_invalid")
            except ValueError:
                errors.append("receipt_time_invalid")
        anonymous.append({"asset_id": asset["id"], "name": item["name"], "tag": item["tag"],
                          "status": "satisfied_by_supplied_receipt" if not errors else
                          ("pending" if errors == ["missing_receipt"] else "failed"), "errors": errors})
    complete_receipts = len(anonymous) == len(expected) and all(not row["errors"] for row in anonymous)
    receipt_failures = sum(row["status"] == "failed" for row in anonymous)
    conditions.append({"id": "anonymous_asset_readback", "status": "satisfied" if complete_receipts else ("failed" if receipt_failures else "pending"),
                       "expected_assets": len(expected), "matched_supplied_receipts": sum(not row["errors"] for row in anonymous),
                       "receipt_failures": receipt_failures})
    return {"schema_version": 1, "snapshot_captured_at": snapshot["captured_at"],
            "repository": repository, "network_requests_performed": 0,
            "asset_validation_scope": "Manifest identity versus supplied GitHub API metadata; artifact bytes were not downloaded by this audit.",
            "local_preparation_checks": {"status": "passed" if all(check["status"] == "passed" for check in checks) else "failed",
                                         "checks": checks},
            "counts": {"evidence_parts": sum(item["kind"] == "evidence_part" for item in expected),
                       "publication_assets": len(publications["artifacts"]),
                       "supplemental_assets": sum(item["kind"] == "supplemental" for item in expected),
                       "required_releases": len(required_tags)},
            "assets": assets_checked, "publication_conditions": conditions,
            "pending_publication_conditions": [condition["id"] for condition in conditions if condition["status"] != "satisfied"],
            "anonymous_readback": {"basis": "supplied receipts only", "records": anonymous}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    catalog, catalog_hash = read(args.root / CATALOG)
    publications, publications_hash = read(args.root / PUBLICATIONS)
    snapshot, snapshot_hash = read(args.snapshot)
    supplemental, supplemental_hash = (read(args.root / SUPPLEMENTAL)
                                       if (args.root / SUPPLEMENTAL).is_file() else (None, None))
    report = audit(catalog, publications, snapshot, supplemental)
    report["inputs"] = [{"path": CATALOG, **catalog_hash}, {"path": PUBLICATIONS, **publications_hash},
                        {"role": "github_api_snapshot", "name": args.snapshot.name, **snapshot_hash}]
    if supplemental_hash is not None:
        report["inputs"].append({"path": SUPPLEMENTAL, **supplemental_hash})
    content = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8", newline="\n")
        print(json.dumps({"local_preparation_checks": report["local_preparation_checks"]["status"],
                          "counts": report["counts"], "pending_publication_conditions": report["pending_publication_conditions"]}))
    else:
        print(content, end="")
    return int(report["local_preparation_checks"]["status"] != "passed")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError, OSError) as error:
        print("Release audit error: " + str(error), file=sys.stderr)
        raise SystemExit(2)
