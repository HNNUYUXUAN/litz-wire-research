(* Compatibility entry; maintained implementation: adapters/wolfram/EnvironmentProbe.wls *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","EnvironmentProbe.wls"}]];
