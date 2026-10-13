(* Compatibility entry; maintained implementation: tools/publication/VerifyPublicationRedraw.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","VerifyPublicationRedraw.wls"}]];
