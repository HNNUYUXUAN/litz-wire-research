(* Compatibility entry; maintained implementation: adapters/gpu/EvaluateGPUNotebookHeadless.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","gpu","EvaluateGPUNotebookHeadless.wls"}]];
