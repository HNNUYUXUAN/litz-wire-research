(* Compatibility entry; maintained implementation: adapters/wolfram/BuildArchiveNotebooks.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","BuildArchiveNotebooks.wls"}]];
