$HistoryLength=0;$CharacterEncoding="UTF8";
req=Import[Last[Rest[$ScriptCommandLine]],"RawJSON"];out=req["output_directory"];
ver=Import[FileNameJoin[{out,"notebook_verification.json"}],"RawJSON"];records={};checks={};
Do[
 before=Get[FileNameJoin[{out,"typography_before_02",item["path"]}]];after=Get[FileNameJoin[{out,item["path"]}]];
 a=Cases[before,_Graphics3DBox,Infinity];b=Cases[after,_Graphics3DBox,Infinity];ok=Length[a]==Length[b]&&Map[First,a]===Map[First,b];
 row=First[Select[ver["notebooks"],#["id"]==item["id"]&]];
 AssociateTo[row,{"frontend_raw_box_representation_identical"->row["native_3D_content_unchanged"],"native_3D_content_unchanged"->ok,"geometry_comparison_method"->"Exact primitive equality after both original and final files are read with Get; normalizes front-end serialization whitespace in CompressedData"}];
 AppendTo[records,row];AppendTo[checks,<|"id"->item["id"],"native_3D_count"->Length[b],"exact_saved_file_primitive_equality"->ok|>];Clear[before,after,a,b];
,{item,req["documents"]}];
Export[FileNameJoin[{out,"native_geometry_invariance.json"}],<|"checks"->checks,"passed"->And@@Lookup[checks,"exact_saved_file_primitive_equality"],"physical_solver_calls"->0|>,"RawJSON"];
Export[FileNameJoin[{out,"notebook_verification.json"}],Join[ver,<|"notebooks"->records|>],"RawJSON"];
Exit[If[And@@Lookup[checks,"exact_saved_file_primitive_equality"],0,1]];
