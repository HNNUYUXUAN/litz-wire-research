Get[FileNameJoin[{stageRoot,"src","Q1Analytical.wl"}]];
anP=Import[FileNameJoin[{stageRoot,"configs","reference_parameters.json"}],"RawJSON"];
anResult=LitzAnalytical`RoundWireSolution[anP];
anTest=TestReport[FileNameJoin[{stageRoot,"tests","Q1Analytical.wlt"}]];
stageCheck["Q1_12_regressions",anTest["TestsFailedCount"],0,"Bessel_50_digit_analytic"];
Export[FileNameJoin[{stageDir,"analytical_regression_report.json"}],<|"tests_succeeded"->anTest["TestsSucceededCount"],"tests_failed"->anTest["TestsFailedCount"],"tests"->Map[<|"id"->#["TestID"],"outcome"->#["Outcome"]|>&,Values[anTest["TestResults"]]]|>,"RawJSON"];
anProfile=Table[{r,Re[LitzPhysics`WireJ[r,0.001,200000.,20.]],Im[LitzPhysics`WireJ[r,0.001,200000.,20.]],Abs[LitzPhysics`WireJ[r,0.001,200000.,20.]],Arg[LitzPhysics`WireJ[r,0.001,200000.,20.]],Abs[LitzPhysics`WireJ[r,0.001,200000.,20.]]^2/(5.8*^7)},{r,0.,0.001,0.000005}];
anFreq=Table[{f,Re[LitzPhysics`WireZ[0.001,f]]/(1/(5.8*^7 Pi 0.001^2)),Im[LitzPhysics`WireZ[0.001,f]]},{f,10.^Range[0,7,.1]}];
stageData=<|"source_model"->"Bessel_50_digit_analytic","solution"->KeyDrop[anResult,"profile"],"profile"->anProfile,"frequency_sweep"->anFreq,
 "assumptions"->"Isolated infinite straight copper cylinder. Internal impedance only. No applied field. SI; exp(+j omega t); RMS. Q1 diameter 2 mm violates 4 A/mm^2 and is retained as calibration. Instantaneous current sqrt(2) Re[J exp(j phase)]."|>;
stageFigure["complex_J",ListLinePlot[Table[(#*{1000,10.^-6}&/@anProfile[[All,{1,k}]]),{k,{2,3,4}}],Frame->True,FrameLabel->{"r (mm)","J (A/mm^2)"},PlotLegends->{"Re J","Im J","Abs J"},PlotRange->All,ImageSize->600]];
stageFigure["phase",ListLinePlot[(#*{1000,180/Pi}&/@anProfile[[All,{1,5}]]),Frame->True,FrameLabel->{"r (mm)","Phase (degrees)"},ImageSize->600]];
stageFigure["Joule_density",ListLinePlot[(#*{1000,1}&/@anProfile[[All,{1,6}]]),Frame->True,FrameLabel->{"r (mm)","Joule loss (W/m^3)"},ImageSize->600]];
stageFigure["frequency",ListLogLogPlot[anFreq[[All,{1,2}]],Frame->True,FrameLabel->{"f (Hz)","Rac/Rdc"},ImageSize->600]];
Export[FileNameJoin[{stageDir,"radial_profile.csv"}],Prepend[anProfile,{"r_m","Re_J_A_m2","Im_J_A_m2","Abs_J_A_m2","phase_rad","loss_W_m3"}],"CSV"];

