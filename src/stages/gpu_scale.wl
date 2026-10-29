(* Compatibility entry; maintained implementation: adapters/gpu/stages/gpu_scale.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","stages","gpu_scale.wl"}]];
