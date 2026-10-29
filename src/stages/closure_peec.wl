(* Compatibility entry; maintained implementation: models/peec/src/stages/closure_peec.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","peec","src","stages","closure_peec.wl"}]];
