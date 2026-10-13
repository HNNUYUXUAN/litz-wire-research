(* Compatibility entry; maintained implementation: adapters/gpu/GPUFarKernel.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","GPUFarKernel.wl"}]];
