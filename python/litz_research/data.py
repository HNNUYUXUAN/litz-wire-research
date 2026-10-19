"""Resumable, hash-verified release datasets and a local object cache."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from .common import read, safe_path, sha, evidence_root,native_path

class CredentialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        follow = super().redirect_request(req, fp, code, msg, headers, newurl)
        if follow and (urllib.parse.urlparse(req.full_url).netloc != urllib.parse.urlparse(newurl).netloc
                       or urllib.parse.urlparse(newurl).scheme != "https"):
            follow.remove_header("Authorization")
        return follow

def download(url, destination, expected_hash, expected_bytes, private=False):
    """Resume a partial response; only verified bytes become cache entries."""
    destination = native_path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == expected_bytes and sha(destination) == expected_hash:
        return destination
    partial = destination.with_suffix(destination.suffix + ".partial")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > expected_bytes:
        raise ValueError("Partial download exceeds manifest length: " + destination.name)
    if offset == expected_bytes:
        if sha(partial) != expected_hash:
            raise ValueError("Partial download checksum mismatch: " + destination.name)
        partial.replace(destination); return destination
    headers = {"User-Agent":"litz-research/1.0.0rc3", "Accept":"application/octet-stream"}
    if offset: headers["Range"] = f"bytes={offset}-"
    if private:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise ValueError("Private release authentication requires HTTPS on api.github.com.")
        token = subprocess.run(["gh","auth","token"], check=True, capture_output=True, text=True).stdout.strip()
        headers["Authorization"] = "Bearer " + token
    response = urllib.request.build_opener(CredentialRedirect()).open(urllib.request.Request(url, headers=headers), timeout=90)
    with response:
        status = getattr(response, "status", 200) or 200
        if status == 206:
            content_range = response.headers.get("Content-Range", "")
            if not content_range.startswith(f"bytes {offset}-"):
                raise ValueError("Range response starts at an unexpected offset.")
            mode = "ab"
        elif status == 200:
            mode = "wb"
        else:
            raise ValueError("Unexpected download status: " + str(status))
        with partial.open(mode) as stream:
            while block := response.read(1024**2):
                stream.write(block)
                if stream.tell() > expected_bytes:
                    raise ValueError("Downloaded bytes exceed the declared length.")
    if partial.stat().st_size != expected_bytes or sha(partial) != expected_hash:
        raise ValueError("Download checksum or length mismatch: " + destination.name)
    partial.replace(destination)
    return destination

def catalog(root):
    path = root / "data/catalog.json"
    return read(path) if path.exists() else {"datasets": {}}

def part_download_url(catalogue, dataset, part):
    """Select authenticated API or validated public release attachment URLs."""
    if not catalogue.get("private", True) and "public_url" in part:
        repository = catalogue.get("repository", "")
        version = dataset.get("source_version") or catalogue.get("tag")
        name = part.get("name")
        if (not isinstance(repository, str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
                or any(piece in {".", ".."} for piece in repository.split("/"))
                or not isinstance(version, str) or not version
                or not isinstance(name, str) or not name or "/" in name or "\\" in name):
            raise ValueError("Public release attachment needs repository, version and filename identities.")
        expected = ("https://github.com/" + repository + "/releases/download/"
                    + urllib.parse.quote(version, safe="") + "/"
                    + urllib.parse.quote(name, safe=""))
        url = part["public_url"]
        if not isinstance(url, str) or url != expected:
            raise ValueError("Public release attachment URL differs from its catalog identity.")
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != "github.com"
                or parsed.query or parsed.fragment):
            raise ValueError("Public release attachment URL must use HTTPS without credentials, query or fragment.")
        return url
    # Existing private catalogs always use their authenticated API URL. Public
    # catalogs without public_url retain their original unauthenticated URL.
    url = part.get("url")
    if not url:
        raise ValueError("Release attachment URL pending for " + part["name"])
    return url

def cached_object(cache, digest):
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("SHA256 object identity required.")
    return native_path(Path(cache) / "objects" / digest)

def unpack_parts(parts, cache, files):
    """Read a verified concatenated tar archive with a closed file allowlist."""
    allowed = {f["sha256"]: f["bytes"] for f in files}
    cache = native_path(cache); cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=cache) as archive:
        for part in parts:
            with Path(part).open("rb") as stream: shutil.copyfileobj(stream, archive, 1024**2)
        archive.seek(0)
        seen = set()
        with tarfile.open(fileobj=archive, mode="r|gz") as bundle:
            for member in bundle:
                digest = member.name.removeprefix("objects/")
                if member.name != "objects/" + digest or digest not in allowed or not member.isfile() or member.size != allowed[digest] or digest in seen:
                    raise ValueError("Unexpected archive entry: " + member.name)
                target = cached_object(cache,digest); target.parent.mkdir(parents=True,exist_ok=True)
                stage = target.with_suffix(".extracting")
                with bundle.extractfile(member) as source, stage.open("wb") as dest:
                    shutil.copyfileobj(source, dest, 1024**2)
                if sha(stage) != digest: raise ValueError("Object checksum mismatch: " + digest)
                stage.replace(target); seen.add(digest)
        if seen != set(allowed): raise ValueError("Archive coverage differs from the file manifest.")

def fetch(root, dataset_id, cache, offline=False):
    c = catalog(root)
    if dataset_id not in c["datasets"]: raise ValueError("Unknown dataset: " + dataset_id)
    dataset = c["datasets"][dataset_id]
    for dependency in dataset.get("dependencies", []): fetch(root, dependency, cache, offline)
    records = dataset["objects"]
    ready = all(cached_object(cache,f["sha256"]).is_file() and sha(cached_object(cache,f["sha256"])) == f["sha256"] for f in records)
    if not ready:
        parts = []
        for part in dataset["parts"]:
            dest = Path(cache)/"parts"/part["sha256"]
            if offline:
                if not dest.is_file() or sha(dest) != part["sha256"]: raise ValueError("Offline cache needs " + part["name"])
            else:
                url = part_download_url(c, dataset, part)
                download(url,dest,part["sha256"],part["bytes"],private=c.get("private",True))
            parts.append(dest)
        unpack_parts(parts,cache,records)
    destination_root=evidence_root(root,dataset.get('source_version'))
    for record in dataset["files"]:
        source = cached_object(cache,record["sha256"])
        if not source.is_file() or sha(source) != record["sha256"]: raise ValueError("Required cached object: " + record["sha256"])
        dest = native_path(safe_path(destination_root,record["path"]))
        if dest.exists() and sha(dest) != record["sha256"]: raise ValueError("Local file has independent edits: " + record["path"])
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists(): shutil.copyfile(source,dest)
    return verify(root,dataset_id)

def verify(root,dataset_id=None):
    c=catalog(root); results=[]
    if dataset_id and dataset_id not in c["datasets"]: raise ValueError("Unknown dataset: "+dataset_id)
    for name,dataset in c["datasets"].items():
        if dataset_id and name != dataset_id:continue
        errors=[]
        destination_root=evidence_root(root,dataset.get('source_version'))
        for record in dataset["files"]:
            path=native_path(safe_path(destination_root,record["path"]))
            if not path.is_file():errors.append({"path":record["path"],"status":"missing","command":f"litz-research data fetch {name}"})
            elif path.stat().st_size!=record["bytes"] or sha(path)!=record["sha256"]:errors.append({"path":record["path"],"status":"checksum_mismatch"})
        results.append(dict(dataset=name,files=len(dataset["files"]),status="passed" if not errors else "failed",errors=errors))
    return results
