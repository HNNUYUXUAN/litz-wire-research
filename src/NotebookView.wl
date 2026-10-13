(* Compatibility entry; maintained implementation: shared/wolfram/NotebookView.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"shared","wolfram","NotebookView.wl"}]];
