(* Compatibility entry; maintained implementation: tools/research/ClosureCSV.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","research","ClosureCSV.wl"}]];
