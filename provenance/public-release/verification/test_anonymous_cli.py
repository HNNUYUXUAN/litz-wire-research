import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request
import urllib.response

from VerifyAnonymousCLI import dependency_order, installed_package_identity, require_empty_destinations, run_cli
from litz_research import cli, common, data


class AnonymousCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="anonymous cli ")
        self.root = Path(self.temp.name) / "source checkout"
        self.root.mkdir()
        (self.root / "configs").mkdir()
        (self.root / "configs/reference_parameters.json").write_text("{}")
        (self.root / "pyproject.toml").write_text("[project]\nname='example'\n")
        (self.root / "data").mkdir()
        self.cache = Path(self.temp.name) / "fresh cache"
        self.bodies, datasets = {}, {}
        for name in ["research-shared", "analytic"]:
            body = (name + " raw\r\nbytes").encode()
            digest = hashlib.sha256(body).hexdigest()
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode="w:gz") as archive:
                entry = tarfile.TarInfo("objects/" + digest)
                entry.size = len(body)
                archive.addfile(entry, io.BytesIO(body))
            packed = stream.getvalue()
            url = "https://github.com/owner/repo/releases/download/v1/" + name + ".part001"
            self.bodies[url] = packed
            datasets[name] = {"source_version": "v1", "dependencies": ["research-shared"] if name == "analytic" else [],
                "objects": [{"sha256": digest, "bytes": len(body)}],
                "files": [{"path": name + "/one.txt", "sha256": digest, "bytes": len(body)}],
                "parts": [{"name": name + ".part001", "public_url": url, "url": url,
                           "sha256": hashlib.sha256(packed).hexdigest(), "bytes": len(packed)}]}
        self.catalog = {"tag": "v1", "repository": "owner/repo", "private": False, "datasets": datasets}
        (self.root / "data/catalog.json").write_text(json.dumps(self.catalog), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self):
        bodies = self.bodies
        class FakeHTTPS(urllib.request.HTTPSHandler):
            def https_open(self, request):
                result = urllib.response.addinfourl(io.BytesIO(bodies[request.full_url]), {}, request.full_url, code=200)
                result.msg = "OK"
                return result
        original_build = urllib.request.build_opener
        def fake_build(*handlers):
            return original_build(*handlers, FakeHTTPS())
        requests, responses, attempts = [], [], []
        with patch.object(urllib.request, "build_opener", fake_build):
            result = run_cli(cli, self.root, self.cache, requests, responses, attempts)
        return result, requests, responses, attempts

    def test_real_cli_restores_dependencies_with_fresh_mock_http_streams(self):
        names = dependency_order(self.catalog, "analytic")
        self.assertEqual(names, ["research-shared", "analytic"])
        self.assertEqual(require_empty_destinations(self.root, self.catalog, names, common), 2)
        result, requests, responses, attempts = self.invoke()
        self.assertEqual(result[0], 0)
        self.assertFalse(attempts)
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(not request["credential_headers"] for request in requests))
        self.assertEqual([response["status"] for response in responses], [200, 200])
        self.assertTrue(all(data.verify(self.root, name)[0]["status"] == "passed" for name in names))
        with self.assertRaises(ValueError):
            require_empty_destinations(self.root, self.catalog, names, common)

    def test_corrupted_download_cannot_pass_actual_cli(self):
        url = next(iter(self.bodies))
        self.bodies[url] = b"corrupted"
        result, requests, _, attempts = self.invoke()
        self.assertEqual(result[0], 1)
        self.assertTrue(requests)
        self.assertFalse(attempts)
        self.assertEqual(data.verify(self.root, "analytic")[0]["status"], "failed")

    def test_private_auth_subprocess_is_blocked(self):
        attempts = []
        fake = SimpleNamespace(main=lambda _args: subprocess.run(["gh", "auth", "token"]))
        with self.assertRaises(RuntimeError):
            run_cli(fake, self.root, self.cache, [], [], attempts)
        self.assertEqual(attempts, [{"status": "blocked"}])

    def test_dependency_cycles_and_modified_installed_code_rejected(self):
        self.catalog["datasets"]["research-shared"]["dependencies"] = ["analytic"]
        with self.assertRaises(ValueError):
            dependency_order(self.catalog, "analytic")
        left, right = self.root / "left", self.root / "right"
        left.mkdir(); right.mkdir()
        (left / "a.py").write_text("a=1\n")
        (right / "a.py").write_text("a=2\n")
        raw = (left / "a.py").read_bytes()
        manifest = [{"path": "python/litz_research/a.py", "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest()}]
        with self.assertRaises(ValueError):
            installed_package_identity(left, right, manifest)

    def package_fixture(self):
        left, right = self.root / "source-package", self.root / "installed-package"
        left.mkdir(); right.mkdir()
        body = b"a=1\r\n"
        for directory in (left, right):
            (directory / "__init__.py").write_bytes(body)
        manifest = [{"path": "python/litz_research/__init__.py", "bytes": len(body),
                     "sha256": hashlib.sha256(body).hexdigest()}]
        self.assertEqual(len(installed_package_identity(left, right, manifest)), 1)
        return left, right, manifest

    def test_extra_source_python_rejected_by_git_manifest(self):
        left, right, manifest = self.package_fixture()
        (left / "unrecorded.py").write_bytes(b"extra=1\n")
        with self.assertRaises(ValueError):
            installed_package_identity(left, right, manifest)

    def test_extra_installed_python_rejected_by_git_manifest(self):
        left, right, manifest = self.package_fixture()
        (right / "unrecorded.py").write_bytes(b"extra=1\n")
        with self.assertRaises(ValueError):
            installed_package_identity(left, right, manifest)

    def test_same_extra_python_in_source_and_installation_is_rejected(self):
        left, right, manifest = self.package_fixture()
        for directory in (left, right):
            (directory / "unrecorded.py").write_bytes(b"extra=1\n")
        with self.assertRaises(ValueError):
            installed_package_identity(left, right, manifest)


if __name__ == "__main__":
    unittest.main()
