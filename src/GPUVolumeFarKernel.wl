(* Compatibility entry; maintained implementation: adapters/gpu/GPUVolumeFarKernel.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","GPUVolumeFarKernel.wl"}]];
