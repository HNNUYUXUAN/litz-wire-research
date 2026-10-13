(* Compatibility entry; maintained implementation: shared/wolfram/NotebookPhysics.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"shared","wolfram","NotebookPhysics.wl"}]];
