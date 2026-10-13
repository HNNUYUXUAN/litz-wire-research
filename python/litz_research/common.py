"""Project locations, integrity, and bounded local execution."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def project(value=None):
    if value or os.getenv("LITZ_PROJECT"):
        candidates = [Path(value or os.environ["LITZ_PROJECT"]).resolve()]
    else:
        candidates = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[2]]
    for root in candidates:
        if ((root / "pyproject.toml").is_file() or (root / "manuscript/publication.json").is_file()) and (root / "configs/reference_parameters.json").is_file():
            return root
    raise ValueError("Select a research checkout with --project PATH or LITZ_PROJECT.")

def evidence_root(root, version=None):
    """Versioned restoration root; archive member names retain original identity."""
    c = read(Path(root) / "data/catalog.json")
    identity = version or c["tag"]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", identity):
        raise ValueError("Invalid evidence version")
    return Path(root) / "data/evidence" / identity

def evidence_path(root, relative, version=None):
    root = Path(root)
    c = read(root / "data/catalog.json")
    name=str(relative).replace('\\','/')
    matches=[(r,d.get('source_version',c['tag'])) for d in c['datasets'].values() for r in d['files'] if r['path']==name or r['path'].startswith(name.rstrip('/')+'/')]
    versions=[version] if version else list(dict.fromkeys(v for r,v in matches)) or [c['tag']]
    for identity in versions:
        mounted=safe_path(evidence_root(root,identity),relative)
        if mounted.is_file() or mounted.is_dir():
            exact=[r for r,v in matches if v==identity and r['path']==name]
            if mounted.is_file() and exact and any(sha(mounted)!=r['sha256'] for r in exact):
                raise ValueError('Frozen evidence checksum mismatch: '+str(relative))
            return mounted
    legacy = safe_path(root, relative)
    exact=[r for r,v in matches if r['path']==name and (not version or v==version)]
    if legacy.is_file() and exact and all(sha(legacy) == r["sha256"] for r in exact):
        return legacy
    raise FileNotFoundError("Missing frozen evidence: " + str(relative) + "; use litz-research data fetch <dataset>.")

def resolve_read_path(root, relative):
    path = Path(relative)
    if path.is_absolute():
        if path.exists():return path
        relative=path.relative_to(root)
    direct=safe_path(root,relative)
    return direct if direct.exists() else evidence_path(root,str(relative).replace('\\','/'))

def safe_path(root, relative):
    path = Path(relative)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", str(relative)):
        raise ValueError("Dataset paths must be relative: " + str(relative))
    resolved = (Path(root) / path).resolve()
    if not resolved.is_relative_to(Path(root).resolve()):
        raise ValueError("Dataset path leaves its destination: " + str(relative))
    return resolved

def tool(root, name):
    config = read(root / "litz.config.json") if (root / "litz.config.json").is_file() else {}
    chosen = os.getenv("LITZ_" + name.upper(), config.get("tools", {}).get(name, name))
    return shutil.which(chosen)

def constrain():
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "8"
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        if not kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), (1 << min(8, os.cpu_count() or 1)) - 1):
            raise ctypes.WinError(ctypes.get_last_error())
    elif hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])

def run_directory(root, run_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Run IDs use letters, digits, underscores and hyphens.")
    target = root / "outputs" / run_id
    target.mkdir(parents=True, exist_ok=False)
    return target
