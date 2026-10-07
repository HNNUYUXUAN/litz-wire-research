(* Wolfram Language -> CUDA/PTX, FP64 transform with a non-block-aligned tail. *)
Function[{Typed[x, "CArray"::["Real64"]], Typed[n, "MachineInteger"]},
  Module[{id},
    id = LibraryFunction["BlockDimensions.x"][] * LibraryFunction["BlockID.x"][] + LibraryFunction["ThreadID.x"][];
    If[id < n, ToRawPointer[x, id, 2.0 FromRawPointer[x, id] + 1.0]];
  ]
]
