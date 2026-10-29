"""Restore only verified downloaded snapshot packages into a fresh directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import zipfile
from SnapshotFullBackup import native


def sha(path):
    h=hashlib.sha256()
    with native(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def safe(root, relative):
    p=PurePosixPath(relative)
    if p.is_absolute() or not p.parts or any(x in {'.','..'} or ':' in x or '\\' in x for x in p.parts):
        raise ValueError('Unsafe restored path')
    target=root.joinpath(*p.parts)
    if not target.is_relative_to(root):raise ValueError('Path escapes restore root')
    return native(target)


def restore(downloads, destination):
    downloads=Path(downloads).resolve();destination=Path(destination).absolute()
    if destination.exists():raise FileExistsError('Restore requires a new directory')
    receipt=json.loads((downloads/'snapshot.json').read_text())
    if receipt['status']!='snapshot_complete':raise ValueError('Snapshot did not pass')
    db=sqlite3.connect('file:'+str(downloads/'paths.sqlite')+'?mode=ro',uri=True)
    try:
        for name,size,digest in db.execute('SELECT name,bytes,sha256 FROM packages'):
            package=safe(downloads,name)
            if not package.is_file() or package.stat().st_size!=size or sha(package)!=digest:raise ValueError('Package hash/size mismatch: '+name)
    except Exception:
        db.close();raise
    destination.mkdir(parents=True)
    count=0;total=0;opened={};exceptions=[]
    try:
        for path,kind,detail in db.execute("SELECT path,kind,detail FROM paths WHERE kind!='file'"):
            if kind=='directory':safe(destination,path).mkdir(parents=True,exist_ok=True)
            elif kind=='error':raise ValueError('Unresolved source error: '+path)
            else:exceptions.append({'path':path,'kind':kind,'detail':detail})
        query='''SELECT p.path,p.bytes,p.mtime_ns,p.sha256,o.package,o.member
          FROM paths p JOIN objects o ON p.sha256=o.sha256 WHERE p.kind='file' ORDER BY o.package,p.path'''
        for path,size,mtime,digest,package,member in db.execute(query):
            target=safe(destination,path);target.parent.mkdir(parents=True,exist_ok=True)
            if member is None:
                source=safe(downloads,package).open('rb')
            else:
                if package not in opened:
                    for archive in opened.values():archive.close()
                    opened={package:zipfile.ZipFile(safe(downloads,package))}
                source=opened[package].open(member)
            h=hashlib.sha256();actual=0
            with source, target.open('xb') as output:
                for block in iter(lambda:source.read(4*1024**2),b''):
                    actual+=len(block)
                    if actual>size:raise ValueError('Restored bytes exceed manifest')
                    h.update(block);output.write(block)
            if h.hexdigest()!=digest or actual!=size or sha(target)!=digest:raise ValueError('Restored file verification failed: '+path)
            os.utime(target,ns=(mtime,mtime));count+=1;total+=size
            if count%5000==0:print(json.dumps({'restored_files':count,'bytes':total}),flush=True)
        expected=db.execute("SELECT COUNT(*),COALESCE(SUM(bytes),0) FROM paths WHERE kind='file'").fetchone()
        if (count,total)!=expected:raise ValueError('Incomplete restore mapping')
    finally:
        for archive in opened.values():archive.close()
        db.close()
    result={'status':'passed','files':count,'bytes':total,'exceptions':exceptions,
            'scope':'Every included file restored from downloaded packages and rehashed; explicit exclusions/reparse identities retained'}
    (destination.parent/(destination.name+'-receipt.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--downloads',required=True,type=Path);p.add_argument('--destination',required=True,type=Path)
    a=p.parse_args();print(json.dumps(restore(a.downloads,a.destination)))
