(* Compatibility entry; maintained implementation: models/analytic/src/stages/analytic.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","analytic","src","stages","analytic.wl"}]];
