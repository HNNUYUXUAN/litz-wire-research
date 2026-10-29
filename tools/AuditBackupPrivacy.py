"""Audit textual private snapshot objects without printing suspected secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import zipfile
from AuditPublicContent import PATTERNS

TEXT={'.txt','.json','.jsonl','.log','.md','.py','.ps1','.sh','.bash','.toml','.yaml','.yml','.xml','.js','.wls','.wl','.csv','.html','.ini','.cfg','.config','.env'}

def audit(snapshot,output):
    snapshot=Path(snapshot);db=sqlite3.connect(snapshot/'paths.sqlite');findings=[];checked=0
    db.execute('CREATE TEMP TABLE textual(sha256 TEXT PRIMARY KEY)')
    rows=db.execute("SELECT path,sha256 FROM paths WHERE kind='file'").fetchall()
    for path,sha in rows:
        if Path(path).suffix.lower() in TEXT or Path(path).name in {'config','credentials','mathpass'}:
            db.execute('INSERT OR IGNORE INTO textual VALUES(?)',(sha,))
    package=None;archive=None
    try:
        for sha,size,name,member in db.execute('SELECT o.* FROM objects o JOIN textual t ON o.sha256=t.sha256 ORDER BY o.package'):
            if member:
                if package!=name:
                    if archive:archive.close()
                    archive=zipfile.ZipFile(snapshot/name);package=name
                stream=archive.open(member)
            else:stream=(snapshot/name).open('rb')
            categories=set();carry=''
            with stream:
                for block in iter(lambda:stream.read(1024**2),b''):
                    text=carry+block.decode('utf-8',errors='ignore')
                    for category,pattern in PATTERNS.items():
                        if pattern.search(text):categories.add(category)
                    carry=text[-512:]
            if categories:
                paths=[r[0] for r in db.execute('SELECT path FROM paths WHERE sha256=?',(sha,))]
                findings.append({'sha256':sha,'categories':sorted(categories),'paths':paths})
            checked+=1
            if checked%5000==0:print(json.dumps({'checked':checked,'findings':len(findings)}),flush=True)
    finally:
        if archive:archive.close()
        db.close()
    result={'status':'requires_review' if findings else 'passed_pattern_scope','checked_objects':checked,'findings':findings,
            'scope':'Textual objects; no suspected credential values are emitted. Browser profiles, account stores and activation files require path-based exclusions. Compressed historical archives retain separate prior audit evidence.'}
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'status':result['status'],'checked_objects':checked,'findings':len(findings)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(audit(a.snapshot,a.output)))
