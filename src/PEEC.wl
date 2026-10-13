(* Compatibility entry; maintained implementation: models/peec/src/PEEC.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","peec","src","PEEC.wl"}]];
