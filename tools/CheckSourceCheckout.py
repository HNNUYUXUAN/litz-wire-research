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
    "test_readiness.ReadinessTests.test_clean_probe_does_not_inherit_accidental_terminal_dependencies",
    "test_readiness.ReadinessTests.test_missing_installation_is_not_successful_tool_execution",
    "test_readiness.ReadinessTests.test_protocol_error_flag_and_text_errors_are_preserved",
    "test_readiness.ReadinessTests.test_wolfram_test_failure_cannot_pass_as_tool_success",
    "test_readiness.ReadinessTests.test_dependency_drift_and_missing_runtime_are_rejected",
    "test_readiness.ReadinessTests.test_explicit_environment_survives_empty_parent_environment",
    "test_readiness.ReadinessTests.test_generated_configuration_keeps_verified_root_and_no_unrelated_secret",
    "test_readiness.ReadinessTests.test_executable_presence_does_not_hide_missing_desktop_environment",
    "test_readiness.ReadinessTests.test_dependency_lock_is_part_of_source_identity",
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
    "test_task_lifecycle.LifecycleTests.test_saved_solver_result_does_not_publish_completion_before_cleanup",
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
    "test_source_checkout.CurrentEditionContractTests.test_invalid_layout_or_hash_is_rejected",
    "test_source_checkout.CurrentEditionContractTests.test_markdown_cannot_leave_checkout",
)

from PublicationContract import validate_current_edition


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
