(* Compatibility entry; maintained implementation: models/analytic/src/RunCalibration.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","analytic","src","RunCalibration.wls"}]];
