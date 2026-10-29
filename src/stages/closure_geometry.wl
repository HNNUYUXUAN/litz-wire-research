(* Compatibility entry; maintained implementation: models/geometry/src/stages/closure_geometry.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","geometry","src","stages","closure_geometry.wl"}]];
