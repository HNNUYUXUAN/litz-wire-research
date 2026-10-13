(* Compatibility entry; maintained implementation: models/aphi/src/stages/fem3_ooc.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","aphi","src","stages","fem3_ooc.wl"}]];
