"""Inspect public source bytes without echoing suspected credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'credential_url': re.compile(r'https?://[^\s/@:]+:[^\s/@]+@'),
    'session_query': re.compile(r'[?&](?:access_token|api_key|apikey|auth_token|sessionid|jsessionid|ticket|signature)=[^\s&"<>]+', re.I),
    'bearer_literal': re.compile(r'Bearer\s+[A-Za-z0-9._~-]{24,}'),
}


def audit(root):
    paths = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root).decode('utf-8').split('\0')
    findings, files = [], []
    for relative in sorted(set(paths)-{''}):
        path=root/relative
        if not path.is_file():
            continue
        payload=path.read_bytes()
        files.append({'path':relative,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)})
        try:
            text=payload.decode('utf-8-sig')
        except UnicodeError:
            continue
        for category,pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({'path':relative,'line':text.count('\n',0,match.start())+1,
                                 'category':category,'matched_text_sha256':hashlib.sha256(match[0].encode()).hexdigest()})
    return {'schema_version':1,'status':'requires_review' if findings else 'passed',
            'scope':'Current Git tracked and nonignored untracked files; pattern checks plus manual source review',
            'limitations':'Pattern checks do not prove absence of all secrets or independently establish redistribution rights',
            'files':files,'findings':findings}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    result=audit(root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'files':len(result['files']),'findings':result['findings']},ensure_ascii=False,indent=2))
    return bool(result['findings'])


if __name__=='__main__':
    raise SystemExit(main())
