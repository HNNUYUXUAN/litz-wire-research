"""Stream public release downloads without credentials and save full-body receipts.

Default scope is the registered evidence, publication and supplemental assets.
--all-assets includes every API asset of the required releases. No local cache
can satisfy a download check. Metadata comes from the supplied offline snapshot.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.request
from urllib.parse import unquote, urlsplit

CATALOG = "data/catalog.json"
PUBLICATIONS = "provenance/editorial/online-assets.json"
SUPPLEMENTAL = "provenance/maintenance/supplemental-assets.json"
CHUNK_BYTES = 1024 * 1024


class DownloadFailure(Exception):
    def __init__(self, code, **details):
        super().__init__(code)
        self.code, self.details = code, details


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw.decode("utf-8-sig")), {
        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "hash_basis": "raw-bytes"}


def sha256_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def flatten(releases):
    require(isinstance(releases, list), "Snapshot releases must be a list")
    if releases and all(isinstance(page, list) for page in releases):
        releases = [release for page in releases for release in page]
    require(all(isinstance(release, dict) for release in releases), "Invalid release page shape")
    return releases


def selected_assets(root, snapshot, all_assets=False):
    """Validate every advertised identity before any HTTP request is possible."""
    inputs = []
    catalog, identity = read_json(Path(root) / CATALOG)
    inputs.append({"path": CATALOG, **identity})
    publications, identity = read_json(Path(root) / PUBLICATIONS)
    inputs.append({"path": PUBLICATIONS, **identity})
    supplemental = None
    if (Path(root) / SUPPLEMENTAL).is_file():
        supplemental, identity = read_json(Path(root) / SUPPLEMENTAL)
        inputs.append({"path": SUPPLEMENTAL, **identity})
    repository = catalog["repository"]
    require(snapshot.get("schema_version") == 1, "Snapshot schema_version must be 1")
    require(isinstance(snapshot.get("captured_at"), str), "Snapshot captured_at is required")
    captured = datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00"))
    require(captured.tzinfo is not None, "Snapshot captured_at must include a time zone")
    require(snapshot["repository"].get("full_name") == repository, "Repository identity mismatch")
    require(snapshot["repository"].get("private") is False, "Repository is not public in the supplied snapshot")
    require(catalog.get("private") is False, "Data catalog still requests authenticated downloads")
    expected = {}

    def register(tag, item, asset_id=None):
        key = (tag, item["name"])
        require(key not in expected, "Duplicate registered asset name")
        expected[key] = {"sha256": item["sha256"], "bytes": item["bytes"], "asset_id": asset_id}

    for dataset in catalog["datasets"].values():
        for part in dataset["parts"]:
            match = re.fullmatch(r"https://api\.github\.com/repos/" + re.escape(repository)
                                 + r"/releases/assets/([1-9][0-9]*)", part.get("url", ""))
            require(match is not None, "Data part has an invalid API asset URL")
            register(dataset.get("source_version", catalog["tag"]), part, int(match[1]))
    for manifest in [publications] + ([supplemental] if supplemental is not None else []):
        for item in manifest["artifacts"]:
            register(manifest["release_tag"], item)
    require(expected, "No assets are registered")
    required_tags = sorted({tag for tag, _ in expected})
    releases = flatten(snapshot["releases"])
    selected = []
    seen_ids = set()
    for tag in required_tags:
        matches = [release for release in releases if release.get("tag_name") == tag]
        require(len(matches) == 1, "Expected exactly one release for " + tag)
        release = matches[0]
        require(release.get("draft") is False and release.get("published_at"), "Release is not published: " + tag)
        assets = release["assets"]
        names = [asset["name"] for asset in assets]
        require(len(names) == len(set(names)), "Duplicate API asset names in " + tag)
        required_names = {name for wanted_tag, name in expected if wanted_tag == tag}
        require(required_names.issubset(names), "Registered assets are missing from " + tag)
        for asset in assets:
            name = asset["name"]
            registered = expected.get((tag, name))
            if not all_assets and registered is None:
                continue
            require(isinstance(name, str) and name not in {"", ".", ".."}
                    and not re.search(r'[\\/:*?"<>|\x00-\x1f]', name), "Unsafe asset filename")
            require(isinstance(asset.get("id"), int) and not isinstance(asset["id"], bool)
                    and asset["id"] > 0 and asset["id"] not in seen_ids, "Invalid or duplicate API asset ID")
            seen_ids.add(asset["id"])
            require(asset.get("state") == "uploaded", "Asset is not uploaded: " + name)
            require(isinstance(asset.get("size"), int) and not isinstance(asset["size"], bool)
                    and asset["size"] > 0, "Invalid API asset byte count")
            digest = asset.get("digest")
            require(isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest),
                    "API SHA256 digest missing: " + name)
            sha = digest[7:].lower()
            if registered is not None:
                require(registered["sha256"] == sha and registered["bytes"] == asset["size"],
                        "Registered bytes or SHA256 differ from API metadata: " + name)
                require(registered["asset_id"] in (None, asset["id"]), "Registered API asset ID differs: " + name)
            url = asset["browser_download_url"]
            parsed = urlsplit(url)
            require(parsed.scheme == "https" and parsed.netloc == "github.com" and not parsed.query
                    and not parsed.fragment and unquote(parsed.path) == "/" + repository + "/releases/download/" + tag + "/" + name,
                    "Invalid public browser download URL")
            selected.append({"asset_id": asset["id"], "release_tag": tag, "name": name,
                             "bytes": asset["size"], "sha256": sha, "url": url,
                             "registered": registered is not None})
    return sorted(selected, key=lambda item: (item["release_tag"], item["name"])), inputs


class AnonymousRedirect(urllib.request.HTTPRedirectHandler):
    """Allow HTTPS GitHub asset redirects while stripping credential headers."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        host = parsed.hostname or ""
        trusted = host == "github.com" or host.endswith(".githubusercontent.com") or host == "github-production-release-asset-2e65be.s3.amazonaws.com"
        if parsed.scheme != "https" or parsed.username or parsed.password or not trusted:
            raise DownloadFailure("untrusted_redirect")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            forbidden = {"authorization", "proxy-authorization", "cookie", "cookie2"}
            for name in [*redirected.headers, *redirected.unredirected_hdrs]:
                if name.casefold() in forbidden:
                    redirected.remove_header(name)
        return redirected


def anonymous_opener():
    # Explicit empty proxy configuration avoids inherited proxy credentials.
    # No auth, cookie or .netrc handler is installed.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), AnonymousRedirect())


def stream_download(asset, keep_dir=None, opener_factory=anonymous_opener, timeout=60):
    """Always issue a fresh complete GET; at most one MiB is held per stream."""
    request = urllib.request.Request(asset["url"], method="GET", headers={
        "User-Agent": "litz-anonymous-release-verifier/1", "Accept": "application/octet-stream",
        "Accept-Encoding": "identity"})
    temporary = None
    target = None
    writer = None
    observed_bytes = 0
    observed_sha = hashlib.sha256()
    try:
        if keep_dir is not None:
            keep_dir = Path(keep_dir)
            keep_dir.mkdir(parents=True, exist_ok=True)
            target = keep_dir / (str(asset["asset_id"]) + "-" + asset["name"])
            writer = tempfile.NamedTemporaryFile(prefix=".download-", suffix=".partial", dir=keep_dir, delete=False)
            temporary = Path(writer.name)
        with opener_factory().open(request, timeout=timeout) as response:
            if response.status != 200:
                raise DownloadFailure("unexpected_http_status", status=response.status)
            length = response.headers.get("Content-Length")
            if length is not None:
                if not length.isdecimal() or int(length) != asset["bytes"]:
                    raise DownloadFailure("content_length_mismatch")
            while block := response.read(CHUNK_BYTES):
                observed_bytes += len(block)
                if observed_bytes > asset["bytes"]:
                    raise DownloadFailure("body_exceeds_expected_size", bytes=observed_bytes)
                observed_sha.update(block)
                if writer is not None:
                    writer.write(block)
        if observed_bytes != asset["bytes"]:
            raise DownloadFailure("body_size_mismatch", bytes=observed_bytes)
        actual_sha = observed_sha.hexdigest()
        if actual_sha != asset["sha256"]:
            raise DownloadFailure("body_sha256_mismatch", sha256=actual_sha, bytes=observed_bytes)
        if writer is not None:
            writer.close()
            writer = None
            if target.exists():
                # Existing files never satisfy the HTTP check; compare only after
                # the new download has independently passed all byte checks.
                if target.stat().st_size != asset["bytes"] or sha256_file(target) != actual_sha:
                    raise DownloadFailure("keep_destination_has_different_bytes")
            else:
                os.replace(temporary, target)
                temporary = None
        receipt = {"asset_id": asset["asset_id"], "release_tag": asset["release_tag"],
                   "authentication": "none", "method": "GET", "scope": "full-body", "status": 200,
                   "bytes": observed_bytes, "sha256": actual_sha, "url": asset["url"], "checked_at": utc_now()}
        if target is not None:
            receipt["kept_file"] = target.name
        return receipt
    finally:
        if writer is not None:
            writer.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def verify_asset(asset, keep_dir=None, opener_factory=anonymous_opener, attempts=3):
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            receipt = stream_download(asset, keep_dir, opener_factory)
            receipt["attempt"] = attempt
            return {"receipt": receipt, "errors": errors}
        except DownloadFailure as error:
            errors.append({"attempt": attempt, "error": error.code, **error.details})
        except urllib.error.HTTPError as error:
            errors.append({"attempt": attempt, "error": "http_error", "status": error.code})
        except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException) as error:
            # Exception messages can contain signed redirect URLs. Save a safe
            # classification only, never repr(error), response URLs or headers.
            errors.append({"attempt": attempt, "error": type(error).__name__})
        if attempt < attempts:
            time.sleep(min(2 ** attempt, 8))
    return {"receipt": None, "errors": errors}


def write_snapshot(path, snapshot, snapshot_hash, inputs, assets, results, workers, scope, finished):
    receipts = [result["receipt"] for result in results.values() if result["receipt"] is not None]
    failures = [{"asset_id": asset["asset_id"], "release_tag": asset["release_tag"], "name": asset["name"],
                 "attempts": results[asset["asset_id"]]["errors"]}
                for asset in assets if asset["asset_id"] in results and results[asset["asset_id"]]["receipt"] is None]
    output = {"schema_version": 1, "captured_at": utc_now(),
              "metadata_captured_at": snapshot.get("metadata_captured_at", snapshot["captured_at"]),
              "repository": snapshot["repository"], "releases": snapshot["releases"],
              "anonymous_receipts": sorted(receipts, key=lambda row: (row["release_tag"], row["asset_id"])),
              "anonymous_verification": {"scope": scope, "workers": workers,
                  "status": ("failed" if failures else "passed") if finished else "running",
                  "selected_assets": len(assets), "registered_assets": sum(asset["registered"] for asset in assets),
                  "successful_assets": len(receipts), "completed_assets": len(results),
                  "expected_bytes": sum(asset["bytes"] for asset in assets),
                  "verified_bytes": sum(row["bytes"] for row in receipts), "failed_assets": failures,
                  "metadata_source": {"role": "provided_github_metadata_snapshot", **snapshot_hash},
                  "manifest_inputs": inputs, "credential_sources_used": [], "cache_hits": 0}}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".receipts-", suffix=".json", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write((json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return output["anonymous_verification"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", choices=range(1, 5), type=int, default=2)
    parser.add_argument("--all-assets", action="store_true", help="Download all assets of the required releases")
    parser.add_argument("--keep", action="append", default=[], metavar="ASSET_NAME", help="Retain this named asset after verification; repeat as needed")
    parser.add_argument("--keep-dir", type=Path, help="Destination for requested --keep assets")
    args = parser.parse_args(argv)
    if args.keep and args.keep_dir is None:
        parser.error("--keep requires --keep-dir")
    snapshot, snapshot_hash = read_json(args.snapshot)
    assets, inputs = selected_assets(args.root, snapshot, args.all_assets)
    keep = set(args.keep)
    require(keep.issubset({asset["name"] for asset in assets}), "A --keep asset is outside the selected scope")
    require(args.snapshot.resolve() != args.output.resolve(), "Output must preserve the input metadata snapshot")
    results = {}
    scope = "all_assets_of_required_releases" if args.all_assets else "registered_assets"
    write_snapshot(args.output, snapshot, snapshot_hash, inputs, assets, results, args.workers, scope, False)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(verify_asset, asset, args.keep_dir if asset["name"] in keep else None): asset for asset in assets}
        for future in as_completed(futures):
            asset = futures[future]
            results[asset["asset_id"]] = future.result()
            summary = write_snapshot(args.output, snapshot, snapshot_hash, inputs, assets, results, args.workers, scope, False)
            print(json.dumps({"completed": summary["completed_assets"], "selected": len(assets),
                              "asset_id": asset["asset_id"], "name": asset["name"],
                              "status": "passed" if results[asset["asset_id"]]["receipt"] else "failed"}), flush=True)
    summary = write_snapshot(args.output, snapshot, snapshot_hash, inputs, assets, results, args.workers, scope, True)
    print(json.dumps({key: summary[key] for key in ("status", "selected_assets", "successful_assets", "verified_bytes")}), flush=True)
    return int(summary["status"] != "passed")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError) as error:
        # Input/metadata errors occur before networking, so no signed URLs are included.
        print(json.dumps({"status": "input_or_output_error", "error_type": type(error).__name__}), flush=True)
        raise SystemExit(2)
