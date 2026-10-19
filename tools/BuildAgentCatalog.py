"""Build a deterministic discovery catalog from tracked Litz research records.

Only Python's standard library and Git are required. No solver, evidence download,
network request, ignored artifact or local environment configuration is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import quote

REPOSITORY = "https://github.com/HNNUYUXUAN/litz-wire-research"
ROUTES = ("analytic", "fem2", "common_terminal", "geometry", "peec", "rt0", "aphi")
LANGUAGES = ("en", "zh-CN")
CATALOG = "docs/agent-catalog.json"
SOURCES = ("configs/research_notebooks.json", "manuscript/publication.json",
           "publications/manifest.json", "automation/examples/verification.json",
           "provenance/editorial/delivery-manifest.json",
           "provenance/editorial/online-assets.json")


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


class Repository:
    def __init__(self, root):
        self.root = Path(root).resolve()
        result = subprocess.run(["git", "-c", "safe.directory=" + str(self.root),
                                 "-C", str(self.root), "ls-files", "-z"],
                                check=True, capture_output=True)
        self.tracked = set(result.stdout.decode("utf-8").split("\0")) - {""}
        self.read_paths = set()
        self.cache = {}

    def read_bytes(self, path):
        relative = PurePosixPath(path)
        if relative.is_absolute() or ".." in relative.parts or "\\" in path or ":" in path:
            raise ValueError("Expected a safe repository path: " + path)
        if path not in self.tracked:
            raise ValueError("Discovery input is not tracked: " + path)
        candidate = (self.root / path).resolve()
        if not candidate.is_relative_to(self.root):
            raise ValueError("Discovery input leaves repository: " + path)
        self.read_paths.add(path)
        if path not in self.cache:
            self.cache[path] = candidate.read_bytes()
        return self.cache[path]

    def text(self, path):
        return self.read_bytes(path).decode("utf-8-sig")

    def json(self, path):
        return json.loads(self.text(path))

    def resource(self, path):
        content = self.read_bytes(path)
        return {"path": path, "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content), "hash_basis": "raw-bytes",
                "identity_source": "tracked_worktree_bytes",
                "url": REPOSITORY + "/blob/main/" + quote(path, safe="/"),
                "raw_url": "https://raw.githubusercontent.com/HNNUYUXUAN/litz-wire-research/main/" + quote(path, safe="/")}


def heading_and_summary(text):
    title = next(line[2:].strip() for line in text.splitlines() if line.startswith("# "))
    paragraphs = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    summary = next((p.replace("\n", " ").strip() for p in paragraphs
                    if p.strip() and not p.startswith(("#", "[", "```", "|"))), "")
    return title, summary


def build(root):
    repo = Repository(root)
    inputs = {path: repo.json(path) for path in SOURCES}
    tutorials = inputs[SOURCES[0]]
    publication = inputs[SOURCES[1]]
    reading = inputs[SOURCES[2]]
    examples = inputs[SOURCES[3]]
    delivery = inputs[SOURCES[4]]
    online = inputs[SOURCES[5]]
    if reading["source_edition"] != delivery["run_id"]:
        raise ValueError("Publication previews and delivery manifest identify different runs")
    items = []
    for route in ROUTES:
        rows = [row for row in tutorials if row["route"] == route]
        by_lang = {row["language"]: row for row in rows}
        if len(rows) != 2 or set(by_lang) != set(LANGUAGES):
            raise ValueError("Expected paired tutorial registration: " + route)
        row = by_lang["en"]
        directory = "models/" + route + "/"
        paths = sorted(path for path in repo.tracked if path.startswith(directory)
                       and PurePosixPath(path).suffix in {".md", ".nb", ".json", ".wl", ".wls", ".py", ".wlt"})
        items.append({"id": "route/" + route, "kind": "route", "titles": row["titles"],
                      "summary": {lang: by_lang[lang]["usage"] for lang in LANGUAGES},
                      "model_id": row["model_id"], "reference_keys": row["references"],
                      "evidence_dataset": row["evidence_dataset"],
                      "parameter_defaults": row["parameters"],
                      "physical_conventions": row["fixed_conventions"],
                      "resources": [repo.resource(path) for path in paths],
                      "commands": {"inspect": "litz-research models " + row["model_id"],
                                   "preflight": "litz-research run " + row["model_id"] + " --case tutorial --dry-run",
                                   "restore_evidence": "litz-research data fetch " + row["evidence_dataset"]}})

    workflow_paths = sorted(path for path in repo.tracked
                            if re.fullmatch(r"automation/workflows/[^/]+/README\.md", path))
    for path in workflow_paths:
        identifier = path.split("/")[2]
        paths = {"en": path, "zh-CN": path.replace("README.md", "README.zh-CN.md")}
        texts = {lang: heading_and_summary(repo.text(p)) for lang, p in paths.items()}
        items.append({"id": "workflow/" + identifier, "kind": "workflow",
                      "titles": {lang: data[0] for lang, data in texts.items()},
                      "summary": {lang: data[1] for lang, data in texts.items()},
                      "resources": [repo.resource(p) for p in paths.values()]})

    for case in examples["cases"]:
        identifier = case["id"]
        base = "automation/examples/" + identifier + "/"
        task = repo.json(base + "task.json")
        if task["id"] != identifier:
            raise ValueError("Task identity mismatch: " + identifier)
        # Saved status values are copied verbatim; no execution is inferred here.
        runs = [{key: run[key] for key in ("run_id", "result_sha256", "execution_status",
                                          "physical_acceptance_status", "attachment_path") if key in run}
                for run in case["runs"]]
        items.append({"id": "case/" + identifier, "kind": "case",
                      "titles": {"en": task["task"]}, "summary": {"en": case["conclusion"]},
                      "recorded_harness": case["harness"], "recorded_runs": runs,
                      "status_source": SOURCES[3],
                      "resources": [repo.resource(path) for path in sorted(repo.tracked)
                                    if path.startswith(base)]})

    for edition, work in sorted(publication["edition"].items()):
        for lang in LANGUAGES:
            identifier = edition + "_" + lang
            preview = "publications/" + edition + "/" + lang + "/README.md"
            records = [record for record in reading["files"] if record["path"] == preview]
            if len(records) != 1:
                raise ValueError("Expected one publication reading record: " + preview)
            markdown = repo.resource(preview)
            if markdown["sha256"] != records[0]["sha256"]:
                raise ValueError("Publication reading bytes differ from manifest: " + preview)
            local = [dict(artifact, hash_basis="raw-bytes", identity_source=SOURCES[4])
                     for artifact in delivery["artifacts"]
                     if PurePosixPath(artifact["path"]).name == identifier + ".md"
                     or PurePosixPath(artifact["path"]).name == identifier + ".nb"
                     or re.fullmatch(re.escape(identifier) + r"_(single|ieee-journal|ieee-conference)\.pdf",
                                     PurePosixPath(artifact["path"]).name)]
            release = [dict(asset, hash_basis="raw-bytes", identity_source=SOURCES[5],
                            release_tag=online["release_tag"], release_url=online["release_url"])
                       for asset in online["artifacts"]
                       if re.fullmatch(r".+_" + re.escape(identifier) + r"(?:_(?:single|ieee-journal|ieee-conference)\.pdf|\.nb)", asset["name"])]
            if len(local) != 5 or len(release) != 4:
                raise ValueError("Expected MD/NB/three PDFs and four release assets: " + identifier)
            chapters = [chapter["sources"][lang] for chapter in work["chapters"]]
            items.append({"id": "manuscript/" + edition + "/" + lang, "kind": "manuscript",
                          "titles": {lang: work["title"][lang]}, "language": lang,
                          "run_id": delivery["run_id"], "resources": [markdown],
                          "chapter_sources": [repo.resource(path) for path in chapters],
                          "local_delivery": local, "release_assets": release})
    items.sort(key=lambda item: item["id"])
    identifiers = [item["id"] for item in items]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate discovery identities")
    counts = {kind: sum(item["kind"] == kind for item in items)
              for kind in ("route", "workflow", "case", "manuscript")}
    sources = [repo.resource(path) for path in sorted(repo.read_paths)]
    catalog = {"schema_version": 1, "repository": REPOSITORY, "source_records": list(SOURCES),
               "hash_basis": "raw-bytes", "input_resources": sources,
               "evidence_policy": "Tracked records only. Local delivery and release identities are separate recorded metadata; ignored artifacts are not opened or reverified.",
               "bibliography": "references/library.bib", "reference_usage": "references/sources.json",
               "counts": counts, "items": items}
    return catalog


def outputs(catalog):
    short = ["# Litz wire research / Litz 线研究", "",
             "> Agent-driven reviewable modeling and simulation, with bilingual research manuscripts and seven physical routes.",
             "> 智能体驱动的可复核建模与仿真，包含双语研究稿件与七条物理路线。", "",
             "- [English overview](README.md)", "- [中文首页](README.zh-CN.md)",
             "- [Research conventions](AGENTS.md)", "- [研究约定](AGENTS.zh-CN.md)",
             "- [Complete publications](publications/ONLINE.md)", "- [完整稿件](publications/ONLINE.zh-CN.md)",
             "- [Catalog interface](docs/agent-catalog.md)", "- [目录接口](docs/agent-catalog.zh-CN.md)",
             "- [Machine catalog](docs/agent-catalog.json)",
             "- [MCP and workflows](automation/README.md)", "- [MCP 与工作流](automation/README.zh-CN.md)",
             "- [Bibliography](references/library.bib)", "- [Citation guide](docs/citation-guide.md)", "",
             "Search: `python tools/BuildAgentCatalog.py --search common_terminal`.",
             "查询：`python tools/BuildAgentCatalog.py --search 解析`。", "",
             "Read the selected model conditions, saved execution status and physical acceptance separately. Cite the source path and actual commit used.",
             "分别核对模型条件、保存的执行状态与物理验收；引用时附来源路径和实际使用的提交。", ""]
    # The expanded index adds navigation only; bibliography remains single-source.
    expanded = short + ["## Indexed resources / 资源目录", ""]
    for item in catalog["items"]:
        label = " / ".join(item["titles"].values())
        expanded += ["### " + item["id"] + " — " + label, ""]
        for lang, summary in item.get("summary", {}).items():
            expanded += [lang + ": " + summary, ""]
        for resource in item["resources"]:
            if resource["path"].endswith(("README.md", "README.zh-CN.md", "task.json", "execution.json")):
                expanded += ["- [" + resource["path"] + "](" + resource["path"] + ")"]
        if item.get("recorded_runs"):
            for run in item["recorded_runs"]:
                expanded += ["- `" + run["run_id"] + "`: `" + run["execution_status"]
                             + "` / `" + run["physical_acceptance_status"] + "`"]
        expanded += [""]
    return {CATALOG: encoded(catalog), "llms.txt": "\n".join(short).encode("utf-8"),
            "llms-full.txt": "\n".join(expanded).encode("utf-8")}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, help="Write generated files here; inputs still use --root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Compare generated bytes without writing")
    mode.add_argument("--search", help="Read-only AND search across IDs, titles, summaries, commands and reference keys")
    mode.add_argument("--show", help="Read-only lookup by stable item ID")
    args = parser.parse_args(argv)
    catalog = build(args.root)
    if args.search is not None or args.show is not None:
        selected = catalog["items"]
        if args.show is not None:
            selected = [item for item in selected if item["id"] == args.show]
        else:
            terms = args.search.casefold().split()
            selected = [item for item in selected if terms and all(term in json.dumps(
                {key: value for key, value in item.items() if key not in
                 {"resources", "chapter_sources", "local_delivery", "release_assets"}},
                ensure_ascii=False).casefold() for term in terms)]
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0 if selected else 1
    destination = (args.output_dir or args.root).resolve()
    stale = []
    for relative, content in outputs(catalog).items():
        path = destination / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(json.dumps({"counts": catalog["counts"], "status": "stale" if stale else "current",
                      "stale": stale}, ensure_ascii=False))
    return int(bool(stale))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print("Catalog error: " + str(error), file=sys.stderr)
        raise SystemExit(2)
