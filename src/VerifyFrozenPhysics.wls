(* Compatibility entry; maintained implementation: adapters/wolfram/VerifyFrozenPhysics.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","VerifyFrozenPhysics.wls"}]];
