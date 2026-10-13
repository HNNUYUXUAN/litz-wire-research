(* Compatibility entry; maintained implementation: models/geometry/src/stages/copper.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","geometry","src","stages","copper.wl"}]];
