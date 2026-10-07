(* Portable CSV exponent conversion without evaluating arbitrary cell text. *)
BeginPackage["LitzClosureCSV`"];
NumericCSV::usage="NumericCSV[path] imports finite real numeric CSV cells; a single header row is retained. Scientific e/E notation is accepted only after a strict numeric grammar check.";
Begin["`Private`"];
number[x_?NumberQ]:=x;
number[x_String]:=Module[{s=StringTrim[x]},If[StringMatchQ[s,RegularExpression["[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:(?:[eE]|\\*\\^)[+-]?[0-9]+)?"]],
 Quiet[Check[ToExpression[StringReplace[s,RegularExpression["[eE]"]->"*^"]],$Failed]],$Failed]];
number[_]:=$Failed;
NumericCSV[path_String]:=Module[{raw=Quiet[Check[Import[path,"CSV"],$Failed]],values},
 If[!ListQ[raw]||Length[raw]<2,Return[Failure["CSVRead",<|"path"->path|>]]];
 values=Map[number,Rest[raw],{2}];
 If[!MatrixQ[values,NumberQ]||!FreeQ[values,_Complex|Indeterminate|_DirectedInfinity],
  Return[Failure["CSVNumericGrammar",<|"path"->path,"reason"->"A data cell is not a finite real number."|>]]];
 <|"header"->First[raw],"data"->values|>
];
End[];EndPackage[];
