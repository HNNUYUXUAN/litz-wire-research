"""Offline release metadata must not be mistaken for public artifact downloads."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("release_audit", Path(__file__).resolve().parents[1] / "tools/CheckReleaseReadiness.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
REPO = "owner/research"
URL = "https://api.github.com/repos/" + REPO + "/releases/assets/"


def fixture():
    catalog = {"repository": REPO, "tag": "rc1", "private": True,
               "datasets": {"analytic": {"parts": [{"name": "evidence.part01", "bytes": 12,
                    "sha256": "a" * 64, "url": URL + "1"}]}}}
    publications = {"release_tag": "rc2", "artifacts": [{"name": "paper.pdf", "bytes": 34, "sha256": "b" * 64}]}
    releases = []
    for number, tag, name, size, char in [(1, "rc1", "evidence.part01", 12, "a"), (2, "rc2", "paper.pdf", 34, "b")]:
        releases.append({"tag_name": tag, "draft": True, "published_at": None,
                         "assets": [{"id": number, "name": name, "size": size, "digest": "sha256:" + char * 64,
                                     "state": "uploaded", "url": URL + str(number),
                                     "browser_download_url": "https://github.com/" + REPO + "/releases/download/" + tag + "/" + name}]})
    snapshot = {"schema_version": 1, "captured_at": "2026-10-20T13:00:00+08:00",
                "repository": {"full_name": REPO, "private": True}, "releases": releases}
    return catalog, publications, snapshot


class ReleaseReadinessTest(unittest.TestCase):
    def test_private_draft_is_valid_preparation_but_not_publication(self):
        report = AUDIT.audit(*fixture())
        self.assertEqual(report["local_preparation_checks"]["status"], "passed")
        self.assertEqual(len(report["pending_publication_conditions"]), 5)
        self.assertEqual(report["network_requests_performed"], 0)
        self.assertNotIn("public_ready", report)

    def test_wrong_sha_missing_asset_and_wrong_api_id_fail(self):
        for change, error in [("sha", "sha256_mismatch"), ("missing", "asset_missing"), ("id", "asset_id_mismatch")]:
            with self.subTest(change=change):
                catalog, publications, snapshot = fixture()
                asset = snapshot["releases"][0]["assets"][0]
                if change == "sha": asset["digest"] = "sha256:" + "f" * 64
                if change == "missing": snapshot["releases"][0]["assets"] = []
                if change == "id": asset["id"] = 999
                report = AUDIT.audit(catalog, publications, snapshot)
                self.assertEqual(report["local_preparation_checks"]["status"], "failed")
                self.assertIn(error, report["assets"][0]["errors"])

    def test_wrong_size_and_missing_api_digest_fail(self):
        catalog, publications, snapshot = fixture()
        snapshot["releases"][1]["assets"][0].update(size=35, digest=None)
        report = AUDIT.audit(catalog, publications, snapshot)
        self.assertEqual(report["assets"][1]["errors"], ["size_mismatch", "api_sha256_missing"])

    def test_slurped_pages_have_the_same_result(self):
        catalog, publications, snapshot = fixture()
        flat = AUDIT.audit(catalog, publications, snapshot)
        snapshot["releases"] = [[release] for release in snapshot["releases"]]
        self.assertEqual(flat, AUDIT.audit(catalog, publications, snapshot))

    def test_public_metadata_still_requires_anonymous_readbacks(self):
        catalog, publications, snapshot = fixture()
        catalog["private"] = snapshot["repository"]["private"] = False
        for release in snapshot["releases"]:
            release.update(draft=False, published_at="2026-10-20T01:00:00Z")
        report = AUDIT.audit(catalog, publications, snapshot)
        self.assertEqual(report["pending_publication_conditions"], ["anonymous_asset_readback"])

    def test_receipts_require_anonymous_full_body_identity(self):
        catalog, publications, snapshot = fixture()
        snapshot["anonymous_receipts"] = []
        for release in snapshot["releases"]:
            asset = release["assets"][0]
            snapshot["anonymous_receipts"].append({"asset_id": asset["id"], "release_tag": release["tag_name"],
                "authentication": "none", "method": "GET", "scope": "full-body", "status": 200,
                "bytes": asset["size"], "sha256": asset["digest"][7:], "url": asset["browser_download_url"],
                "checked_at": "2026-10-20T12:00:00+08:00"})
        valid = AUDIT.audit(catalog, publications, snapshot)
        self.assertNotIn("anonymous_asset_readback", valid["pending_publication_conditions"])
        snapshot["anonymous_receipts"][0]["authentication"] = "token"
        invalid = AUDIT.audit(catalog, publications, snapshot)
        self.assertIn("anonymous_asset_readback", invalid["pending_publication_conditions"])
        self.assertEqual(invalid["anonymous_readback"]["records"][0]["status"], "failed")

    def test_registered_supplemental_asset_missing_fails(self):
        catalog, publications, snapshot = fixture()
        supplemental = {"release_tag": "rc2", "release_url": "https://github.com/" + REPO + "/releases",
                        "artifacts": [{"name": "licenses.zip", "bytes": 56, "sha256": "c" * 64}]}
        report = AUDIT.audit(catalog, publications, snapshot, supplemental)
        self.assertEqual(report["local_preparation_checks"]["status"], "failed")
        row = next(row for row in report["assets"] if row["expected"]["kind"] == "supplemental")
        self.assertEqual(row["errors"], ["asset_missing"])
        self.assertEqual(report["counts"]["publication_assets"], 1)
        self.assertEqual(report["counts"]["supplemental_assets"], 1)

    def test_matching_supplemental_asset_passes_and_requires_readback(self):
        catalog, publications, snapshot = fixture()
        supplemental = {"release_tag": "rc2", "release_url": "https://github.com/" + REPO + "/releases",
                        "artifacts": [{"name": "licenses.zip", "bytes": 56, "sha256": "c" * 64}]}
        snapshot["releases"][1]["assets"].append({"id": 3, "name": "licenses.zip", "size": 56,
            "digest": "sha256:" + "c" * 64, "state": "uploaded", "url": URL + "3",
            "browser_download_url": "https://github.com/" + REPO + "/releases/download/rc2/licenses.zip"})
        report = AUDIT.audit(catalog, publications, snapshot, supplemental)
        self.assertEqual(report["local_preparation_checks"]["status"], "passed")
        self.assertEqual(report["counts"]["publication_assets"], 1)
        self.assertEqual(report["counts"]["supplemental_assets"], 1)
        receipt = next(row for row in report["anonymous_readback"]["records"] if row["asset_id"] == 3)
        self.assertEqual(receipt["status"], "pending")
        condition = next(row for row in report["publication_conditions"] if row["id"] == "anonymous_asset_readback")
        self.assertEqual(condition["expected_assets"], 3)


if __name__ == "__main__":
    unittest.main()
