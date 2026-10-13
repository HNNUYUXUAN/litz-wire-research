BeginPackage["LitzPublication`"];
PublicationText::usage="PublicationText[text,size] explicitly separates SimSun and Times New Roman runs.";
PublicationTextData::usage="PublicationTextData[text,size] returns native mixed-font TextData.";
PublicationStylesheet::usage="PublicationStylesheet[] returns an embedded, portable publication stylesheet.";
PublicationPlotOptions::usage="PublicationPlotOptions[] gives common physical-size plot settings.";
PublicationMagnitudeColor::usage="Sequential magnitude palette, light to dark blue.";
PublicationPhaseColor::usage="Closed cyclic phase palette.";
PublicationFormula::usage="PublicationFormula[held] creates a static TraditionalForm cell.";
Begin["`Private`"];
cjkQ[c_String]:=With[{n=First[ToCharacterCode[c]]},12288<=n<=65535];
fontRuns[s_]:=SplitBy[Characters[ToString[s]],cjkQ];
PublicationText[s_,size_:10,color_:GrayLevel[.12]]:=Style[Row[(Style[StringJoin[#],FontFamily->If[cjkQ[First[#]],"SimSun","Times New Roman"]]&/@fontRuns[s])],FontSize->size,FontColor->color];
PublicationTextData[s_,size_:12]:=TextData[(StyleBox[StringJoin[#],FontFamily->If[cjkQ[First[#]],"SimSun","Times New Roman"],FontSize->size]&/@fontRuns[s])];
PublicationMagnitudeColor[t_?NumericQ]:=Blend[{RGBColor[.95,.98,1],RGBColor[.55,.76,.88],RGBColor[.13,.40,.64],RGBColor[.025,.12,.30]},Clip[t,{0,1}]];
PublicationPhaseColor[t_?NumericQ]:=Blend[{RGBColor[.32,.13,.46],RGBColor[.14,.51,.62],RGBColor[.90,.85,.59],RGBColor[.76,.31,.25],RGBColor[.32,.13,.46]},Mod[t,1]];
PublicationPlotOptions[]:={Frame->True,Axes->False,FrameStyle->Directive[GrayLevel[.22],AbsoluteThickness[.65]],BaseStyle->{FontFamily->"Times New Roman",FontSize->10},ImageSize->252,ImagePadding->{{48,14},{37,12}},Background->White,PlotRangePadding->Scaled[.025]};
PublicationFormula[expr_]:=Cell[BoxData[ToBoxes[expr,TraditionalForm]],"DisplayFormula",Evaluatable->False,CellTags->"formula",FontFamily->"Times New Roman"];
PublicationStylesheet[]:=Notebook[{
 Cell[StyleData[StyleDefinitions->"Article/JournalArticle.nb"]],
 Cell[StyleData[All],FontFamily->"Times New Roman",FontColor->GrayLevel[.12]],
 Cell[StyleData["Notebook"],Background->White,PageWidth->760,CellLabelAutoDelete->True],
 Cell[StyleData["Title"],FontSize->24,FontWeight->"Plain",TextAlignment->Left,FontColor->RGBColor[.08,.17,.30],CellMargins->{{36,36},{12,20}}],
 Cell[StyleData["Subtitle"],FontSize->11,FontSlant->"Plain",FontColor->GrayLevel[.38],CellMargins->{{36,36},{12,0}}],
 Cell[StyleData["Section"],FontSize->16,FontWeight->"Bold",TextAlignment->Left,FontColor->RGBColor[.08,.17,.30],CellMargins->{{36,36},{8,20}}],
 Cell[StyleData["Subsection"],FontSize->13,FontWeight->"Bold",FontColor->GrayLevel[.15],CellMargins->{{36,36},{6,14}}],
 Cell[StyleData["Text"],FontSize->12,LineSpacing->{1.45,0},CellMargins->{{36,36},{6,5}}],
 Cell[StyleData["DisplayFormula"],FontSize->13,CellMargins->{{54,36},{9,9}},TextAlignment->Center],
 Cell[StyleData["Output"],FontSize->10,CellMargins->{{36,36},{6,6}},CellLabelAutoDelete->True],
 Cell[StyleData["Caption"],FontSize->10,LineSpacing->{1.3,0},CellMargins->{{36,36},{12,3}}],
 Cell[StyleData["FigureTitle"],FontSize->10,TextAlignment->Center,LineSpacing->{1.3,0},CellMargins->{{36,36},{4,3}}],
 Cell[StyleData["FigureDescription"],FontSize->10,TextAlignment->Left,LineSpacing->{1.3,0},CellMargins->{{36,36},{12,3}}],
 Cell[StyleData["Reference"],FontSize->10,LineSpacing->{1.2,0},CellMargins->{{36,36},{4,2}}]
},Visible->False];
End[];EndPackage[];
