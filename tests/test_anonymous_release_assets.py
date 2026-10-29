"""All HTTP streams are mocked; these tests never download or use credentials."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

SPEC = importlib.util.spec_from_file_location("anonymous_verifier", Path(__file__).resolve().parents[1] / "tools/VerifyAnonymousReleaseAssets.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class Response(io.BytesIO):
    def __init__(self, body, status=200):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Length": str(len(body))}


class Opener:
    def __init__(self, body, status=200):
        self.body, self.status, self.requests = body, status, []

    def open(self, request, timeout):
        self.requests.append(request)
        return Response(self.body, self.status)


def asset(body=b"verified scientific bytes"):
    return {"asset_id": 1, "release_tag": "rc1", "name": "evidence.part01", "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "url": "https://github.com/owner/research/releases/download/rc1/evidence.part01", "registered": True}


class AnonymousReleaseTest(unittest.TestCase):
    def test_success_reads_full_stream_without_auth_or_range_headers(self):
        body = b"x" * (VERIFIER.CHUNK_BYTES + 17)
        opener = Opener(body)
        receipt = VERIFIER.stream_download(asset(body), opener_factory=lambda: opener)
        self.assertEqual(receipt["sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(receipt["bytes"], len(body))
        self.assertEqual(receipt["authentication"], "none")
        self.assertEqual(receipt["scope"], "full-body")
        self.assertEqual(len(opener.requests), 1)
        self.assertFalse({key.lower() for key, value in opener.requests[0].header_items()} &
                         {"authorization", "proxy-authorization", "cookie", "range"})

    def test_wrong_hash_is_retried_three_times_without_success_receipt(self):
        expected = asset(b"expected")
        opener = Opener(b"different")
        # Equal lengths ensure the body digest is independently checked.
        expected["bytes"] = len(b"different")
        with patch.object(VERIFIER.time, "sleep"):
            result = VERIFIER.verify_asset(expected, opener_factory=lambda: opener)
        self.assertIsNone(result["receipt"])
        self.assertEqual(len(opener.requests), 3)
        self.assertTrue(all(error["error"] == "body_sha256_mismatch" for error in result["errors"]))

    def test_existing_kept_file_cannot_replace_an_http_download(self):
        body = b"verified scientific bytes"
        expected = asset(body)
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "1-evidence.part01"
            saved.write_bytes(body)
            opener = Opener(body)
            VERIFIER.stream_download(expected, directory, lambda: opener)
            self.assertEqual(len(opener.requests), 1)
            self.assertEqual(saved.read_bytes(), body)
            self.assertEqual(list(Path(directory).glob("*.partial")), [])

    def test_redirect_strips_all_authentication_and_cookie_headers(self):
        request = urllib.request.Request(asset()["url"], headers={
            "Authorization": "secret", "Proxy-Authorization": "secret", "Cookie": "session=secret", "Cookie2": "secret"})
        redirect = VERIFIER.AnonymousRedirect().redirect_request(request, None, 302, "", {},
            "https://release-assets.githubusercontent.com/path?signature=DO_NOT_RECORD")
        self.assertFalse({key.lower() for key, value in redirect.header_items()} &
                         {"authorization", "proxy-authorization", "cookie", "cookie2"})
        for url in ["http://release-assets.githubusercontent.com/path", "https://untrusted.example/path"]:
            with self.assertRaises(VERIFIER.DownloadFailure):
                VERIFIER.AnonymousRedirect().redirect_request(request, None, 302, "", {}, url)

    def test_opener_has_no_proxy_credentials_or_auth_cookie_handlers(self):
        opener = VERIFIER.anonymous_opener()
        self.assertFalse(any(isinstance(handler, (urllib.request.HTTPBasicAuthHandler,
            urllib.request.HTTPDigestAuthHandler, urllib.request.HTTPCookieProcessor)) for handler in opener.handlers))
        self.assertTrue(all(not handler.proxies for handler in opener.handlers if isinstance(handler, urllib.request.ProxyHandler)))

    def test_http_errors_never_record_signed_redirect_queries(self):
        class FailedOpener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError("https://release-assets.githubusercontent.com/a?secret=TOKEN", 403, "denied", {}, None)
        with patch.object(VERIFIER.time, "sleep"):
            result = VERIFIER.verify_asset(asset(), opener_factory=FailedOpener)
        self.assertNotIn("TOKEN", json.dumps(result))
        self.assertEqual(result["errors"][0]["status"], 403)

    def test_metadata_mismatch_stops_before_downloading_and_all_assets_expands(self):
        item = asset()
        api_asset = {"id": 1, "name": item["name"], "size": item["bytes"], "digest": "sha256:" + item["sha256"],
                     "state": "uploaded", "browser_download_url": item["url"]}
        snapshot = {"schema_version": 1, "captured_at": "2026-10-20T01:00:00Z",
                    "repository": {"full_name": "owner/research", "private": False},
                    "releases": [{"tag_name": "rc1", "draft": False, "published_at": "2026-10-20T00:00:00Z",
                                  "assets": [api_asset, dict(api_asset, id=2, name="extra.txt",
                                      browser_download_url="https://github.com/owner/research/releases/download/rc1/extra.txt")]}]}
        catalog = {"repository": "owner/research", "tag": "rc1", "private": False,
                   "datasets": {"one": {"parts": [{"name": item["name"], "bytes": item["bytes"], "sha256": item["sha256"],
                       "url": "https://api.github.com/repos/owner/research/releases/assets/1"}]}}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path, data in [(VERIFIER.CATALOG, catalog), (VERIFIER.PUBLICATIONS, {"release_tag": "rc1", "artifacts": []})]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(len(VERIFIER.selected_assets(root, snapshot)[0]), 1)
            self.assertEqual(len(VERIFIER.selected_assets(root, snapshot, True)[0]), 2)
            api_asset["digest"] = "sha256:" + "f" * 64
            with self.assertRaisesRegex(ValueError, "SHA256 differ"):
                VERIFIER.selected_assets(root, snapshot)

    def test_partial_responses_do_not_produce_full_body_receipts(self):
        opener = Opener(b"verified scientific bytes", status=206)
        with self.assertRaisesRegex(VERIFIER.DownloadFailure, "unexpected_http_status"):
            VERIFIER.stream_download(asset(), opener_factory=lambda: opener)


if __name__ == "__main__":
    unittest.main()
