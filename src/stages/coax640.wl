(* Compatibility entry; maintained implementation: models/common_terminal/src/stages/coax640.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","common_terminal","src","stages","coax640.wl"}]];
