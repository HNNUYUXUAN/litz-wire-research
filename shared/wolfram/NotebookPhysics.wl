(* Route definitions retain the established LitzPhysics` public context. *)
physicsRoot=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
Get[FileNameJoin[{physicsRoot,"models","analytic","src","Physics.wl"}]];
Get[FileNameJoin[{physicsRoot,"models","geometry","src","Physics.wl"}]];
Get[FileNameJoin[{physicsRoot,"models","common_terminal","src","Physics.wl"}]];
Get[FileNameJoin[{physicsRoot,"models","fem2","src","Physics.wl"}]];
