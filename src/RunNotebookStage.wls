(* Compatibility entry; maintained implementation: adapters/wolfram/RunNotebookStage.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","RunNotebookStage.wls"}]];
