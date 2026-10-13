(* Compatibility entry; maintained implementation: tools/research/ArchiveNotebookFormatting.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","research","ArchiveNotebookFormatting.wl"}]];
