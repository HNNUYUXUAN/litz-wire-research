(* Compatibility entry; maintained implementation: adapters/wolfram/RecoverNotebookRun.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","RecoverNotebookRun.wls"}]];
