(* Compatibility entry; maintained implementation: tools/publication/VerifyPublicationNativeGeometry.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","VerifyPublicationNativeGeometry.wls"}]];
