"""Create stable, lightweight reading entries from explicitly frozen editions."""
from pathlib import Path
import json,re,shutil
from PIL import Image
from litz_research.common import evidence_root,sha,write,read

def main():
    root=Path(__file__).resolve().parents[1];mount=evidence_root(root)
    base=mount/'outputs/publication_rc1_20261007_01';records=[]
    for edition in ['paper','report']:
        for lang in ['zh-CN','en']:
            source=base/'documents'/edition/lang/(edition+'_'+lang+'.md')
            if not source.exists():raise FileNotFoundError(source)
            text=source.read_text(encoding='utf-8');target=root/'publications'/edition/lang;target.mkdir(parents=True,exist_ok=True)
            def image(match):
                label,relative=match.groups();original=(source.parent/relative).resolve()
                if not original.is_file():raise FileNotFoundError(original)
                dest=root/'publications/assets'/lang/original.name;dest.parent.mkdir(parents=True,exist_ok=True)
                with Image.open(original) as picture:
                    picture.thumbnail((1200,1200));picture.convert('RGB').save(dest,optimize=True)
                records.append({'path':dest.relative_to(root).as_posix(),'source':original.relative_to(mount).as_posix(),'source_sha256':sha(original),'sha256':sha(dest),'processing':'RGB preview; bounded dimensions; same figure identity'})
                return '!['+label+'](../../assets/'+lang+'/'+dest.name+')'
            text=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',image,text).replace(edition+'_'+lang+'.md#','README.md#')
            chapters=[]
            for chapter in sorted(source.parent.glob(edition+'_'+lang+'_*.md')):
                folder=target/'chapters';folder.mkdir(exist_ok=True)
                body=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',image,chapter.read_text(encoding='utf-8'))
                body=body.replace('../../assets/','../../../assets/').replace(edition+'_'+lang+'.md#','../README.md#')
                destination=folder/chapter.name;destination.write_text(body,encoding='utf-8')
                chapters.append('['+chapter.stem.rsplit('_',1)[-1]+'](chapters/'+chapter.name+')')
                records.append({'path':destination.relative_to(root).as_posix(),'source':chapter.relative_to(mount).as_posix(),'source_sha256':sha(chapter),'sha256':sha(destination),'processing':'stable chapter reading path; parent numbering retained'})
            text+='\n\n## Chapters / 章节\n\n'+' · '.join(chapters)+'\n'
            (target/'README.md').write_text(text,encoding='utf-8')
            records.append({'path':(target/'README.md').relative_to(root).as_posix(),'source':source.relative_to(mount).as_posix(),'source_sha256':sha(source),'processing':'stable reading path and lightweight figure links'})
    text='''# Research publications

The complete bilingual reports and papers below retain their frozen scientific source identity. Lightweight previews are available directly in Git. The approved Chinese paper specimen records the editorial and plotting convention for the next scholarly edition.

| Edition | Read | Download PDF |
| --- | --- | --- |
'''
    for edition in ['paper','report']:
        for lang in ['zh-CN','en']:
            asset=edition+'_'+lang+'_single.pdf'
            release=root/'provenance/rc2/release.json'
            link=read(release)['url'] if release.exists() else 'https://github.com/HNNUYUXUAN/litz-wire-research/releases'
            text+='| '+edition+' / '+lang+' | [Markdown]('+edition+'/'+lang+'/README.md) | ['+asset+']('+link+') |\n'
    text+='\nThe candidate Release is private and draft; use authenticated GitHub access. Full Notebooks, figures and historical evidence are restored with `litz-research data fetch academic-editions`. The mount is `data/evidence/v1.0.0-rc.1/`; original relative paths are preserved.\n\n[Approved specimen](../docs/revision-sample-review.zh-CN.md) · [Editorial convention](../manuscript/style.json) · [Citation guide](../docs/citation-guide.md)\n'
    text+='\nDownload one authenticated draft PDF with `gh release download v1.0.0-rc.2 --repo HNNUYUXUAN/litz-wire-research --pattern paper_zh-CN_single.pdf --dir build/reading`; use the table filename for other editions.\n'
    (root/'publications/README.md').write_text(text,encoding='utf-8')
    write(root/'publications/manifest.json',{'source_edition':'publication_rc1_20261007_01','approved_specimen':'publication_20261013_paper_sample_09','files':records})
    print('Stable reading documents',4,'preview/source records',len(records))

if __name__=='__main__':main()
