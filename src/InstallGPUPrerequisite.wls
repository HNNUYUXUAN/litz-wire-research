(* Compatibility entry; maintained implementation: adapters/gpu/InstallGPUPrerequisite.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","InstallGPUPrerequisite.wls"}]];
