(* Compatibility entry; maintained implementation: tools/publication/VerifyPublicationRestore.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","VerifyPublicationRestore.wls"}]];
