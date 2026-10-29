Function[{Typed[rp,"CArray"::["Integer64"]],Typed[ci,"CArray"::["Integer64"]],Typed[ar,"CArray"::["Real64"]],Typed[ai,"CArray"::["Real64"]],Typed[xr,"CArray"::["Real64"]],Typed[xi,"CArray"::["Real64"]],Typed[yr,"CArray"::["Real64"]],Typed[yi,"CArray"::["Real64"]],Typed[n,"MachineInteger"]},
 Module[{row,k,last,col,sr=0.,si=0.,vr=0.,vi=0.,br=0.,bi=0.},
 row=LibraryFunction["BlockDimensions.x"][] LibraryFunction["BlockID.x"][]+LibraryFunction["ThreadID.x"][];
 If[row<n,k=FromRawPointer[rp,row];last=FromRawPointer[rp,row+1];
 While[k<last,col=FromRawPointer[ci,k];vr=FromRawPointer[ar,k];vi=FromRawPointer[ai,k];br=FromRawPointer[xr,col];bi=FromRawPointer[xi,col];sr=sr+vr br-vi bi;si=si+vr bi+vi br;k=k+1];
 ToRawPointer[yr,row,sr];ToRawPointer[yi,row,si]];
 ]]
