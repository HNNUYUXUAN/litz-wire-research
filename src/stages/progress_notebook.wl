(* Compatibility entry; maintained implementation: adapters/wolfram/stages/progress_notebook.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","stages","progress_notebook.wl"}]];
