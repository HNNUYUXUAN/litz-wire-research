(* Compatibility entry; maintained implementation: models/analytic/src/ExploreRoundWireCPU.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","analytic","src","ExploreRoundWireCPU.wls"}]];
