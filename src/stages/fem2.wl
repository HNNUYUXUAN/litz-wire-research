(* Compatibility entry; maintained implementation: models/fem2/src/stages/fem2.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","fem2","src","stages","fem2.wl"}]];
