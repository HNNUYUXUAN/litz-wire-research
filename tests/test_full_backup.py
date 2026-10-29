"""Exercise deduplication, long paths and corruption rejection from isolated bytes."""
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from SnapshotFullBackup import snapshot,native
from RestoreFullBackup import restore,safe

class FullBackupTests(unittest.TestCase):
    def test_reconciliation_reuses_objects_but_rebuilds_complete_path_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            (source/'changed').write_bytes(b'old');(source/'retained').write_bytes(b'same')
            snapshot(source,root/'base',[])
            (source/'changed').write_bytes(b'new');(source/'added').write_bytes(b'same')
            snapshot(source,root/'final',[],root/'base')
            shutil.rmtree(source)
            result=restore(root/'final',root/'restored')
            self.assertEqual(result['files'],3)
            self.assertEqual((root/'restored/changed').read_bytes(),b'new')
            self.assertEqual((root/'restored/added').read_bytes(),b'same')

    def test_restore_uses_only_packages_with_all_paths_and_empty_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            relative='long/' + ('nested_'*15) + '/' + ('nested_'*15) + '/file.txt'
            long=native(source/relative);long.parent.mkdir(parents=True);long.write_bytes(b'identical')
            (source/'copy.txt').write_bytes(b'identical');(source/'empty').mkdir()
            (source/'credential.xml').write_text('fixture only')
            packages=root/'downloaded'
            self.assertEqual(snapshot(source,packages,[]),0)
            db=sqlite3.connect(packages/'paths.sqlite')
            self.assertEqual(db.execute('select count(*) from objects').fetchone()[0],1);db.close()
            # The original source is unavailable throughout the recovery.
            shutil.rmtree(native(source))
            result=restore(packages,root/'restored')
            self.assertEqual(result['files'],2)
            self.assertEqual(native(root/'restored'/relative).read_bytes(),b'identical')
            self.assertTrue((root/'restored/empty').is_dir())
            self.assertFalse((root/'restored/credential.xml').exists())
            shutil.rmtree(native(root/'restored'))

    def test_corrupt_package_rejected_before_restore(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir();(source/'file').write_bytes(b'fixture')
            packages=root/'downloaded';snapshot(source,packages,[])
            next(packages.glob('*.zip')).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'Package hash'):restore(packages,root/'restored')
            self.assertFalse((root/'restored').exists())
            for path in ['../escape','/absolute','C:/host','dir/../../host']:
                with self.assertRaises(ValueError):safe(root,path)

if __name__=='__main__':unittest.main()
