(* Compatibility entry; maintained implementation: adapters/wolfram/EvaluateNotebookHeadless.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","EvaluateNotebookHeadless.wls"}]];
