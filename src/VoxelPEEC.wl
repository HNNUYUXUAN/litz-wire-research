(* Compatibility entry; maintained implementation: models/rt0/src/VoxelPEEC.wl *)
Get[FileNameJoin[{NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&],"models","rt0","src","VoxelPEEC.wl"}]];
