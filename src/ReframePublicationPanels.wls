(* Compatibility entry; maintained implementation: tools/publication/ReframePublicationPanels.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","ReframePublicationPanels.wls"}]];
