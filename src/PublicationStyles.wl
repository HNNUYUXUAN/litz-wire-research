(* Compatibility entry; maintained implementation: tools/publication/PublicationStyles.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","PublicationStyles.wl"}]];
