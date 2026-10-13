(* Compatibility entry; maintained implementation: adapters/wolfram/stages/delivery_data.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","stages","delivery_data.wl"}]];
