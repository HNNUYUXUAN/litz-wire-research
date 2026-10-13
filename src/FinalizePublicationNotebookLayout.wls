(* Compatibility entry; maintained implementation: tools/publication/FinalizePublicationNotebookLayout.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","FinalizePublicationNotebookLayout.wls"}]];
