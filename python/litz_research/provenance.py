"""Portable metadata derivatives with explicit numeric identity checks."""
import hashlib
import json
import re

def numeric_tree(value, path=()):
    """Identify JSON numbers by full structural path, including array positions."""
    if isinstance(value,dict):
        for key,item in value.items():yield from numeric_tree(item,path+(key,))
    elif isinstance(value,list):
        for index,item in enumerate(value):yield from numeric_tree(item,path+(index,))
    elif isinstance(value,(int,float,bool)):
        yield path,value

def portable_text(text):
    """Normalize recorded machine locations while retaining relative suffixes."""
    text=re.sub(r"(?i)[A-Z]:[\\/]+Workspaces[\\/]+repos[\\/]+litz-wire-research", "${PROJECT_ROOT}",text)
    text=re.sub(r"(?i)[A-Z]:[\\/]+Workspaces[\\/]+repos[\\/]+litz-wire-modeling-src", "${PROJECT_ROOT}",text)
    text=re.sub(r"(?i)[A-Z]:[\\/]+Workspaces[\\/]+repos[\\/]+litz-wire-modeling", "${SOURCE_ARCHIVE}",text)
    text=re.sub(r"(?i)[A-Z]:[\\/]+Workspaces[\\/]+archives", "${ARCHIVE_ROOT}",text)
    text=re.sub(r"(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"<>]+", "${USER_HOME}",text)
    text=re.sub(r'(?i)("(?:username|user_name|computername|computer_name|hostname|host_name)"\s*:\s*)"[^"\r\n]*"',r'\1"local-research-environment"',text)
    return text

def derive_text(raw, suffix):
    """Return candidate bytes and quantitative verification for a text source."""
    original=raw.decode("utf-8-sig")
    derived=portable_text(original)
    quantitative="unchanged_text" if derived==original else "path_metadata_only"
    if suffix==".json":
        before=json.loads(original);after=json.loads(derived)
        if list(numeric_tree(before))!=list(numeric_tree(after)):
            raise ValueError("JSON quantitative identity changed.")
        quantitative="all_numeric_paths_equal"
    return derived.encode("utf-8"),quantitative

def derive_wxf(source,destination):
    """Rewrite WXF string metadata while preserving every non-string token byte."""
    import io
    import zlib
    from wolframclient.deserializers.wxf.wxfparser import WXFParser
    class Capture:
        def __init__(self,reader):self.reader=reader;self.parts=[]
        def read(self,n):
            data=self.reader.read(n);self.parts.append(data);return data
        def take(self):
            data=b''.join(self.parts);self.parts=[];return data
    def varint(n):
        result=bytearray()
        while n>=128:result.append((n&127)|128);n>>=7
        result.append(n);return bytes(result)
    source_numeric=hashlib.sha256();modified=0
    with open(source,'rb') as input_stream,open(destination,'wb') as output_stream:
        parser=WXFParser(input_stream);capture=Capture(parser.reader);parser.reader=capture
        compressor=zlib.compressobj(3);output_stream.write(b'8C:')
        for token in parser.tokens():
            raw=capture.take()
            if token.wxf_type==b'S':
                value=portable_text(token.data)
                if value!=token.data:
                    encoded=value.encode('utf-8');raw=b'S'+varint(len(encoded))+encoded;modified+=1
            else:source_numeric.update(raw)
            output_stream.write(compressor.compress(raw))
        output_stream.write(compressor.flush())
    result_numeric=hashlib.sha256()
    with open(destination,'rb') as stream:
        parser=WXFParser(stream);capture=Capture(parser.reader);parser.reader=capture
        for token in parser.tokens():
            raw=capture.take()
            if token.wxf_type!=b'S':result_numeric.update(raw)
    if source_numeric.digest()!=result_numeric.digest():raise ValueError('WXF numerical token identity changed.')
    return dict(changed_string_tokens=modified,non_string_token_sha256=source_numeric.hexdigest(),quantitative_check='all_non_string_tokens_byte_identical')

def derive_parasolid(raw):
    """Use portable names in the ASCII header, retaining binary offsets and body."""
    marker=b'**END_OF_HEADER'
    position=raw.find(marker)
    if position<0:raise ValueError('Parasolid header marker required.')
    end=raw.index(b'\n',position)+1;header=raw[:end];body=raw[end:]
    def field(match):
        value=match[2];name=value.replace(b'\\',b'/').split(b'/')[-1]
        if len(name)>len(value):raise ValueError('Parasolid field capacity')
        return match[1]+name.ljust(len(value),b' ')+b';'
    derived=re.sub(rb'(?m)^((?:KEY|FILE)=)([^;\r\n]*);',field,header)
    result=derived+body
    if len(result)!=len(raw) or result[end:]!=body:raise ValueError('Parasolid body identity changed.')
    return result,dict(header_bytes=end,geometry_payload_sha256=hashlib.sha256(body).hexdigest(),quantitative_check='binary_geometry_and_offsets_byte_identical')
