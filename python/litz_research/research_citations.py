"""Export adopted search records using the project's established citation keys."""
import argparse
import hashlib
import json
from pathlib import Path

from .references import entries


def doi(value):
    return str(value or '').strip().lower().removeprefix('https://doi.org/').removeprefix('doi:').strip()


def export(root, records, output):
    import bibtexparser
    from bibtexparser.bibdatabase import BibDatabase
    from bibtexparser.bwriter import BibTexWriter
    conflicts = records.get('conflicts', []) if isinstance(records, dict) else []
    records = records.get('results') if isinstance(records, dict) else records
    if not isinstance(records, list):
        raise ValueError('Normalized results must be an array')
    canonical = {}
    for entry in entries(root):
        identity = doi(entry.get('doi'))
        if identity:
            if identity in canonical:
                raise ValueError('Duplicate DOI in canonical bibliography: ' + identity)
            canonical[identity] = entry
    selected, provenance = {}, []
    for record in records:
        identity = doi(record.get('doi'))
        if not identity or identity not in canonical:
            raise ValueError('Review and adopt this record in references/library.bib before export: ' + identity)
        entry = canonical[identity]
        selected[entry['ID']] = entry
        provenance.append({'key': entry['ID'], 'doi': identity,
                           'field_sources': record.get('field_sources', {}),
                           'conflicts': record.get('conflicts', {}),
                           'source_platforms': record.get('source_platforms', [])})
    database = BibDatabase()
    database.entries = [selected[key] for key in sorted(selected)]
    writer = BibTexWriter()
    writer.order_entries_by = ('ID',)
    payload = bibtexparser.dumps(database, writer).replace('\r\n', '\n').encode('utf-8')
    if bibtexparser.loads(payload.decode('utf-8')).entries_dict != database.entries_dict:
        raise ValueError('BibTeX export roundtrip changed metadata')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    receipt = {'schema_version': 1, 'canonical_bibliography': 'references/library.bib',
               'canonical_sha256': hashlib.sha256((root / 'references/library.bib').read_bytes()).hexdigest(),
               'export_sha256': hashlib.sha256(payload).hexdigest(), 'keys': sorted(selected),
               'records': provenance, 'normalization_conflicts': conflicts}
    output.with_suffix('.provenance.json').write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', type=Path)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.records.read_text(encoding='utf-8'))
    receipt = export(args.root, data, args.output)
    print(json.dumps({'keys': receipt['keys'], 'export_sha256': receipt['export_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
