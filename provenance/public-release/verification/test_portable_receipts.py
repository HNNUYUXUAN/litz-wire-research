import unittest

from SanitizePublicReceipts import transform


class PortableReceiptTests(unittest.TestCase):
    def test_paths_uris_and_raw_hashes(self):
        value = {"path": "C:\\Users\\name\\acceptance root\\file.txt", "base": "C:/Python312/python.exe",
                 "url": "file:///C:/Users/name/acceptance%20root/source%20checkout",
                 "remote": "https://github.com/owner/repo/releases/download/v1/file.zip", "sha256": "0" * 64,
                 "status": "passed", "bytes": 874, "other": "C:/Users/name/acceptance root unrelated/file.txt"}
        result = transform(value, [("C:/Users/name/acceptance root", "${ACCEPTANCE_ROOT}"),
                                   ("C:/Python312", "${PYTHON_BASE}")])
        self.assertEqual(result["path"], "${ACCEPTANCE_ROOT}/file.txt")
        self.assertEqual(result["url"], "file://${ACCEPTANCE_ROOT}/source%20checkout")
        self.assertEqual(result["base"], "${PYTHON_BASE}/python.exe")
        for key in ("remote", "sha256", "status", "bytes", "other"):
            self.assertEqual(result[key], value[key])


if __name__ == "__main__":
    unittest.main()
