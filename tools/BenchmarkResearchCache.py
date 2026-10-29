"""Measure paired DOI lookup/reuse stages with identical metadata validation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import time
import urllib.request

from litz_research.latex_publication import save

ROOT = Path(__file__).resolve().parents[1]
DOI = '10.1109/tte.2025.3610369'
TITLE = 'AC Loss Calculation for Litz Wire Windings in Electrical Machines'
URL = 'https://api.crossref.org/works/10.1109%2Ftte.2025.3610369'


def validate(payload):
    record = json.loads(payload)['message']
    checks = {'doi': record['DOI'].lower() == DOI, 'title': record['title'][0] == TITLE,
              'authors': bool(record.get('author')), 'publication_date': bool(record.get('published'))}
    return record, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to((ROOT / 'outputs').resolve()):
        raise ValueError('Benchmark output must be under outputs')
    out.mkdir(exist_ok=False)
    original = ROOT / 'outputs/research_online_20261028_01/crossref-en.json'
    cached = original.read_bytes()
    events = json.loads((original.parent / 'crossref-events.json').read_text(encoding='utf-8'))
    cached_at = next(row['retrieved_at'] for row in events if row.get('file') == original.name and row['status'] == 'retrieved')
    validate(cached)
    cache = out / 'verified-cache.json'
    cache.write_bytes(cached)
    cache_sha = hashlib.sha256(cached).hexdigest()
    rows = []
    for pair, order in enumerate([['live', 'reuse'], ['reuse', 'live'], ['live', 'reuse']], 1):
        for condition in order:
            started = datetime.now(timezone.utc).isoformat()
            start = time.perf_counter()
            row = {'pair': pair, 'condition': condition, 'started_at': started,
                   'network_calls': int(condition == 'live'), 'model_calls': 0,
                   'tokens': None, 'human_interventions': 0}
            try:
                if condition == 'live':
                    request = urllib.request.Request(URL, headers={'User-Agent': 'LitzResearch/1.0 paired-cache-validation'})
                    with urllib.request.urlopen(request, timeout=45) as response:
                        payload = response.read()
                    (out / f'live-{pair}.json').write_bytes(payload)
                else:
                    payload = cache.read_bytes()
                    if hashlib.sha256(payload).hexdigest() != cache_sha:
                        raise ValueError('Cache identity changed')
                record, checks = validate(payload)
                row.update(status='passed' if all(checks.values()) else 'failed', quality_checks=checks,
                           doi=record['DOI'], title=record['title'][0], source_url=URL,
                           retrieved_at=started if condition == 'live' else cached_at,
                           payload_sha256=hashlib.sha256(payload).hexdigest())
            except Exception as error:
                row.update(status='failed', error_type=type(error).__name__, error=str(error))
            row['elapsed_seconds'] = time.perf_counter() - start
            rows.append(row)
            save(out / 'measurements.json', rows)
    receipt = {'scope': 'Paired deterministic DOI retrieval stage; live re-fetch versus verified same-day cache',
               'task': {'doi': DOI, 'expected_title': TITLE}, 'orders': ['live/reuse', 'reuse/live', 'live/reuse'],
               'model': {'invoked': False, 'settings': 'Identical deterministic script in both conditions'},
               'permissions': 'Same interpreter, filesystem and network permission in both conditions',
               'tokens': None, 'token_note': 'No model generation in measured stages; host turn tokens are unavailable',
               'cache_sha256': cache_sha, 'measurements': rows,
               'status': 'passed' if all(r['status'] == 'passed' for r in rows) else 'failed',
               'limitations': ['One DOI, three pairs, same-day metadata; not an end-to-end agent or cross-domain benchmark',
                               'Elapsed measurements exclude human review and initial cache creation; cache freshness requires review'],
               'median_seconds': {condition: statistics.median(r['elapsed_seconds'] for r in rows if r['condition'] == condition)
                                  for condition in ['live', 'reuse']}}
    save(out / 'receipt.json', receipt)
    print(json.dumps({key: receipt[key] for key in ['status', 'median_seconds']}, indent=2))


if __name__ == '__main__':
    main()
