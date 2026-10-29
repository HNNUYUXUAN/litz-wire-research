(* Compatibility entry; maintained implementation: adapters/gpu/GPUAffineKernel.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","GPUAffineKernel.wl"}]];
