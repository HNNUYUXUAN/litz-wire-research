"""Archive the superseded publication maintenance chain and map retained algorithms."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / '.local-archive/publication-chain-20261028'
RETAIN = ('PreManuscriptClosure.py', 'FreezePreManuscriptCompute.py', 'PublicationData.py')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    existing = ROOT / 'docs/publication-chain-cleanup-receipt.json'
    if existing.exists() and json.loads(existing.read_text(encoding='utf-8-sig'))['status'] == 'completed':
        raise ValueError('Publication retirement is complete; preserve the original receipt')
    candidates = {p for p in (ROOT / 'tools/publication').iterdir() if p.is_file()}
    for path in list(candidates):
        if path.name not in RETAIN and (ROOT / 'src' / path.name).is_file():
            candidates.add(ROOT / 'src' / path.name)
    for relative in ['tools/BuildPublicReading.py', 'tools/PreparePublicationInputs.py',
                     'tools/AuditScholarlySources.py', 'tools/BuildScholarlyTemplates.py',
                     'tools/MigrateLatexMasters.py', 'tools/BuildResearchSources.py',
                     'tools/research/RunArchiveCache.py', 'tools/research/VerifyClosureDelivery.py',
                     'tools/research/FinalizeClosureCache.py', 'tools/research/ArchiveNotebookFormatting.wl',
                     'src/RunArchiveCache.py', 'src/VerifyClosureDelivery.py', 'src/FinalizeClosureCache.py',
                     'src/ArchiveNotebookFormatting.wl', 'src/BuildArchiveNotebooks.wls',
                     'manuscript/publication.json', 'manuscript/references.bib']:
        if (ROOT / relative).is_file():
            candidates.add(ROOT / relative)
    for folder in [ROOT / 'latex', ROOT / 'manuscript/specimens']:
        candidates.update(p for p in folder.rglob('*') if p.is_file())
    for edition in ['report', 'paper', 'automation']:
        candidates.update((ROOT / 'manuscript' / edition).rglob('*.md'))
    records = []
    for source in sorted(candidates):
        if not source.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('Source outside workspace')
        relative = source.relative_to(ROOT)
        target = ARCHIVE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        identity = sha(source)
        if target.exists() and sha(target) != identity:
            raise ValueError('Archive identity differs: ' + str(relative))
        if not target.exists():
            shutil.copy2(source, target)
        if sha(target) != identity:
            raise ValueError('Archive verification failed')
        row = {'path': relative.as_posix(), 'sha256': identity,
               'retained': target.relative_to(ROOT).as_posix(), 'status': 'archived_pending_removal'}
        if source.parent == ROOT / 'tools/publication' and source.name in RETAIN:
            maintained = ROOT / 'tools/research' / source.name
            if maintained.exists() and sha(maintained) != identity:
                raise ValueError('Maintained implementation already differs')
            shutil.copy2(source, maintained)
            row['maintained'] = maintained.relative_to(ROOT).as_posix()
        records.append(row)
    destination = ROOT / 'docs/publication-chain-cleanup-receipt.json'
    destination.write_bytes((json.dumps({'status': 'archived_pending_removal', 'files': records},
                                       ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print('Archived and verified', len(records), 'files; retained algorithms', len(RETAIN))


if __name__ == '__main__':
    main()
