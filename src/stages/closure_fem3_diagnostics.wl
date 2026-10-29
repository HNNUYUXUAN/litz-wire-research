(* Compatibility entry; maintained implementation: models/aphi/src/stages/closure_fem3_diagnostics.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","aphi","src","stages","closure_fem3_diagnostics.wl"}]];
