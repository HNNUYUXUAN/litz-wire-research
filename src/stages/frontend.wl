(* Compatibility entry; maintained implementation: adapters/wolfram/stages/frontend.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","stages","frontend.wl"}]];
