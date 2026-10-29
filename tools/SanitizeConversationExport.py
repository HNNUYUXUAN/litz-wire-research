"""Derive private conversation exports without credentials or login sessions."""
import argparse,hashlib,json,re
from pathlib import Path
from AuditPublicContent import PATTERNS

SENSITIVE=re.compile(r'^(?:access[_-]?token|refresh[_-]?token|api[_-]?key|authorization|cookie|set-cookie|password|secret)$',re.I)
SIGNED=re.compile(r'(https?://[^\s"<>?]+)\?[^\s"<>]*(?:X-Amz-|X-Goog-|signature=|sig=)[^\s"<>]*',re.I)
KEY_BLOCK=re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',re.S)

def sanitize(value):
    if isinstance(value,dict):return {k:('[CREDENTIAL OMITTED]' if SENSITIVE.fullmatch(k) and v else sanitize(v)) for k,v in value.items()}
    if isinstance(value,list):return [sanitize(v) for v in value]
    if not isinstance(value,str):return value
    value=KEY_BLOCK.sub('[PRIVATE KEY OMITTED]',value)
    value=SIGNED.sub(r'\1?[SIGNED QUERY OMITTED]',value)
    for category,pattern in PATTERNS.items():value=pattern.sub('[OMITTED:'+category+']',value)
    value=re.sub(r'(?im)\b(authorization|cookie|set-cookie)\s*:\s*[^\r\n]+',r'\1: [SESSION OMITTED]',value)
    return value

def export(source,destination):
    destination.mkdir(parents=True,exist_ok=False);rows=[]
    for file in sorted(source.glob('*.json')):
        raw=file.read_bytes();before=json.loads(raw.decode('utf-8-sig'));after=sanitize(before)
        data=(json.dumps(after,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        (destination/file.name).write_bytes(data)
        rows.append({'name':file.name,'raw_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'redacted':before!=after})
    receipt={'schema_version':1,'scope':'Private project conversation export; credential/session patterns omitted. Original raw export stays local.','files':rows}
    (destination/'sanitization-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return {'files':len(rows),'redacted_files':sum(x['redacted'] for x in rows)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.source,a.destination)))
