(* Convert archived evidence only. Never load stage/solver source or run a solver. *)
$HistoryLength=0;$CharacterEncoding="UTF8";
ceCPUText=Environment["LITZ_CLOSURE_CPU_THREADS"];
ceCPUThreadLimit=If[StringQ[ceCPUText]&&StringMatchQ[ceCPUText,DigitCharacter..],Min[8,Max[1,ToExpression[ceCPUText]]],8];
If[Quiet[Check[SetSystemOptions["ParallelOptions"->"ParallelThreadNumber"->Min[ceCPUThreadLimit,$ProcessorCount]],$Failed]]===$Failed,Print["CPU thread cap could not be configured"];Exit[2]];
ceMaximumArrayElements=2000000;
ceRoot=NestWhile[DirectoryName,DirectoryName[$InputFileName],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&];
ceDir=Environment["LITZ_CLOSURE_EXPORT_DIR"];
ceIndex=Environment["LITZ_CLOSURE_INDEX"];
If[!StringQ[ceDir]||ceDir==="",Print["LITZ_CLOSURE_EXPORT_DIR is required"];Exit[2]];
If[!StringQ[ceIndex]||ceIndex==="",ceIndex=FileNameJoin[{ceRoot,"docs","总控","当前运行索引.json"}]];
If[!FileExistsQ[ceIndex],Print["Frozen index missing"];Exit[2]];
If[!DirectoryQ[ceDir],CreateDirectory[ceDir,CreateIntermediateDirectories->True]];
ceRel[p_String]:=StringReplace[FileNameDrop[p,FileNameDepth[ceRoot]],"\\"->"/"];
ceOutRel[p_String]:=StringReplace[FileNameDrop[p,FileNameDepth[ceDir]],"\\"->"/"];
ceJSON[p_,v_]:=Module[{r},r=Quiet[Check[Export[p,v,"RawJSON"],$Failed]];If[r===$Failed,Print["JSON export failed: ",p];Throw["json_export_failed"]];r];
ceRead[p_]:=If[FileExistsQ[p],Quiet[Check[Import[p,"RawJSON"],<||>]],<||>];
ceFrozen=FileNameJoin[{ceDir,"source_index.json"}];
If[FileExistsQ[ceFrozen],If[FileHash[ceFrozen,"SHA256"]=!=FileHash[ceIndex,"SHA256"],Print["Frozen index differs; use a new bundle"];Exit[2]],CopyFile[ceIndex,ceFrozen]];
ceIndexHash=FileHash[ceFrozen,"SHA256","HexString"];
cePins=Lookup[ceRead[ceFrozen],"routes",<||>];
If[!AssociationQ[cePins]||Length[cePins]==0,Print["No pinned routes"];Exit[2]];
If[!AllTrue[Keys[cePins],StringMatchQ[#,RegularExpression["[A-Za-z0-9_-]+"]]&],Print["Invalid route path component"];Exit[2]];
ceManifestPath=FileNameJoin[{ceDir,"closure_manifest.json"}];
ceManifest=If[FileExistsQ[ceManifestPath],ceRead[ceManifestPath],<|"schema_version"->1,"source_index"->"source_index.json","source_index_sha256"->ceIndexHash,"selection_policy"->"explicit frozen run_id; no mtime selection","routes"-><||>,"conversion_policy"->"Read preserved WXF/JSON; large dense operator matrices remain in the hashed original WXF. Numeric currents, coordinates, connectivity, markers and profiles are exported. No solver execution."|>];
cePointerQ[p_]:=Module[{s},s=OpenRead[p,BinaryFormat->True];With[{b=BinaryReadList[s,"Byte",Min[256,FileByteCount[p]]]},Close[s];StringStartsQ[FromCharacterCode[b],"version https://git-lfs.github.com/spec/v1"]]];
ceFiniteQ[x_]:=NumberQ[x]&&FreeQ[x,Indeterminate|_DirectedInfinity];
ceNum[x_]:=Which[IntegerQ[x],x,TrueQ[x==0],0,True,N[x,17]];
ceUnit[path_String]:=Which[StringContainsQ[path,"W_per_m3"],"W/m^3",StringContainsQ[path,"A_per_m2"],If[StringContainsQ[path,"RMS_A_per_m2"],"A/m^2 RMS","A/m^2"],StringContainsQ[path,"V_per_m"],"V/m",StringContainsQ[path,"S_per_m"],"S/m",StringContainsQ[path,"ohm_m"],"ohm m",StringContainsQ[path,"H_per_m"],"H/axial_m",StringContainsQ[path,"W_per_axial_m"],"W/axial_m",StringContainsQ[path,"m3_per_axial_m"],"m^3/axial_m",StringContainsQ[path,"RMS_A"]||StringEndsQ[path,"/currents"],"A RMS",StringContainsQ[path,"ohm_per_m"]||StringContainsQ[path,"ohm_per_axial_m"],"ohm/axial_m",StringEndsQ[path,"_ohm"]||StringEndsQ[path,"/impedance"],"ohm",StringContainsQ[path,"W_per_m"],"W/axial_m",StringEndsQ[path,"_W"],"W",StringEndsQ[path,"_m2"],"m^2",StringEndsQ[path,"_m3"],"m^3",StringEndsQ[path,"_m"],"m",StringEndsQ[path,"_V"]||StringEndsQ[path,"/voltage"],"V RMS",StringEndsQ[path,"_H"],"H",StringEndsQ[path,"_Hz"],"Hz",StringContainsQ[path,"seconds"],"s",StringContainsQ[path,"residual"]||StringContainsQ[path,"relative_error"],"dimensionless",True,"unspecified_in_source; see model_assumptions and field definitions"];
ceName[path_String]:=StringTake[StringReplace[path,Except[LetterCharacter|DigitCharacter|"_"|"-"]->"_"],UpTo[120]]<>"_"<>StringTake[Hash[path,"SHA256","HexString"],12];
ceAsset[p_,kind_,extra_:<||>]:=Join[<|"path"->ceOutRel[p],"sha256"->FileHash[p,"SHA256","HexString"],"bytes"->FileByteCount[p],"kind"->kind|>,extra];
ceRTAbs=10.^-30;ceRTRel=2.*^-14;
ceRTNumber[x_?NumberQ]:=x;
ceRTNumber[x_String]:=If[StringMatchQ[x,RegularExpression["[-+]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][-+]?[0-9]+|\\*\\^[-+]?[0-9]+)?"]],ToExpression[StringReplace[x,RegularExpression["[eE]"]->"*^"]],$Failed];
ceRTNumber[_]:=$Failed;
ceRTWithin[a_,b_]:=ceFiniteQ[a]&&ceFiniteQ[b]&&Abs[a-b]<=ceRTAbs+ceRTRel Abs[a];
ceRTJSON[original_,restored_,path_]:=Which[
 AssociationQ[original],If[!AssociationQ[restored]||Sort[Keys[original]]=!=Sort[Keys[restored]],Throw["JSON_roundtrip_key_mismatch"]];KeyValueMap[ceRTJSON[#2,restored[#1],path<>"/"<>ToString[#1]]&,original],
 ListQ[original],If[!ListQ[restored]||Length[original]=!=Length[restored],Throw["JSON_roundtrip_list_mismatch"]];MapIndexed[ceRTJSON[#1,restored[[First[#2]]],path<>"/"<>ToString[First[#2]]]&,original],
 ceFiniteQ[original],If[IntegerQ[original]&&original=!=restored,Throw["JSON_integer_roundtrip_mismatch"]];If[!ceRTWithin[original,restored],Throw["JSON_scalar_roundtrip_numeric_mismatch"]];ceJSONRTCount++;ceJSONRTAbs=Max[ceJSONRTAbs,Abs[original-restored]];ceJSONRTRel=Max[ceJSONRTRel,Abs[original-restored]/Max[Abs[original],10.^-300]];ceJSONRTNorm=Max[ceJSONRTNorm,Abs[original-restored]/(ceRTAbs+ceRTRel Abs[original])],
 True,If[original=!=restored,Throw["JSON_roundtrip_value_mismatch"]]];
ceArray[v_,path_]:=Module[{dims=Dimensions[v],name,file,flat,complex,rows,headers,desc,readback,restored,difference,rt,anchors,componentOriginal,componentRestored},
 name=ceName[path]<>".csv";file=FileNameJoin[{ceRouteDir,"arrays",name}];
 flat=Flatten[v];complex=AnyTrue[flat,Head[#]===Complex&];
 headers=If[complex,{"flat_index_1based","real","imag"},{"flat_index_1based","value"}];
 rows=If[complex,MapIndexed[{First[#2],ceNum[Re[#1]],ceNum[Im[#1]]}&,flat],MapIndexed[{First[#2],ceNum[#1]}&,flat]];
 If[Quiet[Check[Export[file,Prepend[rows,headers],"CSV"],$Failed]]===$Failed,Throw["csv_export_failed"]];
 (* Independent serializer/importer readback, compared directly with this original
    preserved WXF array; generated numbers alone are parsed, no model evaluation. *)
 readback=Quiet[Check[Import[file,"CSV"],$Failed]];
 If[!ListQ[readback]||Length[readback]=!=Length[rows]+1||First[readback]=!=headers,Throw["CSV_roundtrip_header_or_count_mismatch"]];
 readback=Map[ceRTNumber,Rest[readback],{2}];
 If[!AllTrue[readback,ListQ[#]&&Length[#]===Length[headers]&&AllTrue[#,ceFiniteQ]&]||readback[[All,1]]=!=Range[Length[flat]],Throw["CSV_roundtrip_index_or_numeric_mismatch"]];
 restored=If[complex,readback[[All,2]]+I readback[[All,3]],readback[[All,2]]];
 componentOriginal=If[complex,Flatten[Transpose[{Re[flat],Im[flat]}]],flat];
 componentRestored=If[complex,Flatten[Transpose[{Re[restored],Im[restored]}]],restored];
 If[!And@@MapThread[ceRTWithin,{componentOriginal,componentRestored}],Throw["CSV_roundtrip_original_WXF_numeric_mismatch"]];
 difference=Abs[componentOriginal-componentRestored];
 anchors=DeleteDuplicates[{1,Max[1,Ceiling[Length[flat]/2]],Length[flat]}];
 rt=<|"passed"->True,"source_key"->path,"csv_path"->ceOutRel[file],"dimensions"->dims,"element_count"->Length[flat],"complex"->complex,"indices_verified"->True,"components_compared"->Length[componentOriginal],"maximum_absolute_error"->Max[difference],"maximum_relative_error"->Max[MapThread[#1/Max[Abs[#2],10.^-300]&,{difference,componentOriginal}]],"absolute_tolerance"->ceRTAbs,"relative_tolerance"->ceRTRel,"original_WXF_anchors"->Map[Function[i,<|"flat_index_1based"->i,"real"->ceNum[Re[flat[[i]]]],"imag"->ceNum[Im[flat[[i]]]]|>],anchors]|>;
 AppendTo[ceRoundTrips,rt];
 ceRoundTrips[[-1]]=Append[rt,"maximum_normalized_error"->Max[MapThread[#1/(ceRTAbs+ceRTRel Abs[#2])&,{difference,componentOriginal}]]];
 desc=<|"representation"->"numeric_csv","path"->ceOutRel[file],"dimensions"->dims,"element_count"->Length[flat],"order"->"Wolfram Flatten row-major; flat_index is 1-based","complex"->complex,"unit"->ceUnit[path],"source_key"->path|>;
 AssociateTo[desc,"roundtrip_verified"->True];
 AppendTo[ceAssets,ceAsset[file,"numeric_array",desc]];desc];
ceMesh[v_,path_]:=Module[{coords,elements,out},
 coords=Quiet[Check[v["Coordinates"],$Failed]];elements=Quiet[Check[v["MeshElements"],$Failed]];
 If[!MatrixQ[coords,NumericQ]||!ListQ[elements],Return[<|"representation"->"not_exportable","object_head"->ToString[Head[v]],"reason"->"mesh property extraction failed","source_key"->path|>]];
 out=<|"representation"->"archived_element_mesh","coordinate_unit"->"model_coordinates; do not assume metres","coordinates"->ceConvert[coords,path<>"/coordinates"]|>;
 out["elements"]=MapIndexed[<|"element_type"->ToString[Head[#1]],"connectivity"->ceConvert[#1[[1]],path<>"/elements/"<>ToString[First[#2]]<>"/connectivity"],"markers"->If[Length[#1]>=2,ceConvert[#1[[2]],path<>"/elements/"<>ToString[First[#2]]<>"/markers"],<|"representation"->"not_present"|>]|>&,elements];out];
ceFieldSamples[a_Association,path_]:=Module[{coords,fields,samples},
 If[!KeyExistsQ[a,"mesh"],Return[<||>]];
 coords=Quiet[Check[a["mesh"]["Coordinates"],$Failed]];
 fields=Lookup[a,"fields",Lookup[a,"field",None]];
 If[Head[fields]===InterpolatingFunction,fields={fields}];
 If[!MatrixQ[coords,NumericQ]||!ListQ[fields]||!AllTrue[fields,Head[#]===InterpolatingFunction&],Return[<||>]];
 samples=Quiet[Check[Transpose[Table[(f@@#)&/@coords,{f,fields}]],$Failed]];
 If[!MatrixQ[samples,ceFiniteQ],Return[<|"field_node_samples"-><|"representation"->"not_exportable","reason"->"archived interpolant sampling failed"|>|>]];
 <|"field_node_samples"-><|"representation"->"samples_of_archived_interpolants","values"->ceArray[samples,path<>"/field_node_samples"],"coordinate_reference"->path<>"/mesh/coordinates","field_component_order"->Range[Length[fields]],"unit"->"model_field_units; see source equations","scope"->"sampled preserved interpolants at preserved mesh nodes; no new field solve"|>|>];
ceConvert[v_,path_String]:=Which[
 AssociationQ[v],Join[Association@KeyValueMap[ToString[#1]->ceConvert[#2,path<>"/"<>ToString[#1]]&,v],ceFieldSamples[v,path]],
 MatchQ[v,True|False|Null]||StringQ[v],v,
 Head[v]===Complex&&ceFiniteQ[v],<|"representation"->"complex_re_im","real"->ceNum[Re[v]],"imag"->ceNum[Im[v]],"unit"->ceUnit[path]|>,
 ceFiniteQ[v],ceNum[v],
 MemberQ[{"R_ohm","L_H","resistance_matrix_ohm","partial_inductance_matrix_H","Z_ohm"},Last[StringSplit[path,"/"]]]&&(ByteCount[v]>1024^2||(Length[Dimensions[v]]==2&&Times@@Dimensions[v]>65536)),<|"representation"->"retained_in_original_WXF","reason"->"operator matrix excluded from lightweight viewer; preserved source hash and WXF remain authoritative","dimensions"->Dimensions[v],"source_key"->path|>,
 StringContainsQ[ToString[Head[v]],"ElementMesh"],ceMesh[v,path],
 Head[v]===SparseArray&&Times@@Dimensions[v]>2000000,<|"representation"->"retained_in_original_WXF","reason"->"large sparse operator retained without allocating its dense expansion","dimensions"->Dimensions[v],"source_key"->path|>,
 ListQ[v]&&Length[Dimensions[v]]>=2&&Times@@Dimensions[v]>ceMaximumArrayElements,<|"representation"->"retained_in_original_WXF","reason"->"large multidimensional array retained to bound CSV/readback allocations; the complete hashed original remains authoritative","dimensions"->Dimensions[v],"source_key"->path|>,
 Head[v]===SparseArray,ceConvert[Normal[v],path],
 ListQ[v]&&ArrayQ[v,_,ceFiniteQ]&&Length[Flatten[v]]>128,ceArray[v,path],
 ListQ[v],MapIndexed[ceConvert[#1,path<>"/"<>ToString[First[#2]]]&,v],
 True,<|"representation"->"not_exportable","object_head"->ToString[Head[v]],"reason"->"non-numeric Wolfram object; original retained in hashed WXF","source_key"->path|>];
ceSourceRecord[p_]:=Module[{h=Quiet[Check[FileHash[p,"SHA256","HexString"],$Failed]]},If[!StringQ[h],Throw["source_file_hash_failed"]];<|"path"->ceRel[p],"sha256"->h,"bytes"->FileByteCount[p]|>];
ceOriginalFiles[source_]:=Sort@Select[FileNames["*",source,Infinity],FileExistsQ[#]&&!DirectoryQ[#]&];
ceCustomQ[p_,source_]:=Module[{relative=StringReplace[FileNameDrop[p,FileNameDepth[source]],"\\"->"/"]},
 !StringStartsQ[relative,"source_snapshot/"]&&!StringStartsQ[relative,"source_snapshots/"]&&
 !MemberQ[{"environment.json","process_status.json","resource_budget.json","run_manifest.json"},FileNameTake[p]]&&
 !MemberQ[{"results.json","parameters.json","test_report.json"},relative]&&MemberQ[{"json","csv"},ToLowerCase[FileExtension[p]]]];
(* Index every scalar key without a fixed truncation limit. Dense numeric vectors
   are referenced in their complete cached JSON/CSV rather than duplicated here. *)
ceScalarWalk[v_,path_]:=Which[
 AssociationQ[v]&&Lookup[v,"representation",None]==="complex_re_im",AppendTo[ceScalarItems,Join[ceScalarContext,<|"source_key"->path,"kind"->"complex_re_im","real"->v["real"],"imag"->v["imag"],"unit"->Lookup[v,"unit",ceUnit[path]]|>]],
 AssociationQ[v]&&KeyExistsQ[v,"representation"],AppendTo[ceVectorReferences,Join[ceScalarContext,<|"source_key"->path,"representation"->v|>]],
 AssociationQ[v],KeyValueMap[ceScalarWalk[#2,path<>"/"<>ToString[#1]]&,v],
 ListQ[v]&&ArrayQ[v,_,ceFiniteQ]&&Length[Flatten[v]]>128,AppendTo[ceVectorReferences,Join[ceScalarContext,<|"source_key"->path,"representation"->"numeric_array_in_complete_cached_JSON","dimensions"->Dimensions[v]|>]],
 ListQ[v],MapIndexed[ceScalarWalk[#1,path<>"/"<>ToString[First[#2]]]&,v],
 ceFiniteQ[v]||StringQ[v]||MatchQ[v,True|False|Null],AppendTo[ceScalarItems,Join[ceScalarContext,<|"source_key"->path,"kind"->If[ceFiniteQ[v],"numeric_scalar","annotation"],"value"->v,"unit"->If[ceFiniteQ[v],ceUnit[path],"not_applicable_annotation"]|>]],
 True,Null];
ceExportRoute[route_,pin_]:=Module[{run,source,wxf,result,test,process,payload,converted,meta,sources,files,rawManifest,start,figDir,customJSON,customCSV,customNotes={},rawBinary,staticFigures,originalParameters,effectiveParameters,parameterSources={},specialParameters,processEvidence,sourcePayload,scalarIndexPath},
 start=AbsoluteTime[];run=Lookup[pin,"selected_run_id",None];
 If[!StringQ[run]||!StringMatchQ[run,RegularExpression["[A-Za-z0-9_-]+"]],Throw["invalid_run_id"]];
 source=FileNameJoin[{ceRoot,"outputs",run}];ceRouteDir=FileNameJoin[{ceDir,"routes",route}];
 If[FileExistsQ[FileNameJoin[{ceRouteDir,"export_metadata.json"}]],If[KeyExistsQ[ceManifest["routes"],route],Print["Already exported: ",route];Return[Null],Throw["incomplete_existing_route_export_use_new_bundle"]]];
 CreateDirectory[FileNameJoin[{ceRouteDir,"arrays"}],CreateIntermediateDirectories->True];
 ceAssets={};ceRoundTrips={};ceJSONRTCount=0;ceJSONRTAbs=0.;ceJSONRTRel=0.;ceJSONRTNorm=0.;result=ceRead[FileNameJoin[{source,"results.json"}]];test=ceRead[FileNameJoin[{source,"test_report.json"}]];process=ceRead[FileNameJoin[{source,"process_status.json"}]];
 wxf=FileNameJoin[{source,"results.wxf"}];
 (* Inventory every original child artifact including cases, Ansys fields/meshes/source
    files and archived CPU_model/GPU_solution WXF. These binaries are not imported. *)
 files=ceOriginalFiles[source];
 rawManifest=ceRead[FileNameJoin[{source,"run_manifest.json"}]];
 ceSnapshotPaths=FileNameJoin[{source,"source_snapshot",Lookup[#,"path",""]}]&/@Lookup[rawManifest,"sources",{}];
 If[AnyTrue[ceSnapshotPaths,!FileExistsQ[#]&],Throw["missing_source_snapshot"]];
 If[!And@@MapThread[ToLowerCase[FileHash[#1,"SHA256","HexString"]]===ToLowerCase[Lookup[#2,"sha256",""]]&,{ceSnapshotPaths,Lookup[rawManifest,"sources",{}]}],Throw["original_source_snapshot_hash_mismatch"]];
 If[AnyTrue[files,cePointerQ],Throw["unresolved_LFS_pointer"]];
 sources=ceSourceRecord/@DeleteDuplicates[files];
 processEvidence=Lookup[pin,"process_evidence",Null];
 If[AssociationQ[processEvidence],With[{evidencePath=FileNameJoin[{ceRoot,Sequence@@StringSplit[processEvidence["path"],"/"]}]},If[!FileExistsQ[evidencePath]||ToLowerCase[FileHash[evidencePath,"SHA256","HexString"]]=!=ToLowerCase[processEvidence["sha256"]],Throw["pinned_process_evidence_hash_mismatch"]]]];
 rawBinary=Select[sources,!MemberQ[{"json","csv","svg","png","jpg","jpeg","md","txt","log"},ToLowerCase[FileExtension[#["path"]]]]&];
 payload=If[FileExistsQ[wxf],Needs["NDSolve`FEM`"];Quiet[Check[Import[wxf,"WXF"],$Failed]],result];
 If[!AssociationQ[payload]||Length[payload]==0,Throw["missing_or_invalid_source_data"]];
 converted=ceConvert[Lookup[payload,"data",payload],"data"];ceJSON[FileNameJoin[{ceRouteDir,"data.json"}],converted];
 sourcePayload=If[FileExistsQ[wxf],wxf,FileNameJoin[{source,"results.json"}]];
 ceScalarItems={};ceVectorReferences={};ceScalarContext=<|"cached_file"->ceOutRel[FileNameJoin[{ceRouteDir,"data.json"}]],"source_file"->ceRel[sourcePayload],"source_sha256"->FileHash[sourcePayload,"SHA256","HexString"]|>;ceScalarWalk[converted,"data"];
 ceRTJSON[converted,ceRead[FileNameJoin[{ceRouteDir,"data.json"}]],"data"];
 ceJSON[FileNameJoin[{ceRouteDir,"numerical_roundtrip.json"}],<|"schema_version"->1,"route"->route,"run_id"->run,"source_index_sha256"->ceIndexHash,"source_payload_path"->If[FileExistsQ[wxf],ceRel[wxf],ceRel[FileNameJoin[{source,"results.json"}]]],"source_payload_sha256"->FileHash[If[FileExistsQ[wxf],wxf,FileNameJoin[{source,"results.json"}]],"SHA256","HexString"],"solver_executed"->False,"physical_acceptance_status"->"not_applicable_serialization_check","passed"->True,"arrays"->ceRoundTrips,"JSON_scalar_readback"-><|"passed"->True,"numeric_scalars_compared"->ceJSONRTCount,"maximum_absolute_error"->ceJSONRTAbs,"maximum_relative_error"->ceJSONRTRel,"maximum_normalized_error"->ceJSONRTNorm,"absolute_tolerance"->ceRTAbs,"relative_tolerance"->ceRTRel,"keys_and_list_lengths_verified"->True|>|>];
 originalParameters=ceRead[FileNameJoin[{source,"parameters.json"}]];effectiveParameters=If[AssociationQ[originalParameters],originalParameters,<||>];
 If[FileExistsQ[FileNameJoin[{source,"parameters.json"}]],AppendTo[parameterSources,ceSourceRecord[FileNameJoin[{source,"parameters.json"}]]]];
 Do[If[FileExistsQ[FileNameJoin[{source,specialName}]],specialParameters=ceRead[FileNameJoin[{source,specialName}]];If[AssociationQ[specialParameters],effectiveParameters=Join[effectiveParameters,specialParameters];AppendTo[parameterSources,ceSourceRecord[FileNameJoin[{source,specialName}]]]]],{specialName,{"closure_peec_parameters.json","closure_rt0_parameters.json"}}];
 If[KeyExistsQ[effectiveParameters,"net_transport_current_RMS_A"],AssociateTo[effectiveParameters,<|"current_RMS_A"->effectiveParameters["net_transport_current_RMS_A"],"total_current_RMS_A"->effectiveParameters["net_transport_current_RMS_A"],"excitation"->"independent_imposed_field_zero_net_transport","Rac_from_P_over_I2"->"not_applicable; loss is absorbed field power"|>]];
 ceJSON[FileNameJoin[{ceRouteDir,"checks.json"}],test];ceJSON[FileNameJoin[{ceRouteDir,"parameters.json"}],originalParameters];ceJSON[FileNameJoin[{ceRouteDir,"effective_parameters.json"}],<|"parameters"->effectiveParameters,"source_files"->parameterSources,"precedence"->"dedicated closure physics parameters supersede generic wrapper parameters; originals remain unchanged"|>];
 If[FileExistsQ[FileNameJoin[{source,"model_assumptions.md"}]],CopyFile[FileNameJoin[{source,"model_assumptions.md"}],FileNameJoin[{ceRouteDir,"model_assumptions.md"}]]];
 staticFigures=Select[files,MemberQ[{"svg","png","jpg","jpeg"},ToLowerCase[FileExtension[#]]]&&!StringContainsQ[StringReplace[#,"\\"->"/"],"/source_snapshot/"]&];
 Scan[Function[p,With[{relative=FileNameDrop[p,FileNameDepth[source]]},With[{target=FileNameJoin[{ceRouteDir,"figures",relative}]},If[!DirectoryQ[DirectoryName[target]],CreateDirectory[DirectoryName[target],CreateIntermediateDirectories->True]];CopyFile[p,target];AppendTo[ceAssets,ceAsset[target,"preserved_figure",<|"source_path"->ceRel[p]|>]]]]],staticFigures];
 (* Preserve custom numerical outputs too; do not publish raw machine environment. *)
 customJSON=Select[files,ToLowerCase[FileExtension[#]]==="json"&&ceCustomQ[#,source]&];
 customCSV=Select[files,ToLowerCase[FileExtension[#]]==="csv"&&ceCustomQ[#,source]&];
 Scan[Function[p,With[{target=FileNameJoin[{ceRouteDir,"custom",FileNameDrop[p,FileNameDepth[source]]}]},If[!DirectoryQ[DirectoryName[target]],CreateDirectory[DirectoryName[target],CreateIntermediateDirectories->True]];CopyFile[p,target];
  If[ToLowerCase[FileExtension[p]]==="json"&&Quiet[Check[Import[p,"RawJSON"],$Failed]]===$Failed,
   AppendTo[customNotes,<|"path"->ceOutRel[target],"status"->"not_exportable_as_JSON","reason"->"original custom JSON is unparseable; exact bytes retained"|>];AppendTo[ceAssets,ceAsset[target,"preserved_unparseable_original",<|"source_path"->ceRel[p]|>]],AppendTo[ceAssets,ceAsset[target,"preserved_custom_data",<|"source_path"->ceRel[p],"source_relative_path"->StringReplace[FileNameDrop[p,FileNameDepth[source]],"\\"->"/"]|>]];
    If[ToLowerCase[FileExtension[p]]==="json",ceScalarContext=<|"cached_file"->ceOutRel[target],"source_file"->ceRel[p],"source_sha256"->FileHash[p,"SHA256","HexString"]|>;ceScalarWalk[Import[p,"RawJSON"],"custom"]]]]],Join[customJSON,customCSV]];
 scalarIndexPath=FileNameJoin[{ceRouteDir,"scalar_index.json"}];ceJSON[scalarIndexPath,<|"schema_version"->1,"route"->route,"run_id"->run,"source_index_sha256"->ceIndexHash,"scope"->"complete scalar/annotation leaves from converted primary data and every parseable custom JSON; numeric arrays reference complete cached data","scalar_count"->Length[ceScalarItems],"numeric_scalar_count"->Count[Lookup[ceScalarItems,"kind"],"numeric_scalar"],"scalars"->ceScalarItems,"array_references"->ceVectorReferences,"solver_executed"->False|>];
 meta=<|"schema_version"->1,"route"->route,"run_id"->run,"source_model"->Lookup[result,"source_model",Lookup[pin,"source_model",route]],"execution_status"->Lookup[pin,"execution_status",Lookup[result,"execution_status","unknown"]],"physical_acceptance_status"->Lookup[pin,"physical_acceptance_status",Lookup[result,"physical_acceptance_status","unknown"]],"process_exit"->Lookup[process,"process_exit_code",Null],"failure_reason"->Lookup[pin,"failure_reason",Lookup[result,"failure_reason",Null]],"export_status"->If[FileExistsQ[wxf],"exported","json_only"],"source_index_sha256"->ceIndexHash,"source_files"->sources,"metrics"->KeyTake[result,{"elapsed_seconds","check_count","failed_checks"}],"data"->ceOutRel[FileNameJoin[{ceRouteDir,"data.json"}]],"unit_policy"->"SI only when the source key explicitly declares units; model coordinates and unnamed fields retain unspecified units","conversion_seconds"->(AbsoluteTime[]-start),"solver_executed"->False,"field_sampling"->"preserved interpolants at preserved mesh nodes only","custom_export_notes"->customNotes,"assets"->ceAssets|>;
 AssociateTo[meta,<|"retained_original_binary_files"->rawBinary,"source_inventory_policy"->"recursive_original_files","numerical_roundtrip_required"->True,"numerical_roundtrip"->ceOutRel[FileNameJoin[{ceRouteDir,"numerical_roundtrip.json"}]],"original_binary_policy"->"All recursively inventoried binary source artifacts remain at their hashed original archive paths; only results.wxf is converted. No CPU_model/GPU_solution or dense operator re-solve/expansion.","pinned_process_exit"->Lookup[pin,"process_exit",Null],"pinned_process_evidence"->processEvidence,"effective_parameters"->effectiveParameters,"effective_parameter_sources"->parameterSources,"scalar_index"->ceOutRel[scalarIndexPath],"scalar_count"->Length[ceScalarItems],"CPU_thread_limit"->ceCPUThreadLimit,"maximum_array_elements_for_CSV"->ceMaximumArrayElements,"original_result_execution_status"->Lookup[result,"execution_status","not_recorded"],"original_result_physical_acceptance_status"->Lookup[result,"physical_acceptance_status","not_recorded"]|>];
 Scan[Function[key,If[KeyExistsQ[pin,key]||KeyExistsQ[result,key],AssociateTo[meta,key->Lookup[pin,key,Lookup[result,key,Null]]]]],{"scalar_validation_status","full_physical_acceptance","full_physical_acceptance_status","scientific_execution_status","scientific_acceptance_status"}];
 ceJSON[FileNameJoin[{ceRouteDir,"export_metadata.json"}],meta];
 Scan[Function[p,If[!AnyTrue[ceAssets,#["path"]===ceOutRel[p]&],AppendTo[ceAssets,ceAsset[p,"metadata_or_scalar_data"]]]],Select[FileNames["*",ceRouteDir],FileExistsQ[#]&&!DirectoryQ[#]&]];
 AssociateTo[ceManifest,"routes"->Append[ceManifest["routes"],route-><|"run_id"->run,"export_status"->meta["export_status"],"metadata"->ceOutRel[FileNameJoin[{ceRouteDir,"export_metadata.json"}]],"assets"->ceAssets,"solver_executed"->False|>]];
 ceJSON[ceManifestPath,ceManifest];Print["EXPORTED ",route," ",run," seconds=",AbsoluteTime[]-start];
 Clear[payload,converted];ClearSystemCache[];
];
ceRequested=Environment["LITZ_CLOSURE_ROUTE"];
ceRoutes=If[StringQ[ceRequested]&&ceRequested=!=""&&ceRequested=!="all",{ceRequested},Keys[cePins]];
If[!AllTrue[ceRoutes,KeyExistsQ[cePins,#]&],Print["Unpinned route requested"];Exit[2]];
ceErrors={};
Do[Print["START EXPORT ",ceRoute];ceError=Catch[ceExportRoute[ceRoute,cePins[ceRoute]]];If[StringQ[ceError],AppendTo[ceErrors,<|"route"->ceRoute,"failure"->ceError|>];Print["FAILED ",ceRoute," ",ceError]],{ceRoute,ceRoutes}];
ceJSON[FileNameJoin[{ceDir,"export_completion.json"}],<|"requested_routes"->ceRoutes,"failures"->ceErrors,"solver_executed"->False,"process_exit_evidence"->"caller must record the actual child process exit code separately"|>];
Exit[If[Length[ceErrors]==0,0,1]];
