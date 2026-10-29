(* Compatibility entry; maintained implementation: models/geometry/src/ExportRetainedTopology.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","geometry","src","ExportRetainedTopology.wls"}]];
