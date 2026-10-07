"""Focused archive-contract checks; fixture bytes are not physical solver evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ExportRetainedTopology as topology


class RetainedTopologyContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.folder = self.root / "outputs" / "supplement"
        self.bundle = self.root / "outputs" / "bundle"
        self.folder.mkdir(parents=True)
        self.bundle.mkdir(parents=True)
        (self.folder / "arrays").mkdir()
        source = self.root / "source.wxf"
        source.write_bytes(b"synthetic fixture, no WXF reader or solver")
        original = self.bundle / "data.json"
        original.write_text('{}')
        index = self.bundle / "source_index.json"
        index.write_text('{}')
        key = "data/cases/3/mesh/elements/1/connectivity"
        alias = "data/cases/3/triangles_node_ids"
        target = {"source_key": key, "alias_source_key": alias, "dimensions": [2, 3]}
        request = {"source_index_path": index.relative_to(self.root).as_posix(), "source_index_sha256": topology.digest(index), "source_payload_path": "source.wxf", "source_payload_sha256": topology.digest(source), "original_data_path": original.relative_to(self.root).as_posix(), "original_data_sha256": topology.digest(original), "targets": [target]}
        self.write("request.json", request)
        csv = self.folder / "arrays" / "case_3_mesh_connectivity.csv"
        csv.write_text("element_index_1based,node_1_ID_1based,node_2_ID_1based,node_3_ID_1based\n1,1,2,3\n2,3,4,1\n")
        checks = ["frozen_index_SHA256", "original_omission_SHA256", "original_WXF_SHA256_before_read", "original_WXF_SHA256_after_read", "frozen_index_SHA256_after_read", alias+"_identity"]
        checks += [key+suffix for suffix in ("_dimensions", "_integer_node_IDs", "_CSV_write", "_CSV_header_rows", "_CSV_indices", "_original_WXF_integer_readback")]
        self.manifest = dict(request, execution_status="passed_original_integer_topology_readback", solver_executed=False, GPU_compute_enabled=False, arrays=[{"source_key": key, "alias_source_keys": [alias], "path": "arrays/"+csv.name, "sha256": topology.digest(csv), "bytes": csv.stat().st_size, "dimensions": [2, 3], "node_count": 4, "CSV_header": ["element_index_1based", "node_1_ID_1based", "node_2_ID_1based", "node_3_ID_1based"], "roundtrip": {"passed": True, "components_compared": 6, "maximum_absolute_error": 0, "absolute_tolerance": 0, "relative_tolerance": 0, "original_WXF_anchors": [{"element_index_1based": 1, "node_IDs": [1, 2, 3]}, {"element_index_1based": 2, "node_IDs": [3, 4, 1]}]}}], checks=[{"id": check, "passed": True} for check in checks])
        self.write("topology_manifest.json", self.manifest)
        self.write("process_status.json", {"process_exit_code": 0})

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, value):
        (self.folder / name).write_text(json.dumps(value), encoding="utf-8")

    def verify(self):
        with patch.object(topology, "ROOT", self.root):
            return topology.verify(self.folder, self.bundle)

    def test_complete_contract_and_exact_integer_anchors(self):
        self.assertTrue(self.verify()["passed"])
        self.assertEqual(self.verify()["integer_components"], 6)

    def test_changed_source_or_incomplete_original_identity_is_rejected(self):
        (self.root / "source.wxf").write_bytes(b"changed source")
        self.assertFalse(self.verify()["passed"])
        self.manifest["checks"].pop()
        self.write("topology_manifest.json", self.manifest)
        self.assertIn("original-WXF direct identity and full integer readback checks incomplete", self.verify()["errors"])

    def test_numeric_tampering_even_with_new_file_hash_rejects_original_anchor(self):
        array = self.manifest["arrays"][0]
        csv = self.folder / array["path"]
        csv.write_text(csv.read_text().replace("2,3,4,1", "2,3,4,2"))
        array["sha256"] = topology.digest(csv)
        array["bytes"] = csv.stat().st_size
        self.write("topology_manifest.json", self.manifest)
        self.assertFalse(self.verify()["passed"])

    def test_failed_actual_exit_and_missing_alias_are_rejected(self):
        self.write("process_status.json", {"process_exit_code": 1})
        self.manifest["arrays"][0]["alias_source_keys"] = []
        self.write("topology_manifest.json", self.manifest)
        self.assertFalse(self.verify()["passed"])


if __name__ == "__main__":
    unittest.main()
