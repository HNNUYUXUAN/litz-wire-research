"""Exercise public/private release selection through a verified fixture archive."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import quote

from litz_research import data


class PublicDataTests(unittest.TestCase):
    repository = "example/litz-research"
    api_url = "https://api.github.com/repos/example/litz-research/releases/assets/123"
    part_name = "example data.tar.gz.part000"
    version = "v1.0.0-rc.2"

    def fixture(self, root, private=False, with_public=True, with_source_version=True):
        content = b"source_model,execution_status\nfixture,completed\n"
        digest = hashlib.sha256(content).hexdigest()
        bundle = io.BytesIO()
        with tarfile.open(fileobj=bundle, mode="w:gz") as archive:
            member = tarfile.TarInfo("objects/" + digest)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
        payload = bundle.getvalue()
        part = {"name": self.part_name, "url": self.api_url,
                "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        version = self.version if with_source_version else "v1.0.0-rc.1"
        public = ("https://github.com/" + self.repository + "/releases/download/"
                  + version + "/" + quote(self.part_name, safe=""))
        if with_public:
            part["public_url"] = public
        dataset = {"objects": [{"sha256": digest, "bytes": len(content)}],
                   "files": [{"path": "results/data.csv", "sha256": digest, "bytes": len(content)}],
                   "parts": [part]}
        if with_source_version:
            dataset["source_version"] = self.version
        catalogue = {"repository": self.repository, "tag": "v1.0.0-rc.1",
                     "private": private, "datasets": {"fixture": dataset}}
        (root / "data").mkdir()
        self.write_catalog(root, catalogue)
        return catalogue, payload, content, public, version

    @staticmethod
    def write_catalog(root, value):
        (root / "data/catalog.json").write_text(json.dumps(value), encoding="utf-8")

    @staticmethod
    def response(payload):
        response = io.BytesIO(payload)
        response.status = 200
        response.headers = {}
        return response

    def assert_restored(self, root, version, content, result):
        self.assertEqual(result[0]["status"], "passed")
        self.assertEqual((root / "data/evidence" / version / "results/data.csv").read_bytes(), content)

    def test_public_fetch_prefers_browser_url_without_authentication(self):
        with tempfile.TemporaryDirectory(prefix="Litz public data ") as tmp:
            root = Path(tmp)
            _, payload, content, public, version = self.fixture(root)
            with patch.object(data.urllib.request, "build_opener") as opener, \
                    patch.object(data.subprocess, "run", side_effect=AssertionError("Public fetch invoked gh")) as auth:
                opener.return_value.open.return_value = self.response(payload)
                result = data.fetch(root, "fixture", root / "cache")
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, public)
            self.assertIsNone(request.get_header("Authorization"))
            auth.assert_not_called()
            self.assert_restored(root, version, content, result)

    def test_public_fetch_uses_catalog_tag_without_dataset_source_version(self):
        with tempfile.TemporaryDirectory(prefix="Litz public tag ") as tmp:
            root = Path(tmp)
            _, payload, content, public, version = self.fixture(root, with_source_version=False)
            with patch.object(data.urllib.request, "build_opener") as opener, \
                    patch.object(data.subprocess, "run", side_effect=AssertionError("Public fetch invoked gh")):
                opener.return_value.open.return_value = self.response(payload)
                result = data.fetch(root, "fixture", root / "cache")
            self.assertEqual(opener.return_value.open.call_args.args[0].full_url, public)
            self.assert_restored(root, version, content, result)

    def test_public_legacy_catalog_falls_back_without_authentication(self):
        with tempfile.TemporaryDirectory(prefix="Litz legacy public data ") as tmp:
            root = Path(tmp)
            _, payload, content, _, version = self.fixture(root, with_public=False)
            with patch.object(data.urllib.request, "build_opener") as opener, \
                    patch.object(data.subprocess, "run", side_effect=AssertionError("Public fetch invoked gh")) as auth:
                opener.return_value.open.return_value = self.response(payload)
                result = data.fetch(root, "fixture", root / "cache")
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, self.api_url)
            self.assertIsNone(request.get_header("Authorization"))
            auth.assert_not_called()
            self.assert_restored(root, version, content, result)

    def test_private_fetch_uses_api_url_and_ignores_public_url(self):
        with tempfile.TemporaryDirectory(prefix="Litz private data ") as tmp:
            root = Path(tmp)
            catalogue, payload, content, _, version = self.fixture(root, private=True)
            catalogue["datasets"]["fixture"]["parts"][0]["public_url"] = "https://unrelated.invalid/ignored"
            self.write_catalog(root, catalogue)
            with patch.object(data.urllib.request, "build_opener") as opener, \
                    patch.object(data.subprocess, "run", return_value=SimpleNamespace(stdout="fixture-token\n")) as auth:
                opener.return_value.open.return_value = self.response(payload)
                result = data.fetch(root, "fixture", root / "cache")
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, self.api_url)
            self.assertEqual(request.get_header("Authorization"), "Bearer fixture-token")
            auth.assert_called_once_with(["gh", "auth", "token"], check=True, capture_output=True, text=True)
            self.assert_restored(root, version, content, result)

    def test_malformed_public_url_is_rejected_before_network_or_auth(self):
        with tempfile.TemporaryDirectory(prefix="Litz invalid public data ") as tmp:
            root = Path(tmp)
            catalogue, _, _, public, _ = self.fixture(root)
            part = catalogue["datasets"]["fixture"]["parts"][0]
            invalid = [public.replace("https:", "http:"), public.replace("github.com", "github.com.invalid"),
                       public.replace("github.com", "user:password@github.com"),
                       public.replace("github.com", "github.com:443"),
                       public.replace(self.repository, "other/repository"),
                       public.replace(self.version, "v9.9.9"), public + "?token=fixture", public + "#fragment",
                       public.replace("%20", " "), public + ".wrong", " " + public, "", None]
            for value in invalid:
                with self.subTest(url=value), \
                        patch.object(data.urllib.request, "build_opener") as opener, \
                        patch.object(data.subprocess, "run") as auth:
                    part["public_url"] = value
                    self.write_catalog(root, catalogue)
                    with self.assertRaises(ValueError):
                        data.fetch(root, "fixture", root / "cache")
                    opener.assert_not_called()
                    auth.assert_not_called()

    def test_private_authentication_rejects_untrusted_transport(self):
        with tempfile.TemporaryDirectory(prefix="Litz private host ") as tmp:
            target = Path(tmp) / "part"
            for url in [self.api_url.replace("https:", "http:"),
                        self.api_url.replace("api.github.com", "github.com"),
                        self.api_url.replace("api.github.com", "user:password@api.github.com"),
                        self.api_url.replace("api.github.com", "api.github.com:443")]:
                with self.subTest(url=url), patch.object(data.subprocess, "run") as auth, \
                        patch.object(data.urllib.request, "build_opener") as opener:
                    with self.assertRaises(ValueError):
                        data.download(url, target, "0" * 64, 1, private=True)
                    auth.assert_not_called()
                    opener.assert_not_called()

    def test_redirect_removes_credentials_across_hosts_or_https_downgrade(self):
        request = data.urllib.request.Request(self.api_url, headers={"Authorization": "Bearer fixture-token"})
        for destination in ["https://release-assets.githubusercontent.com/fixture", self.api_url.replace("https:", "http:")]:
            with self.subTest(destination=destination):
                redirected = data.CredentialRedirect().redirect_request(request, None, 302, "Found", {}, destination)
                self.assertIsNotNone(redirected)
                self.assertIsNone(redirected.get_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
