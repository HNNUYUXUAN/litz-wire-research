(* Compatibility entry; maintained implementation: models/peec/src/stages/peec_equivalence.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","peec","src","stages","peec_equivalence.wl"}]];
