(* Compatibility entry; maintained implementation: adapters/wolfram/RunClosureSmallTests.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","RunClosureSmallTests.wls"}]];
