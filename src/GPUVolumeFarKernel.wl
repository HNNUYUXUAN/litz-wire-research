Function[{Typed[o,"CArray"::["Real64"]],Typed[x,"CArray"::["Real64"]],Typed[y,"CArray"::["Real64"]],Typed[qx,"CArray"::["Real64"]],Typed[qy,"CArray"::["Real64"]],Typed[qw,"CArray"::["Real64"]],Typed[n,"MachineInteger"],Typed[start,"MachineInteger"],Typed[count,"MachineInteger"],Typed[len,"Real64"],Typed[cut,"Real64"]},
 Module[{tid,k,r,c,a=0,b=0,dx=0.,dy=0.,d=0.,rx=0.,ry=0.,val=0.},
 tid=LibraryFunction["BlockDimensions.x"][] LibraryFunction["BlockID.x"][]+LibraryFunction["ThreadID.x"][];
 If[tid<count,k=start+tid;r=Quotient[k,n];c=Mod[k,n];dx=FromRawPointer[x,r]-FromRawPointer[x,c];dy=FromRawPointer[y,r]-FromRawPointer[y,c];
 If[dx dx+dy dy>cut cut,
  a=0;While[a<16,b=0;While[b<16,rx=dx+FromRawPointer[qx,a]-FromRawPointer[qx,b];ry=dy+FromRawPointer[qy,a]-FromRawPointer[qy,b];d=Sqrt[rx rx+ry ry];
   val=val+FromRawPointer[qw,a] FromRawPointer[qw,b] 2.*^-7 (len Log[len/d+Sqrt[1.+(len/d)^2]]-Sqrt[len len+d*d]+d);b=b+1];a=a+1]];
 ToRawPointer[o,tid,val]];
 ]]
