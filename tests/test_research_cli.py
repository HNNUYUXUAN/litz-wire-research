"""Exercise download integrity, archive boundaries and the analytical entry."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import tarfile
import tempfile
import threading
import unittest
from litz_research.common import project, run_directory, safe_path, sha
from litz_research.data import download, unpack_parts
from litz_research.analytical import execute
from litz_research.packaging import pack_objects
from litz_research.provenance import derive_text

class ResearchTests(unittest.TestCase):
    def test_metadata_derivative_keeps_numeric_paths(self):
        source=b'{"file":"C:/Users/researcher/work/data.csv","I":{"real":2.0,"imag":-3.0},"passed":false}'
        candidate,proof=derive_text(source,'.json')
        self.assertNotIn(b'C:/Users/',candidate)
        self.assertEqual(proof,'all_numeric_paths_equal')

    def test_pack_respects_part_limit_and_restores(self):
        content=bytes(range(256))*8;digest=hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=root/'store';store.mkdir();(store/digest).write_bytes(content)
            files=[dict(sha256=digest,bytes=len(content))]
            parts=pack_objects(files,store,root/'parts','example',part_limit=97)
            self.assertGreater(len(parts),1)
            self.assertTrue(all(p['bytes']<=97 for p in parts))
            unpack_parts([root/'parts'/p['name'] for p in parts],root/'cache',files)
            self.assertEqual((root/'cache/objects'/digest).read_bytes(),content)

    def test_analytical_reference_and_unique_run(self):
        with tempfile.TemporaryDirectory(prefix="Litz Example ") as tmp:
            root=Path(tmp);output=run_directory(root,"analytic_01")
            result=execute(project(),output)
            self.assertEqual(len(result["checks"]),12)
            self.assertTrue(all(c["passed"] for c in result["checks"]))
            with self.assertRaises(FileExistsError):run_directory(root,"analytic_01")

    def test_paths_stay_in_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in ["../escape", "C:/escape", "/escape"]:
                with self.assertRaises(ValueError):safe_path(tmp,path)

    def test_download_resume_and_corruption(self):
        content=b"reference dataset\n"*10000;digest=hashlib.sha256(content).hexdigest();ranges=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                offset=int(self.headers.get("Range","bytes=0-").split("=")[1].split("-")[0]);ranges.append(offset)
                self.send_response(206 if offset else 200)
                self.send_header("Content-Length",str(len(content)-offset))
                if offset:self.send_header("Content-Range",f"bytes {offset}-{len(content)-1}/{len(content)}")
                self.end_headers();self.wfile.write(content[offset:])
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/"part";partial=Path(tmp)/"part.partial";partial.write_bytes(content[:1327])
                url=f"http://127.0.0.1:{server.server_port}/data"
                download(url,target,digest,len(content));self.assertEqual(ranges,[1327]);self.assertEqual(sha(target),digest)
                bad=Path(tmp)/"bad"
                with self.assertRaises(ValueError):download(url,bad,"0"*64,len(content))
                self.assertFalse(bad.exists())
        finally:server.shutdown();thread.join();server.server_close()

    def test_archive_parts_restore_and_member_integrity(self):
        content=b"current real imaginary\n1 2 3\n";digest=hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory(prefix="Litz Data ") as tmp:
            root=Path(tmp);bundle=io.BytesIO()
            with tarfile.open(fileobj=bundle,mode="w:gz") as archive:
                item=tarfile.TarInfo("objects/"+digest);item.size=len(content);archive.addfile(item,io.BytesIO(content))
            binary=bundle.getvalue();a=root/"1";b=root/"2";a.write_bytes(binary[:40]);b.write_bytes(binary[40:])
            unpack_parts([a,b],root/"cache",[{"sha256":digest,"bytes":len(content)}])
            self.assertEqual((root/"cache/objects"/digest).read_bytes(),content)
            with self.assertRaises(ValueError):unpack_parts([a,b],root/"bad",[{"sha256":"0"*64,"bytes":len(content)}])

if __name__=="__main__":unittest.main()
