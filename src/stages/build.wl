(* Compatibility entry; maintained implementation: adapters/wolfram/stages/build.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","stages","build.wl"}]];
