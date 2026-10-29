"""Inspect research evidence without conflating access, identity and reuse rights."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl

SENSITIVE = re.compile(r'(?:token|secret|password|passwd|cookie|session|jsessionid|authorization|api[_-]?key|signature|credential|ticket|samlresponse|access[_-]?key)', re.I)


def public_url(value):
    if not isinstance(value, str):return False
    try:
        url = urlsplit(value)
        return bool(url.scheme in ('https', 'http') and url.hostname and not url.username
                    and not url.password and not any(SENSITIVE.search(k) for k, _ in parse_qsl(url.query))
                    and not SENSITIVE.search(url.fragment)
                    and not re.search(r';(?:jsessionid|sessionid)=', url.path, re.I))
    except ValueError:return False


def file_identity(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        head = stream.read(1024)
        digest.update(head)
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):digest.update(chunk)
    return digest.hexdigest(), head


def validate(records: list[dict], root: Path) -> list[str]:
    errors = []
    if not isinstance(records,list):return ['records must be an array']
    identities = set()
    for record in records:
        if not isinstance(record,dict):
            errors.append('record must be an object');continue
        identity = record.get('id', '')
        if not isinstance(identity,str):
            errors.append('id must be text');identity=''
        prefix = identity or '<missing id>'
        if not identity or identity in identities:
            errors.append(f'{prefix}: missing or duplicate identity')
        identities.add(identity)
        for field in ('title', 'url', 'retrieved_at', 'provider', 'kind', 'access_status', 'identity_status', 'redistribution'):
            if not isinstance(record.get(field),str) or not record[field].strip():
                errors.append(f'{prefix}: missing or invalid {field}')
        try:
            date=datetime.fromisoformat(record.get('retrieved_at','').replace('Z','+00:00'))
            if date.tzinfo is None:raise ValueError('timezone required')
        except (ValueError,AttributeError,TypeError):errors.append(f'{prefix}: retrieved_at requires an ISO timestamp with timezone')
        if not public_url(record.get('url')):
            errors.append(f'{prefix}: supply a canonical public URL without session parameters')
        for field,allowed in {
            'kind':('paper','software','skill','forum','documentation','dataset'),
            'access_status':('metadata','accessible','downloaded','unavailable','failed','session_expired'),
            'identity_status':('unverified','verified','mismatch','conflict'),
            'redistribution':('unknown','allowed','restricted','prohibited')}.items():
            if record.get(field) not in allowed:errors.append(f'{prefix}: invalid {field}')
        if record.get('access_status') in ('failed','session_expired','unavailable') and not (
                isinstance(record.get('failure_reason'),str) and record['failure_reason'].strip()):
            errors.append(f'{prefix}: failed access requires failure_reason')
        if 'publish_fulltext' in record and not isinstance(record['publish_fulltext'],bool):
            errors.append(f'{prefix}: publish_fulltext must be boolean')
        for field in ('field_sources','conflicts'):
            if field in record and not isinstance(record[field],dict):errors.append(f'{prefix}: {field} must be an object')
        for field, sources in (record.get('field_sources',{}).items() if isinstance(record.get('field_sources',{}),dict) else []):
            if not isinstance(field,str) or not isinstance(sources,list) or not sources:
                errors.append(f'{prefix}: field_sources entries require non-empty evidence arrays');continue
            for source in sources:
                if not isinstance(source,dict) or not public_url(source.get('url')) or not isinstance(source.get('locator'),str) or not source['locator'].strip():
                    errors.append(f'{prefix}: field source requires public url and locator')
        if record.get('publish_fulltext') and record.get('access_status') != 'downloaded':
            errors.append(f'{prefix}: full-text publication requires a downloaded file')
        if record.get('identity_status') == 'verified' and record.get('access_status') in ('failed','session_expired','unavailable'):
            if not isinstance(record.get('identity_evidence'),str) or not record['identity_evidence'].strip():
                errors.append(f'{prefix}: verified identity with failed access requires separate identity_evidence')
        if record.get('kind') in ('software', 'skill') and record.get('use') in ('adopted', 'modified'):
            for field in ('commit', 'license', 'copyright', 'original_files', 'modifications'):
                if field not in record or record[field] in ('', None):
                    errors.append(f'{prefix}: reused software requires {field}')
            for field in ('commit','license','copyright'):
                if not isinstance(record.get(field),str):errors.append(f'{prefix}: {field} must be text')
            for field in ('original_files','modifications'):
                if not isinstance(record.get(field),list) or any(not isinstance(p,str) for p in record[field]):
                    errors.append(f'{prefix}: {field} must be a text array')
        if record.get('access_status') == 'downloaded':
            relative = record.get('local_path', '')
            if not isinstance(relative,str):relative=''
            path = (root / relative).resolve()
            if not relative or Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
                errors.append(f'{prefix}: download path must remain inside evidence root')
            elif not path.is_file():
                errors.append(f'{prefix}: downloaded file missing')
            else:
                try:digest,head = file_identity(path)
                except OSError as error:
                    errors.append(f'{prefix}: unreadable download: {error}');continue
                if digest != record.get('sha256'):
                    errors.append(f'{prefix}: downloaded file hash differs')
                if record.get('media_type') == 'application/pdf' and not head.lstrip().startswith(b'%PDF-'):
                    errors.append(f'{prefix}: response is not a PDF')
        if record.get('publish_fulltext') and not (
            record.get('redistribution') == 'allowed' and record.get('rights_evidence')
            and record.get('identity_status') == 'verified'
        ):
            errors.append(f'{prefix}: publication requires verified identity and redistribution evidence')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', type=Path)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:errors = validate(json.loads(args.records.read_text(encoding='utf-8')), args.root)
    except (OSError,ValueError) as error:errors = [str(error)]
    print(json.dumps({'status': 'failed' if errors else 'passed', 'errors': errors}, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
