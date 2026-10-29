"""Validate six portable masters and their generated reading identities."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from CheckSourceCheckout import validate_current_edition

class CurrentEditionContractTests(unittest.TestCase):
    def fixture(self,root):
        def file(path,text):
            p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode('utf-8'))
            return hashlib.sha256(p.read_bytes()).hexdigest()
        source='manuscript/latex-publication.json'; source_sha=file(source,'{}')
        documents=[]
        for work in ('report','paper','automation'):
            for language in ('en','zh-CN'):
                identity=f'{work}_{language}'; main=f'manuscript/{work}/{language}/main.tex'
                section=f'manuscript/{work}/{language}/sections/01.tex';md=f'publications/reading/{identity}.md'
                mh=file(main,'LaTeX main');sh=file(section,'Section');rh=file(md,'# Research manuscript\n')
                documents.append(dict(id=identity,edition=work,language=language,
                    layout='single' if work=='report' else 'ieee-journal',main=main,main_sha256=mh,
                    sections={section:sh},input_hashes={main:mh,section:sh},markdown=md,markdown_sha256=rh))
        return dict(schema_version=3,run_id='example',source_edition='example',documents=documents,
                    source_manifest=source,source_manifest_sha256=source_sha)
    def test_complete_bilingual_set_is_accepted(self):
        with tempfile.TemporaryDirectory(prefix='Litz source contract ') as folder:
            root=Path(folder);index=self.fixture(root)
            self.assertEqual(validate_current_edition(root,index),[]);self.assertFalse((root/'outputs').exists())
    def test_missing_or_duplicate_language_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);index=self.fixture(root)
            missing=copy.deepcopy(index);missing['documents'].pop()
            duplicate=copy.deepcopy(index);duplicate['documents'][-1]=duplicate['documents'][0]
            for case in (missing,duplicate):
                self.assertTrue(any('six unique' in e for e in validate_current_edition(root,case)))
    def test_invalid_layout_or_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);index=self.fixture(root)
            index['documents'][0]['layout']='ieee-conference';index['documents'][1]['main_sha256']='unverified'
            errors=validate_current_edition(root,index)
            self.assertTrue(any('expected layout' in e for e in errors));self.assertTrue(any('SHA256' in e for e in errors))
    def test_markdown_cannot_leave_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'checkout';root.mkdir();index=self.fixture(root)
            (root.parent/'outside.md').write_text('# Outside\n',encoding='utf-8')
            index['documents'][0]['markdown']='../outside.md'
            self.assertTrue(any('Markdown must' in e for e in validate_current_edition(root,index)))
    def test_stale_source_and_missing_input_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);index=self.fixture(root);doc=index['documents'][0]
            (root/doc['main']).write_text('changed',encoding='utf-8');del doc['input_hashes'][next(iter(doc['sections']))]
            errors=validate_current_edition(root,index)
            self.assertTrue(any('differs' in e for e in errors));self.assertTrue(any('missing or inconsistent' in e for e in errors))

if __name__=='__main__':unittest.main()
