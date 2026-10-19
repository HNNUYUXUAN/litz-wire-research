import hashlib
import io
from pathlib import Path
import stat
import tempfile
import unittest
import urllib.request
import zipfile

from AnonymousHTTP import FORBIDDEN, Redirect, RequestAudit, opener, trusted_url
from VerifyPublicSource import extract_verified, inspect_zip


class SourceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="source verification ")
        self.root = Path(self.temp.name)
        self.body = b"raw\r\nsource\x00bytes\n"
        self.manifest = [{"path": "dir/a.txt", "bytes": len(self.body),
                          "sha256": hashlib.sha256(self.body).hexdigest()}]

    def tearDown(self):
        self.temp.cleanup()

    def archive(self, entries):
        path = self.root / "source.zip"
        with zipfile.ZipFile(path, "w") as bundle:
            for name, body in entries:
                bundle.writestr(name, body)
        return path

    def test_exact_raw_bytes_extract_and_no_overwrite(self):
        archive = self.archive([("prefix/dir/a.txt", self.body)])
        destination = self.root / "source checkout"
        self.assertEqual(extract_verified(archive, self.manifest, destination), 1)
        self.assertEqual((destination / "dir/a.txt").read_bytes(), self.body)
        with self.assertRaises(FileExistsError):
            extract_verified(archive, self.manifest, destination)

    def test_inventory_must_match_and_traversal_is_rejected(self):
        for entries in [[], [("prefix/dir/a.txt", self.body), ("prefix/extra.txt", b"x")],
                        [("prefix/../outside", b"x")]]:
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    inspect_zip(self.archive(entries), self.manifest)

    def test_same_length_wrong_digest_does_not_extract(self):
        archive = self.archive([("prefix/dir/a.txt", self.body.replace(b"raw", b"RAW"))])
        destination = self.root / "source checkout"
        with self.assertRaises(ValueError):
            extract_verified(archive, self.manifest, destination)
        self.assertFalse(destination.exists())

    def test_symlinks_and_case_collisions_rejected(self):
        link = zipfile.ZipInfo("prefix/dir/a.txt")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for entries in [[(link, self.body)], [("prefix/dir/a.txt", self.body), ("prefix/Dir/A.txt", self.body)]]:
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    inspect_zip(self.archive(entries), self.manifest)

    def test_transport_strips_redirect_credentials_and_query_logs(self):
        self.assertTrue(trusted_url("https://codeload.github.com/org/repo/zip/tag"))
        req = urllib.request.Request("https://github.com/org/repo", headers={
            "Authorization": "secret", "Proxy-Authorization": "secret", "Cookie": "secret"})
        redirected = Redirect().redirect_request(req, io.BytesIO(), 302, "redirect", {},
            "https://codeload.github.com/org/repo/zip/tag?token=secret")
        self.assertFalse(FORBIDDEN & {key.casefold() for key, _ in redirected.header_items()})
        records = []
        RequestAudit(records).https_request(redirected)
        self.assertNotIn("secret", str(records))
        with self.assertRaises(ValueError):
            RequestAudit([]).https_request(req)

    def test_explicit_proxy_handler_disables_environment_proxy(self):
        captured = []
        opener([], build=lambda *handlers: captured.extend(handlers))
        self.assertEqual(captured[0].proxies, {})
        self.assertFalse(any(isinstance(handler, (urllib.request.HTTPBasicAuthHandler,
            urllib.request.HTTPCookieProcessor)) for handler in captured))


if __name__ == "__main__":
    unittest.main()
