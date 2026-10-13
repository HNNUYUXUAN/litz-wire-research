(* Compatibility entry; maintained implementation: tools/publication/BuildPublicationLauncher.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","BuildPublicationLauncher.wls"}]];
