$HistoryLength=0;$CharacterEncoding="UTF8";
req=Import[Last[Rest[$ScriptCommandLine]],"RawJSON"];
UsingFrontEnd[g=Get[req["source"]];result=Export[req["output"],g,"PDF"];pages=Import[req["output"],"PageCount"];];
Export[req["verification"],<|"passed"->(StringQ[result]&&pages==1),"source_sha256"->FileHash[req["source"],"SHA256","HexString"],"pdf_sha256"->FileHash[req["output"],"SHA256","HexString"],"physical_solver_calls"->0|>,"RawJSON"];
Exit[If[StringQ[result]&&pages==1,0,1]];
