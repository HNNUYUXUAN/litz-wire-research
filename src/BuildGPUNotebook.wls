(* Compatibility entry; maintained implementation: adapters/gpu/BuildGPUNotebook.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","BuildGPUNotebook.wls"}]];
