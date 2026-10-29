import hashlib
from pathlib import Path
import tempfile
import unittest

from litz_research.research_records import validate


class ResearchRecordsTests(unittest.TestCase):
    def test_normal_queries_are_retained_and_credentials_rejected(self):
        r=self.record()
        for url in ('https://example.org/search?q=litz&year=2026','https://example.org/paper?id=123#abstract'):
            r['url']=url
            self.assertEqual(validate([r],Path.cwd()),[])
        for url in ('https://example.org/?access_token=x','https://example.org/?api_key=x',
                    'https://example.org/;jsessionid=x','https://example.org/#session=x'):
            r['url']=url
            self.assertTrue(validate([r],Path.cwd()))

    def test_malformed_types_dates_status_and_duplicate_identities(self):
        for value in ({},[None],[{'id':[]}],['text']):
            self.assertTrue(validate(value,Path.cwd()))
        for field,value in [('retrieved_at','2026-99-31'),('retrieved_at','2026-10-28'),
                            ('access_status','complete'),('url',[]),('publish_fulltext','false')]:
            r=self.record();r[field]=value
            self.assertTrue(validate([r],Path.cwd()))
        self.assertTrue(validate([self.record(),self.record()],Path.cwd()))

    def test_streamed_pdf_identity_and_failed_access_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'paper.pdf';p.write_bytes(b'%PDF-1.7\n'+b'a'*2097152)
            r=self.record();r.update(access_status='downloaded',local_path='paper.pdf',
                media_type='application/pdf',sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(validate([r],Path(tmp)),[])
        r=self.record();r['access_status']='session_expired'
        self.assertTrue(validate([r],Path.cwd()))
        r['failure_reason']='login required'
        self.assertEqual(validate([r],Path.cwd()),[])

    def record(self):
        return dict(id='paper', title='Example', url='https://doi.org/10.1/example',
                    retrieved_at='2026-10-28T00:00:00Z', provider='crossref', kind='paper',
                    access_status='metadata', identity_status='unverified', redistribution='unknown')

    def test_metadata_does_not_imply_fulltext_rights(self):
        r = self.record()
        self.assertEqual(validate([r], Path.cwd()), [])
        r['publish_fulltext'] = True
        self.assertTrue(validate([r], Path.cwd()))

    def test_download_requires_matching_bytes_and_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'paper.pdf'
            p.write_bytes(b'<html>Sign in</html>')
            r = self.record()
            r.update(access_status='downloaded', local_path='paper.pdf', media_type='application/pdf',
                     sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertTrue(any('not a PDF' in e for e in validate([r], Path(d))))
            p.write_bytes(b'%PDF-1.7\nexample')
            self.assertTrue(any('hash differs' in e for e in validate([r], Path(d))))

    def test_escape_and_session_urls_rejected(self):
        r = self.record()
        r.update(access_status='downloaded', local_path='../outside.pdf', url='https://example.org/?token=example')
        errors = validate([r], Path.cwd())
        self.assertTrue(any('inside' in e for e in errors))
        self.assertTrue(any('canonical' in e for e in errors))

    def test_adopted_code_requires_provenance(self):
        r = self.record()
        r.update(kind='software', use='adopted')
        self.assertTrue(any('commit' in e for e in validate([r], Path.cwd())))

    def test_field_sources_and_status_combinations(self):
        r=self.record()
        r['field_sources']={'title':[{'url':'https://example.org/?session=private','locator':'heading'}]}
        self.assertTrue(validate([r],Path.cwd()))
        r['field_sources']['title'][0]['url']='https://example.org/?id=123'
        self.assertEqual(validate([r],Path.cwd()),[])
        r.update(access_status='failed',failure_reason=' ',identity_status='verified')
        self.assertTrue(validate([r],Path.cwd()))
        r.update(failure_reason='HTTP 503',identity_evidence='Publisher metadata checked before failure')
        self.assertEqual(validate([r],Path.cwd()),[])


if __name__ == '__main__':
    unittest.main()
