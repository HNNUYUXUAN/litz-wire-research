"""Run the installed public CLI against fresh source and cache, with audited HTTP.

Run this helper with a clean virtual environment that has installed the verified
source checkout. The helper never installs packages or starts a physics solver.
"""
import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import urllib.request

from AnonymousHTTP import opener, safe_url
from VerifyPublicSource import validate_path


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dependency_order(catalog, selected):
    order, active = [], set()
    def visit(name):
        if name in active:
            raise ValueError("Dataset dependency cycle")
        if name in order:
            return
        if name not in catalog["datasets"]:
            raise ValueError("Unknown dependency")
        active.add(name)
        for dependency in catalog["datasets"][name].get("dependencies", []):
            visit(dependency)
        active.remove(name)
        order.append(name)
    visit(selected)
    return order


def verify_source(source, receipt):
    if (receipt.get("status") != "passed" or receipt.get("full_git_tree_match") is not True
            or Path(receipt["source_directory"]).resolve() != source):
        raise ValueError("Successful matching source verification receipt required")
    for record in receipt["git_files"]:
        validate_path(record["path"])
        path = source / record["path"]
        if (not path.is_file() or path.is_symlink() or path.stat().st_size != record["bytes"]
                or sha(path) != record["sha256"]):
            raise ValueError("Source differs from verified Git bytes")
    return len(receipt["git_files"])


def package_manifest(git_files):
    """Project package Python identities from the verified committed Git tree."""
    prefix, expected = "python/litz_research/", {}
    for record in git_files:
        path = record["path"]
        if not path.startswith(prefix) or not path.endswith(".py"):
            continue
        validate_path(path)
        name = path[len(prefix):]
        if name in expected:
            raise ValueError("Duplicate package path in verified Git manifest")
        expected[name] = {"path": name, "sha256": record["sha256"], "bytes": record["bytes"]}
    if not expected:
        raise ValueError("Verified Git manifest contains no package Python files")
    return [expected[name] for name in sorted(expected)]


def installed_package_identity(source, installed, git_files):
    expected = {record["path"]: record for record in package_manifest(git_files)}
    current = {p.relative_to(source).as_posix(): p for p in source.rglob("*.py")}
    actual = {p.relative_to(installed).as_posix(): p for p in installed.rglob("*.py")}
    if set(expected) != set(current) or set(expected) != set(actual):
        raise ValueError("Source or installed package inventory differs from verified Git manifest")
    records = []
    for name in sorted(expected):
        record = expected[name]
        for path in (current[name], actual[name]):
            if (not path.is_file() or path.is_symlink() or path.stat().st_size != record["bytes"]
                    or sha(path) != record["sha256"]):
                raise ValueError("Source or installed package bytes differ from verified Git manifest")
        records.append(record)
    return records


def require_empty_destinations(source, catalog, names, common):
    count = 0
    for name in names:
        dataset = catalog["datasets"][name]
        destination = common.evidence_root(source, dataset.get("source_version"))
        for item in dataset["files"]:
            path = common.native_path(common.safe_path(destination, item["path"]))
            if path.exists() or path.is_symlink():
                raise ValueError("Restoration requires every advertised destination file to be absent")
            count += 1
    return count


class ResponseAudit(urllib.request.BaseHandler):
    def __init__(self, records):
        self.records = records

    def http_response(self, request, response):
        self.records.append({"url": safe_url(request.full_url), "status": response.status})
        return response

    https_response = http_response


def run_cli(cli, source, cache, network_requests, network_responses, process_attempts):
    original_build = urllib.request.build_opener
    def audited_build(*_handlers):
        # A known explicit transport prevents ambient proxies, auth and cookie
        # handlers. CLI parameter parsing, download, cache and restore stay live.
        result = opener(network_requests, build=original_build)
        result.add_handler(ResponseAudit(network_responses))
        return result
    def blocked_process(*_args, **_kwargs):
        process_attempts.append({"status": "blocked"})
        raise RuntimeError("Subprocess execution is forbidden in anonymous restoration acceptance")
    def audited_urlopen(request, *args, **kwargs):
        return audited_build().open(request, *args, **kwargs)
    stdout, stderr = io.StringIO(), io.StringIO()
    arguments = ["--project", str(source), "data", "fetch", "analytic", "--cache", str(cache)]
    with patch.object(urllib.request, "build_opener", audited_build), \
            patch.object(urllib.request, "urlopen", audited_urlopen), \
            patch.object(subprocess, "run", blocked_process), \
            patch.object(subprocess, "Popen", blocked_process), \
            patch.object(os, "system", blocked_process), \
            patch.object(os, "popen", blocked_process), \
            redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = cli.main(arguments)
    return exit_code, stdout.getvalue(), len(stderr.getvalue()), arguments


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    source, directory = args.source.resolve(), args.directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    cache = directory / "empty object cache"
    cache.mkdir()
    receipt_path = directory / "cli-restoration-verification.json"
    record = {"schema_version": 1, "started_at": now(), "status": "running",
              "authentication": "none", "cache_was_empty": True, "cache_hits_before_run": 0,
              "network_requests": [], "network_responses": [], "process_attempts": [],
              "transport_policy": "explicit no-proxy urllib opener; credential headers rejected; trusted GitHub redirects",
              "execution_scope": "installed CLI data fetch analytic and recursive dependencies; file restoration"}
    def save():
        receipt_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    try:
        if sys.prefix == sys.base_prefix:
            raise ValueError("Run with the clean installed-project virtual environment")
        source_receipt_path = args.source_receipt or source.parent / "source-verification.json"
        source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
        record["source_commit"] = source_receipt["source_commit"]
        record["source_receipt_sha256"] = sha(source_receipt_path)
        record["verified_source_files"] = verify_source(source, source_receipt)
        import litz_research
        from litz_research import cli, common, data
        installed = Path(litz_research.__file__).resolve().parent
        record["installed_package"] = {"path": str(installed), "version": litz_research.__version__,
            "files": installed_package_identity(source / "python/litz_research", installed, source_receipt["git_files"])}
        record["python"] = {"version": sys.version, "executable": sys.executable,
                            "prefix": sys.prefix, "base_prefix": sys.base_prefix}
        catalog_path = source / "data/catalog.json"
        catalog = data.catalog(source)
        if catalog.get("private") is not False:
            raise ValueError("The source catalog must enable public anonymous downloads")
        names = dependency_order(catalog, "analytic")
        record["catalog_sha256"] = sha(catalog_path)
        record["datasets"] = names
        record["absent_destination_files_before_run"] = require_empty_destinations(source, catalog, names, common)
        expected_parts = []
        for name in names:
            dataset = catalog["datasets"][name]
            for part in dataset["parts"]:
                url = data.part_download_url(catalog, dataset, part)
                expected_parts.append({"dataset": name, "url": url, "name": part["name"],
                                       "bytes": part["bytes"], "sha256": part["sha256"]})
        record["expected_parts"] = expected_parts
        save()
        exit_code, output, stderr_characters, arguments = run_cli(cli, source, cache,
            record["network_requests"], record["network_responses"], record["process_attempts"])
        record.update(cli_exit_code=exit_code, cli_arguments=arguments, stderr_characters=stderr_characters)
        if exit_code != 0 or record["process_attempts"]:
            raise ValueError("Actual installed CLI failed anonymous restoration")
        # Keep only parsed success output, never an exception string containing
        # signed redirect query parameters.
        record["cli_result"] = json.loads(output)
        report = [row for name in names for row in data.verify(source, name)]
        record["restored_datasets"] = report
        if any(row["status"] != "passed" for row in report):
            raise ValueError("Restored file verification failed")
        object_sets, unique_objects = [], {}
        for name in names:
            objects = catalog["datasets"][name]["objects"]
            for item in objects:
                path = data.cached_object(cache, item["sha256"])
                if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
                    raise ValueError("Dependency cache object differs from the source catalog")
                unique_objects[item["sha256"]] = item["bytes"]
            object_sets.append({"dataset": name, "objects": len(objects),
                                "bytes": sum(item["bytes"] for item in objects), "status": "passed"})
        record["verified_object_sets"] = object_sets
        record["verified_unique_objects"] = len(unique_objects)
        record["verified_unique_object_bytes"] = sum(unique_objects.values())
        request_urls = {request["url"] for request in record["network_requests"]}
        if (not record["network_requests"] or any(part["url"] not in request_urls for part in expected_parts)
                or any(request["credential_headers"] or "range" in request["header_names"]
                       for request in record["network_requests"])):
            raise ValueError("Fresh anonymous full-body request evidence is incomplete")
        verified_parts = []
        for part in expected_parts:
            path = cache / "parts" / part["sha256"]
            if path.stat().st_size != part["bytes"] or sha(path) != part["sha256"]:
                raise ValueError("Downloaded part bytes differ from the source catalog")
            verified_parts.append(dict(part, verified=True))
        record.update(status="passed", checked_at=now(), verified_parts=verified_parts,
                      restored_file_records=sum(row["files"] for row in report))
        save()
        print(json.dumps({key: record[key] for key in ("status", "source_commit", "restored_datasets")}, ensure_ascii=False))
        return 0
    except Exception as error:
        record.update(status="failed", checked_at=now(), error_type=type(error).__name__)
        save()
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
