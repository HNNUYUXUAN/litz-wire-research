"""Validate the source checkout without downloading evidence or starting solvers.

Run after ``python -m pip install -e ".[automation]"``. Tests use small temporary
fixtures; saved scientific fields, licensed applications and fonts are not inputs.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import sys
import unittest
from unittest.mock import patch


# This explicit allowlist keeps new integration tests out of source-only CI.
TESTS = (
    "test_research_cli.ResearchTests.test_metadata_derivative_keeps_numeric_paths",
    "test_research_cli.ResearchTests.test_pack_respects_part_limit_and_restores",
    "test_research_cli.ResearchTests.test_paths_stay_in_dataset",
    "test_research_cli.ResearchTests.test_archive_parts_restore_and_member_integrity",
    "test_automation_tasks.AutomationTests.test_corrupted_mounted_evidence_is_rejected",
    "test_automation_tasks.AutomationTests.test_cancel_before_worker_prevents_solver_start",
    "test_automation_tasks.AutomationTests.test_dataset_version_controls_mount_and_automatic_readback",
    "test_automation_tasks.AutomationTests.test_tutorial_rejects_accidental_large_campaign",
    "test_automation_tasks.AutomationTests.test_restore_supports_long_windows_snapshot_paths",
    "test_automation_tasks.AutomationTests.test_parameters_must_be_actual_supported_inputs",
    "test_task_lifecycle.LifecycleTests.test_reused_parent_pid_does_not_adopt_an_older_process",
    "test_tool_experience.ToolExperienceTests.test_catalogue_entry_points_and_evidence_datasets_exist",
    "test_tool_experience.ToolExperienceTests.test_models_are_discoverable_without_solver_probes",
    "test_tool_experience.ToolExperienceTests.test_dry_run_reports_missing_sources_without_creating_outputs",
    "test_tool_experience.ToolExperienceTests.test_run_identity_is_checked_before_execution",
    "test_tool_experience.ToolExperienceTests.test_probe_reports_nonzero_exit_and_timeout",
    "test_tool_experience.ToolExperienceTests.test_ansys_student_executable_is_discovered_from_environment_root",
    "test_tool_experience.ToolExperienceTests.test_doctor_preserves_existing_fields_and_observation_scope",
    "test_tool_experience.ToolExperienceTests.test_json_output_uses_utf8_in_a_legacy_encoded_console",
    "test_research_manifest.ReleaseManifestTests.test_current_publication_documents_and_download_identities",
    "test_research_manifest.ReleaseManifestTests.test_catalogue_provenance_and_dependency_coverage",
    "test_source_checkout.CurrentEditionContractTests.test_complete_bilingual_set_is_accepted",
    "test_source_checkout.CurrentEditionContractTests.test_missing_or_duplicate_language_is_rejected",
    "test_source_checkout.CurrentEditionContractTests.test_missing_pdf_layout_or_hash_is_rejected",
    "test_source_checkout.CurrentEditionContractTests.test_markdown_cannot_leave_checkout",
)

LAYOUTS = {"single", "ieee-journal", "ieee-conference"}
EXPECTED_IDS = {f"{work}_{lang}" for work in ("report", "paper", "automation")
                for lang in ("en", "zh-CN")}


def validate_current_edition(root: Path, index: dict) -> list[str]:
    """Check publication identities using only the committed reading sources."""
    errors = []
    if index.get("schema_version") != 2:
        errors.append("current-edition schema_version must be 2")
    documents = index.get("documents", [])
    ids = [document.get("id") for document in documents]
    if len(ids) != 6 or set(ids) != EXPECTED_IDS:
        errors.append("current-edition must contain six unique bilingual document IDs")
    run_id = index.get("run_id")
    if not run_id or index.get("source_edition") != run_id:
        errors.append("current-edition run_id and source_edition must agree")
    root = root.resolve()
    asset_names = []
    for document in documents:
        identity = document.get("id", "unknown")
        if identity != f"{document.get('edition')}_{document.get('language')}":
            errors.append(f"{identity}: edition/language identity mismatch")
        markdown = document.get("markdown", "")
        path = (root / markdown).resolve()
        if (not markdown or Path(markdown).is_absolute()
                or not path.is_relative_to(root) or not path.is_file()):
            errors.append(f"{identity}: Markdown must be a file inside the checkout")
        pdfs = document.get("pdfs", {})
        if set(pdfs) != LAYOUTS:
            errors.append(f"{identity}: all three PDF layouts are required")
        assets = [("notebook", document.get("notebook", {}))] + list(pdfs.items())
        for kind, asset in assets:
            if not isinstance(asset, dict):
                errors.append(f"{identity}/{kind}: an asset record is required")
                continue
            local = asset.get("local_path", "")
            if (not local or Path(local).is_absolute() or re.match(r"^[A-Za-z]:", local)
                    or not (root / local).resolve().is_relative_to(root)):
                errors.append(f"{identity}/{kind}: local_path must remain inside the checkout")
            name = asset.get("asset_name", "")
            suffix = ".nb" if kind == "notebook" else ".pdf"
            if not name or "/" in name or "\\" in name or not name.endswith(suffix):
                errors.append(f"{identity}/{kind}: valid release asset name required")
            if not re.fullmatch(r"[0-9a-f]{64}", asset.get("sha256", "")):
                errors.append(f"{identity}/{kind}: SHA256 required")
            asset_names.append(name)
    if len(asset_names) != len(set(asset_names)):
        errors.append("current-edition release asset names must be unique")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Optional JSON receipt path")
    args = parser.parse_args(argv)
    root = args.project.resolve()
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["LITZ_PROJECT"] = str(root)
    sys.path[:0] = [str(root / "tests"), str(root / "tools")]
    os.chdir(root)
    system_name = "Windows" if os.name == "nt" else os.uname().sysname

    # Fail closed if a selected test ever grows an execution or network path.
    attempts = []
    def audit(event, values):
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempts.append(event)
            raise RuntimeError("Source-only validation prohibits " + event)
    sys.addaudithook(audit)

    from litz_research import __version__
    from litz_research import analytical, cli, references
    solver_attempts = []
    def reject_solve(*args, **kwargs):
        solver_attempts.append("analytical.solve")
        raise RuntimeError("Source-only validation prohibits physical solves")

    failures = []
    with ExitStack() as stack:
        # platform.system() may launch `ver` on Windows; the OS name is already
        # available without that subprocess and no version probe is needed here.
        stack.enter_context(patch.object(platform, "system", return_value=system_name))
        stack.enter_context(patch.object(analytical, "solve", reject_solve))
        suite = unittest.defaultTestLoader.loadTestsFromNames(TESTS)
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        reference_report = references.verify(root)
        if reference_report["failed_checks"]:
            failures.append("reference_validation")
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli.main(["--project", str(root), "models", "--json"])
        model_rows = json.loads(output.getvalue())
        if code or not model_rows or not all(row["source_available"] for row in model_rows):
            failures.append("cli_model_discovery")
    if not result.wasSuccessful():
        failures.append("unit_tests")
    if result.skipped or result.testsRun != len(TESTS):
        failures.append("incomplete_test_selection")
    if attempts or solver_attempts:
        failures.append("source_only_boundary")
    receipt = {
        "schema_version": 1,
        "scope": "source_checkout_only",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failures else "failed",
        "python": platform.python_version(),
        "platform": system_name,
        "package_version": __version__,
        "tests": {"selected": list(TESTS), "run": result.testsRun,
                  "failures": len(result.failures), "errors": len(result.errors),
                  "skipped": len(result.skipped)},
        "references": reference_report,
        "discovered_models": [row["id"] for row in model_rows],
        "physical_solver_calls": 0,
        "blocked_solver_attempts": solver_attempts,
        "blocked_external_operations": attempts,
        "input_sha256": {
            path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in ["pyproject.toml", "docs/current-edition.json", "data/catalog.json",
                         "references/library.bib", "references/sources.json"]
        },
        "failed_checks": failures,
    }
    text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        destination = args.output.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    print(text, end="")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
