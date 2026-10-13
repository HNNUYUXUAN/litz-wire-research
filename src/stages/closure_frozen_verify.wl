(* Compatibility entry; maintained implementation: adapters/wolfram/stages/closure_frozen_verify.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"adapters","wolfram","stages","closure_frozen_verify.wl"}]];
