(* Compatibility entry; maintained implementation: adapters/gpu/stages/closure_gpu.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","stages","closure_gpu.wl"}]];
