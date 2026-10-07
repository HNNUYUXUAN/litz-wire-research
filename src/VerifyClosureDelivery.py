"""Consolidate actual document-host, cache, plotting and restore acceptance.

Only standard-library reads, SHA256 and a CPU cache-reader subprocess are used.
The device inventory may query nvidia-smi; no GPU computation or field solve runs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import PreManuscriptClosure as controller

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4*1024**2), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--package-run", required=True)
    parser.add_argument("--native-qa", required=True, type=Path)
    parser.add_argument("--browser-qa", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not controller.RUN_RE.fullmatch(args.run_id):
        raise ValueError("Safe unique run ID required")
    directory = ROOT / "outputs" / args.run_id
    directory.mkdir(exist_ok=False)
    sources = [Path(__file__), ROOT/"src/ReadFrozenManuscript.py", ROOT/"src/PreManuscriptClosure.py"]
    snapshot = directory/"source_snapshot"
    snapshot.mkdir()
    for source in sources:
        shutil.copy2(source, snapshot/source.name)
    write(directory/"run_manifest.json", {"started_UTC":datetime.now(timezone.utc).isoformat(),
          "sources":[{"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p)} for p in sources],
          "physical_solver_executed":False,"GPU_compute_used":False})
    environment = controller.hardware()
    write(directory/"environment.json", environment)
    checks = []
    def check(name, passed, details=None):
        checks.append({"id":name,"passed":bool(passed),"details":details})
    check("user_selected_32GiB_document_host", 31*controller.GIB <= environment["RAM_bytes"] <= 33*controller.GIB
          and environment["logical_processors"] >= 8, environment)
    check("system_free_reserve_8GiB", environment["free_RAM_bytes"] >= 8*controller.GIB)
    bundle = args.bundle.resolve()
    manifest = read(bundle/"closure_manifest.json")
    index = read(bundle/"source_index.json")
    index_hash = sha(bundle/"source_index.json")
    check("63_explicit_frozen_routes", len(manifest["routes"]) == 63 and set(manifest["routes"]) == set(index["routes"]))
    check("frozen_index_unchanged", index_hash == manifest["source_index_sha256"] == sha(ROOT/"docs/总控/当前运行索引.json"))
    check("bundle_integrity_verification", read(bundle/"closure_verification.json")["execution_status"] == "passed")
    books = read(bundle/"archive_notebooks.json")
    check("14_static_notebooks", len(books["notebooks"]) == 14 and len({b["notebook"] for b in books["notebooks"]}) == 14
          and not books["failures"] and all(
          all(book[key] == 0 for key in ("input_cell_count","dynamic_box_count","button_box_count")) for book in books["notebooks"]))
    documents = ROOT/"docs/report/pre_manuscript_closure_20261005"
    built = read(documents/"build_validation.json")
    check("10_source_backed_manuscript_figures", built["failed_checks"] == 0 and built["figure_count"] == 10)
    package = ROOT/"outputs"/args.package_run
    package_result = read(package/"results.json")
    package_status = read(package/"process_status.json")
    package_controller = read(package/"delivery_controller_status.json")
    package_parameters = read(package/"parameters.json")
    check("package_uses_current_bundle_and_documents", package_parameters["bundle"] == bundle.relative_to(ROOT).as_posix()
          and package_parameters["documents"] == documents.relative_to(ROOT).as_posix())
    check("actual_package_process_exit", package_status["process_exit_code"] == 0
          and package_status.get("monitor_exit_code") in (None, 0)
          and package_controller["controller_exit_code"] == 0 and not package_controller["source_changed_during_execution"])
    package_tests = read(package/"test_report.json")
    required_package_checks = {"private_members_all_SHA256", "manuscript_members_all_SHA256",
                               "space_path_restored_cache_reader", "space_path_ten_frozen_data_figures",
                               "restored_chart_CSV_SHA256", "LFS_entities_not_pointers"}
    check("all_package_restore_checks", package_tests["execution_status"] == "passed"
          and len(package_tests["checks"]) == 6 and {item["id"] for item in package_tests["checks"]} == required_package_checks
          and all(item["passed"] for item in package_tests["checks"]))
    archive_checks = []
    for archive in package_result["archives"]:
        path = (ROOT/archive["path"]).resolve()
        exists = path.is_relative_to(package.resolve()) and path.is_file()
        passed = exists and path.stat().st_size == archive["bytes"] and sha(path) == archive["sha256"]
        archive_checks.append({"path":archive["path"], "passed":passed})
    check("two_archives_current_bytes_and_SHA256", len(archive_checks) == 2 and all(x["passed"] for x in archive_checks), archive_checks)
    check("space_path_ten_chart_rebuild", package_result["restored_replot_actual_exit_code"] == 0
          and package_result["restored_replot_figure_count"] == 10 and package_result["restored_chart_CSV_SHA256"] == "passed")
    native = read(args.native_qa.resolve())
    browser = read(args.browser_qa.resolve())
    native_folder = args.native_qa.resolve().parent
    native_before = read(native_folder/"before_inputs.json")
    book_by_path = {item["notebook"]:item for item in books["notebooks"]}
    native_rows = native["notebooks"]
    native_bound = (native_before["bundle"] == bundle.relative_to(ROOT).as_posix()
                    and native_before["archive_manifest_sha256"] == sha(bundle/"archive_notebooks.json")
                    and native_before["closure_manifest_sha256"] == sha(bundle/"closure_manifest.json")
                    and native["actual_native_render_count"] == native["actual_visual_review_passed_count"] == 14
                    and len(native_rows) == 14 and {row["notebook"] for row in native_rows} == set(book_by_path))
    if native_bound:
        for row in native_rows:
            book = book_by_path[row["notebook"]]
            native_bound = native_bound and row["execution_status"] == "passed" and (
                row["archive_source_sha256_before"] == row["archive_source_sha256_after"]
                == book["notebook_sha256"] == sha(bundle/row["notebook"]))
            native_bound = native_bound and sha(native_folder/row["png_path"]) == row["png_sha256"]
    browser_before = read(args.browser_qa.resolve().parent/"run_manifest.json")
    expected_html_paths = {(bundle.relative_to(ROOT)/book["html"]).as_posix() for book in books["notebooks"]}
    browser_source_paths = {row["path"] for row in browser_before["sources"]}
    browser_bound = (browser["bundle"] == bundle.relative_to(ROOT).as_posix() and browser["page_count"] == 14
                     and browser["unique_figure_count"] == 10 and expected_html_paths <= browser_source_paths)
    for row in browser_before["sources"]:
        path = (ROOT/row["path"]).resolve()
        browser_bound = browser_bound and path.is_relative_to(bundle) and path.is_file() and sha(path) == row["sha256"]
    evidence_paths = [args.native_qa.resolve(), args.browser_qa.resolve(), bundle/"closure_manifest.json",
                      bundle/"archive_notebooks.json", bundle/"closure_verification.json", package/"results.json",
                      package/"parameters.json", package/"process_status.json", documents/"build_validation.json",
                      native_folder/"before_inputs.json", args.browser_qa.resolve().parent/"run_manifest.json"]
    write(directory/"evidence_inputs.json", [{"path":str(path), "sha256":sha(path)} for path in evidence_paths])
    check("final_native_reading_QA", native["execution_status"] == "passed" and native_bound, str(args.native_qa))
    check("final_static_browser_QA", browser["execution_status"] == "passed" and browser_bound, str(args.browser_qa))
    selection = read(ROOT/"outputs/closure_20261005_compute_pin_01/selection.json")
    check("43_finite_science_task_states", len(selection["task_finalizations"]) == 43)
    child_env = os.environ.copy()
    child_env.update({"PATH":"","CUDA_VISIBLE_DEVICES":"","OMP_NUM_THREADS":"8","MKL_NUM_THREADS":"8",
                      "OPENBLAS_NUM_THREADS":"8","PYTHONIOENCODING":"utf-8"})
    command = [sys.executable,"-B",str(ROOT/"src/ReadFrozenManuscript.py"),"--bundle",str(bundle),
               "--output",str(directory/"cache_readback.json")]
    child = subprocess.run(command, env=child_env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    (directory/"cache_reader.log").write_text(child.stdout+child.stderr, encoding="utf-8")
    write(directory/"cache_reader_process_status.json", {"process_exit_code":child.returncode,"command":command,
          "PATH":"","CUDA_VISIBLE_DEVICES":"","CPU_thread_cap":8})
    check("actual_no_NVIDIA_dependency_cache_entry", child.returncode == 0)
    failed = [item for item in checks if not item["passed"]]
    write(directory/"test_report.json", {"execution_status":"failed" if failed else "passed","checks":checks})
    write(directory/"results.json", {"run_id":args.run_id,"execution_status":"failed" if failed else "passed",
          "source_model":"user_selected_document_host_and_frozen_delivery_acceptance",
          "physical_acceptance_status":"not_applicable_document_and_archive_acceptance",
          "physical_solver_executed":False,"GPU_compute_used":False,"CPU_thread_cap":8,
          "actual_environment":environment,"bundle":bundle.relative_to(ROOT).as_posix(),"package_run":args.package_run,
          "frozen_index_sha256":index_hash,"science_task_count":43,"route_count":63,"notebook_count":14,"figure_count":10,
          "strict_8logical_noGPU_hardware_acceptance":"superseded_by_user_selected_current_delivery_host",
          "failed_checks":failed,"model_boundaries":"See manuscript acceptance matrix; physical failures remain failed."})
    print(json.dumps({"run_id":args.run_id,"execution_status":"failed" if failed else "passed","failed_checks":len(failed)}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
