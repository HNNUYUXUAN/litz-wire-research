(* Compatibility entry; maintained implementation: models/analytic/src/Q1Analytical.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","analytic","src","Q1Analytical.wl"}]];
