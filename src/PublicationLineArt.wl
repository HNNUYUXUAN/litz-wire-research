(* Compatibility entry; maintained implementation: tools/publication/PublicationLineArt.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"tools","publication","PublicationLineArt.wl"}]];
