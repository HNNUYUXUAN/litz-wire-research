(* Compatibility entry; maintained implementation: tools/publication/BuildPublicationDocuments.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","BuildPublicationDocuments.wls"}]];
