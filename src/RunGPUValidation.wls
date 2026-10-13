(* Compatibility entry; maintained implementation: adapters/gpu/RunGPUValidation.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","RunGPUValidation.wls"}]];
