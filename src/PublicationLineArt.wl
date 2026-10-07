(* Point-based line art uses explicit model relations and local font runs. *)
pubLineArt[spec_]:=Module[{s=spec["layout"],h,xy,rect,txt,icon,node,group,edge},
 h=s["height"];xy[p_]:=p;
 txt[t_,p_,size_:9.5]:=Inset[LitzPublication`PublicationText[t,size,Black],p];
 rect[b_,fill_]:={EdgeForm[Directive[Black,AbsoluteThickness[.55]]],FaceForm[fill],Rectangle[b[[1]],b[[2]]]};
 icon[type_,p_]:=Switch[type,
  "round",{Circle[p,8],Circle[p,5],Circle[p,2]},
  "mesh",{Circle[p,8],Line[{p+{-7,-4},p+{7,4}}],Line[{p+{-7,4},p+{7,-4}}],Line[{p+{0,-8},p+{0,8}}]},
  "bundle",Table[Circle[p+v,2.8],{v,{{0,0},{6,0},{-6,0},{3,5.2},{-3,5.2},{3,-5.2},{-3,-5.2}}}],
  "filaments",Table[{FaceForm[White],EdgeForm[Black],Rectangle[p+{-12,k},p+{12,k+2}],Line[{p+{8,k},p+{12,k+2}}]},{k,{-6,0,6}}],
  _,{}];
 node[n_]:=Module[{p=n["center"],z=n["size"],lines=n["lines"],withIcon=n["icon"]!="none",y},
  y=If[withIcon,p[[2]]-6,p[[2]]+(Length[lines]-1)*6];
  {rect[{p-z/2,p+z/2},White],Black,AbsoluteThickness[.6],If[withIcon,icon[n["icon"],p+{0,z[[2]]/2-13}],{}],Table[txt[lines[[k]],{p[[1]],y-12(k-1)},9.5],{k,Length[lines]}]}];
 group[g_]:={rect[g["box"],GrayLevel[.97]],txt[g["label"],{Mean[g["box"][[All,1]]],g["box"][[2,2]]-12},9.5]};
 edge[e_]:={Black,AbsoluteThickness[.6],If[e["style"]=="dashed",AbsoluteDashing[{2,2}],AbsoluteDashing[{}]],Arrowheads[.022],Arrow[e["path"]],AbsoluteDashing[{}],txt[e["label"],e["label_position"],9]};
 Graphics[{group/@s["groups"],Black,AbsoluteThickness[.65],Line/@s["wires"],node/@s["nodes"],edge/@s["edges"],Black,Disk[#,1.5]&/@s["dots"],(txt[#["text"],#["position"],#["size"]]&/@s["labels"])},PlotRange->{{0,252},{0,h}},ImagePadding->0,PlotRangePadding->0,ImageSize->{252,h},Background->White]
];
