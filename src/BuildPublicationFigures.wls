(* Compatibility entry; maintained implementation: tools/publication/BuildPublicationFigures.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","BuildPublicationFigures.wls"}]];
