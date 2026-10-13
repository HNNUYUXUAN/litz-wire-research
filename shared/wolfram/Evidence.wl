BeginPackage["LitzEvidence`"];
ReadPath::usage="ReadPath[root,path] resolves an existing live path or immutable versioned evidence, verifying catalogued file hashes.";
ReadPath::hash="Frozen evidence checksum differs from the catalog: `1`.";
Begin["`Private`"];
catalog[root_]:=catalog[root]=Import[FileNameJoin[{root,"data","catalog.json"}],"RawJSON"];
ReadPath[root_String,path_String]:=Module[{c,relative,versions,candidates,found,records},
 If[FileExistsQ[path]||DirectoryQ[path],Return[path]];
 c=catalog[root];relative=FileNameDrop[path,FileNameDepth[root]];
 versions=DeleteDuplicates[Prepend[Lookup[Values[c["datasets"]],"source_version",c["tag"]],c["tag"]]];
 candidates=FileNameJoin[{root,"data","evidence",#,relative}]&/@versions;
 found=SelectFirst[candidates,FileExistsQ[#]||DirectoryQ[#]&,path];
 If[FileExistsQ[found],
  records=Select[Flatten[Lookup[Values[c["datasets"]],"files"],1],#["path"]===StringReplace[relative,"\\"->"/"]&];
  If[Length[records]>0&&!AllTrue[records,#["sha256"]===FileHash[found,"SHA256","HexString"]&],Message[ReadPath::hash,relative];Abort[]]];
 found
];
End[];EndPackage[];
