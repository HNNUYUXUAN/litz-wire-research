Function[{Typed[o,"CArray"::["Real64"]],Typed[x,"CArray"::["Real64"]],Typed[y,"CArray"::["Real64"]],Typed[n,"MachineInteger"],Typed[start,"MachineInteger"],Typed[count,"MachineInteger"],Typed[len,"Real64"]},
 Module[{tid,k,r,c,dx=0.,dy=0.,d=0.,val=0.},
 tid=LibraryFunction["BlockDimensions.x"][] LibraryFunction["BlockID.x"][]+LibraryFunction["ThreadID.x"][];
 If[tid<count,k=start+tid;r=Quotient[k,n];c=Mod[k,n];
 If[r!=c,dx=FromRawPointer[x,r]-FromRawPointer[x,c];dy=FromRawPointer[y,r]-FromRawPointer[y,c];d=Sqrt[dx dx+dy dy];val=2.*^-7 (len Log[len/d+Sqrt[1.+(len/d)^2]]-Sqrt[len len+d*d]+d)];ToRawPointer[o,tid,val]];
 ]]
