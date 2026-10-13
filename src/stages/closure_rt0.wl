(* Compatibility entry; maintained implementation: models/rt0/src/stages/closure_rt0.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","rt0","src","stages","closure_rt0.wl"}]];
