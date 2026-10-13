(* Compatibility entry; maintained implementation: adapters/gpu/stages/gpu_physics.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","stages","gpu_physics.wl"}]];
