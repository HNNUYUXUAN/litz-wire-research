"""Deterministic content-addressed research archives with bounded part sizes."""
import gzip
import hashlib
import io
from pathlib import Path
import tarfile
from .common import sha

class PartWriter(io.RawIOBase):
    def __init__(self, directory, name, limit=2**30):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.name=name;self.limit=limit;self.parts=[];self.stream=None;self.count=0;self.digest=None
    def writable(self):return True
    def finish_part(self):
        if self.stream is not None:
            self.stream.flush();self.stream.close()
            self.parts.append(dict(name=self.path.name,bytes=self.count,sha256=self.digest.hexdigest()))
            self.stream=None
    def write(self,data):
        remaining=memoryview(data);total=len(data)
        while remaining:
            if self.stream is None:
                self.path=self.directory/f"{self.name}.tar.gz.part{len(self.parts)+1:03d}"
                self.stream=self.path.open('xb');self.count=0;self.digest=hashlib.sha256()
            take=min(len(remaining),self.limit-self.count);chunk=remaining[:take]
            self.stream.write(chunk);self.digest.update(chunk);self.count+=take;remaining=remaining[take:]
            if self.count==self.limit:self.finish_part()
        return total
    def close(self):
        if not self.closed:self.finish_part()
        super().close()

def pack_objects(objects,store,output,name,part_limit=2**30):
    writer=PartWriter(output,name,part_limit)
    with writer:
        with gzip.GzipFile(fileobj=writer,mode='wb',filename='',mtime=0,compresslevel=3) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as archive:
                for record in sorted(objects,key=lambda x:x['sha256']):
                    path=Path(store)/record['sha256']
                    if path.stat().st_size!=record['bytes'] or sha(path)!=record['sha256']:
                        raise ValueError('Source object identity changed: '+record['sha256'])
                    entry=tarfile.TarInfo('objects/'+record['sha256']);entry.size=record['bytes'];entry.mode=0o644;entry.mtime=0
                    with path.open('rb') as stream:archive.addfile(entry,stream)
    return writer.parts
