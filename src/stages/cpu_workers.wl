(* Compatibility entry; maintained implementation: adapters/wolfram/stages/cpu_workers.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","stages","cpu_workers.wl"}]];
