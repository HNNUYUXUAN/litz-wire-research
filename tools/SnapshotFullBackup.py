"""Long-path, content-addressed private snapshot with explicit exclusions.

Run into a new directory beneath outputs; later deltas must use another directory.
The SQLite manifest records every observed path, including directories and links.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import time
import zipfile


def native(path):
    value = str(Path(path).absolute())
    return Path('\\\\?\\' + value) if os.name == 'nt' and not value.startswith('\\\\?\\') else Path(value)


def snapshot(source, destination, exclusions, reuse=None):
    source, destination = Path(source).absolute(), Path(destination).absolute()
    destination.mkdir(parents=True, exist_ok=False)
    db = sqlite3.connect(destination / 'paths.sqlite')
    db.executescript('''CREATE TABLE paths(path TEXT PRIMARY KEY, kind TEXT, bytes INTEGER,
      mtime_ns INTEGER, sha256 TEXT, detail TEXT);
      CREATE TABLE objects(sha256 TEXT PRIMARY KEY, bytes INTEGER, package TEXT, member TEXT);
      CREATE TABLE packages(name TEXT PRIMARY KEY, bytes INTEGER, sha256 TEXT);''')
    roots = [source / x for x in exclusions] + [destination]
    forbidden = {'credential.xml', 'credentials', 'credentials.json', 'cookies', 'cookies.sqlite',
                 'login data', 'web data', 'mathpass', 'activationkey', 'id_rsa', 'id_ed25519', '.env'}
    counts = dict(files=0, directories=0, links=0, excluded=0, errors=0, bytes=0, unique_bytes=0)
    package = None
    package_name = None
    package_size = 0
    index = 0
    started = time.time()

    if reuse is not None:
        reuse = Path(reuse).resolve()
        prior = json.loads((reuse/'snapshot.json').read_text(encoding='utf-8'))
        if prior['status'] != 'snapshot_complete': raise ValueError('Reuse requires a complete snapshot')
        old = sqlite3.connect('file:'+str(reuse/'paths.sqlite')+'?mode=ro', uri=True)
        try:
            for name,size,identity in old.execute('SELECT name,bytes,sha256 FROM packages'):
                if Path(name).name != name or ':' in name: raise ValueError('Unsafe package name')
                original = reuse/name
                h=hashlib.sha256()
                with original.open('rb') as stream:
                    for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
                if original.stat().st_size!=size or h.hexdigest()!=identity:raise ValueError('Reuse package changed')
                os.link(original,destination/name)
                db.execute('INSERT INTO packages VALUES(?,?,?)',(name,size,identity))
                if name.startswith('objects-') and name.endswith('.zip'):index=max(index,int(name[8:-4]))
            db.executemany('INSERT INTO objects VALUES(?,?,?,?)',old.execute('SELECT * FROM objects'))
            counts['unique_bytes']=old.execute('SELECT COALESCE(SUM(bytes),0) FROM objects').fetchone()[0]
            db.commit()
        finally:old.close()

    def digest(path):
        h = hashlib.sha256()
        with native(path).open('rb') as stream:
            for chunk in iter(lambda: stream.read(4 * 1024**2), b''): h.update(chunk)
        return h.hexdigest()

    def close_package():
        nonlocal package
        if package:
            package.close()
            path = destination / package_name
            db.execute('INSERT INTO packages VALUES(?,?,?)', (package_name, path.stat().st_size, digest(path)))
            db.commit()
            package = None

    def walk(folder):
        nonlocal package, package_name, package_size, index
        with os.scandir(native(folder)) as entries:
            for entry in entries:
                path = folder / entry.name
                relative = path.relative_to(source).as_posix()
                try:
                    info = entry.stat(follow_symlinks=False)
                    if path in roots or (entry.is_file(follow_symlinks=False) and entry.name.lower() in forbidden):
                        db.execute('INSERT INTO paths VALUES(?,?,?,?,?,?)',
                                   (relative, 'excluded', info.st_size, info.st_mtime_ns, None,
                                    'generated destination' if path in roots else 'credential/session/activation identity'))
                        counts['excluded'] += 1
                    elif info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT if os.name == 'nt' else entry.is_symlink():
                        db.execute('INSERT INTO paths VALUES(?,?,?,?,?,?)',
                                   (relative, 'reparse', 0, info.st_mtime_ns, None, os.readlink(entry.path)))
                        counts['links'] += 1
                    elif entry.is_dir(follow_symlinks=False):
                        db.execute('INSERT INTO paths VALUES(?,?,?,?,?,?)', (relative, 'directory', 0, info.st_mtime_ns, None, None))
                        counts['directories'] += 1
                        walk(path)
                    elif entry.is_file(follow_symlinks=False):
                        sha = digest(path)
                        known = db.execute('SELECT 1 FROM objects WHERE sha256=?', (sha,)).fetchone()
                        if not known:
                            if info.st_size > 2 * 1024**3:
                                target = destination / (sha + '.blob')
                                shutil.copyfile(native(path), target)
                                if digest(target) != sha: raise RuntimeError('changed during copy')
                                db.execute('INSERT INTO packages VALUES(?,?,?)', (target.name, info.st_size, sha))
                                package_id, member = target.name, None
                            else:
                                if package and package_size + info.st_size + 1024 > 2 * 1024**3: close_package()
                                if not package:
                                    index += 1
                                    package_name = f'objects-{index:05d}.zip'
                                    package = zipfile.ZipFile(destination / package_name, 'x', compression=zipfile.ZIP_STORED, allowZip64=True)
                                    package_size = 0
                                member = 'objects/' + sha
                                h = hashlib.sha256()
                                with native(path).open('rb') as stream, package.open(member, 'w', force_zip64=True) as target:
                                    for chunk in iter(lambda: stream.read(4 * 1024**2), b''):
                                        h.update(chunk); target.write(chunk)
                                if h.hexdigest() != sha: raise RuntimeError('changed during packaging')
                                package_size += info.st_size + 1024
                                package_id = package_name
                            db.execute('INSERT INTO objects VALUES(?,?,?,?)', (sha, info.st_size, package_id, member))
                            counts['unique_bytes'] += info.st_size
                        after = entry.stat(follow_symlinks=False)
                        if (after.st_size, after.st_mtime_ns) != (info.st_size, info.st_mtime_ns): raise RuntimeError('changed during snapshot')
                        db.execute('INSERT INTO paths VALUES(?,?,?,?,?,?)', (relative, 'file', info.st_size, info.st_mtime_ns, sha, None))
                        counts['files'] += 1; counts['bytes'] += info.st_size
                        if counts['files'] % 1000 == 0:
                            db.commit()
                            print(json.dumps(counts | {'elapsed_seconds': time.time() - started}), flush=True)
                    else:
                        raise RuntimeError('unsupported filesystem entity')
                except Exception as error:
                    counts['errors'] += 1
                    db.execute('INSERT OR REPLACE INTO paths VALUES(?,?,?,?,?,?)', (relative, 'error', 0, 0, None, str(error)))
    try:
        walk(source)
    except Exception:
        counts['errors'] += 1
        raise
    finally:
        close_package(); db.commit(); db.close()
        receipt = counts | {'status': 'snapshot_complete' if not counts['errors'] else 'failed',
                           'elapsed_seconds': time.time() - started, 'source': str(source),
                           'excluded_roots': [str(x) for x in roots],
                           'scope': 'Private base snapshot; final incremental source reconciliation and privacy audit required before upload.'}
        (destination / 'snapshot.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt), flush=True)
    return counts['errors']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--reuse',type=Path)
    args = parser.parse_args()
    raise SystemExit(bool(snapshot(args.source, args.destination, args.exclude,args.reuse)))
