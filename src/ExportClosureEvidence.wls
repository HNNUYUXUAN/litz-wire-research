(* Compatibility entry; maintained implementation: adapters/wolfram/ExportClosureEvidence.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","ExportClosureEvidence.wls"}]];
