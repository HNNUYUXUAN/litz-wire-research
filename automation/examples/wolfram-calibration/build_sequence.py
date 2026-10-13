"""Create a portable official-Wolfram MCP calibration and Notebook sequence."""
from pathlib import Path
import argparse,json

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    root=next(x for x in Path(__file__).resolve().parents if (x/'pyproject.toml').exists())
    out=root/'outputs'/a.run_id;notebook=out/'calibration.nb'
    q=lambda x:json.dumps(str(x).replace('\\','/'))
    source=root/'models/analytic/src/Q1Analytical.wl';inputs=root/'configs/reference_parameters.json'
    helper=root/'shared/wolfram/ResearchNotebook.wl'
    code='Get['+q(helper)+'];SetEnvironment["LITZ_NOTEBOOK_RUN_ID"->'+q(a.run_id)+'];research=LitzNotebook`RunResearch['+q(root)+',"wolfram-analytic",<|"frequency_Hz"->200000.,"current_RMS_A"->20.|>];SetEnvironment["LITZ_NOTEBOOK_RUN_ID"->""];LitzNotebook`ResearchSummary[research]'
    markdown='# Round-wire calibration\n\nMiao Yuxuan / Huainan Normal University. SI; exp(+j omega t); RMS. The 2 mm wire is the Q1 calibration.\n\n```wl\nprojectRoot=NestWhile[DirectoryName,NotebookDirectory[],!FileExistsQ[FileNameJoin[{#,"pyproject.toml"}]]&&DirectoryName[#]=!=#&];\nGet[FileNameJoin[{projectRoot,"models","analytic","src","Q1Analytical.wl"}]];\np=Import[FileNameJoin[{projectRoot,"configs","reference_parameters.json"}],"RawJSON"];\nr=LitzAnalytical`RoundWireSolution[p];\nKeyTake[r,{"Rac_ohm_per_m","loss_W_per_m"}]\n```\n\n```wl\nListLinePlot[r["profile"][[All,{1,4}]],Frame->True,FrameLabel->{"r (m)","|J| (A/m^2 RMS)"}]\n```'
    calls=[{'name':'WolframLanguageContext','arguments':{'context':'Local SI/RMS isolated round wire calibration using modified Bessel functions, independent current and Joule integrals, and native Notebook creation.'}},{'name':'WolframLanguageEvaluator','arguments':{'code':code,'timeConstraint':60}},{'name':'TestReport','arguments':{'paths':str(root/'tests/Q1Analytical.wlt'),'newKernel':True}},{'name':'WriteNotebook','arguments':{'file':str(notebook),'markdown':markdown,'overwrite':False}},{'name':'ReadNotebook','arguments':{'notebook':str(notebook)}}]
    # Query the live tool schema before invoking a new upstream version.
    Path(a.output).write_text(json.dumps(calls,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
