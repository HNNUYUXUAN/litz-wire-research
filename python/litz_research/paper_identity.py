"""Check PDF structure and bibliographic identity without granting reuse rights."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from .research_records import file_identity


def compact(value: str) -> str:
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value)).casefold()


def contains_doi(text: str, doi: str) -> bool:
    normalized = unicodedata.normalize('NFKC', text).casefold()
    # PDF extraction may split identifiers across lines; retain an end boundary
    # so an expected identifier cannot match the prefix of another paper's DOI.
    pattern = r'\s*'.join(re.escape(c) for c in compact(doi))
    return bool(re.search(r'(?<![a-z0-9])' + pattern + r'(?![a-z0-9_/-]|\.[a-z0-9])', normalized))


def inspect(path: Path, title: str, doi: str | None = None) -> dict:
    from pypdf import PdfReader

    result = {'filename': path.name, 'expected_title': title, 'expected_doi': doi,
              'identity_status': 'unverified', 'redistribution': 'unknown',
              'method': 'PDF parser plus normalized exact title and DOI in first three pages'}
    try:
        digest, head = file_identity(path)
        result['sha256'] = digest
        if not head.lstrip().startswith(b'%PDF-'):
            raise ValueError('Response is not a PDF')
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError('Encrypted PDF requires an authorized readable copy')
        if not reader.pages:
            raise ValueError('PDF contains no pages')
        text = '\n'.join(page.extract_text() or '' for page in reader.pages[:3])
        normalized = compact(text)
        title_match = bool(title.strip()) and compact(title) in normalized
        doi_match = bool(doi) and contains_doi(text, doi)
        result.update(pdf_status='parser_validated', page_count=len(reader.pages),
                      title_match=title_match, doi_match=doi_match,
                      identity_status='verified' if title_match and doi_match else 'mismatch')
        if not doi:
            result.update(identity_status='unverified', reason='No DOI supplied; inspect author, edition and title manually')
        elif not title_match or not doi_match:
            result['reason'] = 'Expected title or DOI absent; manual inspection required before acceptance'
    except Exception as exc:
        result.update(pdf_status='failed', identity_status='unverified', reason=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--title', required=True)
    parser.add_argument('--doi')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.pdf, args.title, args.doi)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['identity_status'] == 'verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
