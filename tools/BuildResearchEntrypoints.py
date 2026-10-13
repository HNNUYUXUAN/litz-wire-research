"""Generate bilingual route guides and native Notebook requests from one source."""
from pathlib import Path
import json
from litz_research.tasks import DEFAULTS

ROOT=Path(__file__).resolve().parents[1]
ROUTES=[
 ('analytic','wolfram-analytic','Round-wire analytical calibration','单圆线解析校准','∇²Ez−jωμσEz=0; Zint=κ I0(κa)/(2πaσ I1(κa))','BESSEL','Change frequency/current; compare independent current and Joule integrals.','修改频率与总电流，核对独立电流积分与焦耳积分。'),
 ('fem2','fem2','Two-dimensional diffusion FEM','二维扩散有限元','∇⊥²Ez−jωμσEz=0; Jz=σEz','FEMDOC','Change mesh_h; run at least three meshes before making a convergence claim.','修改 mesh_h；收敛判断至少运行三档网格。'),
 ('common_terminal','coax','Common-terminal current sharing','共端复电流分配','Zi+e=V1; 1ᵀi=It','P01; P02','Change strand count or return geometry; inspect complex strand currents and input/loss balance.','修改股数或回流几何；检查复电流及输入功率与损耗。'),
 ('geometry','geometry','Geometry and transposition','几何与换位','ℓi=∫√(1+x′²+y′²) dz; Rdc=(ΣσAi/ℓi)⁻¹','P01; N01','Change topology, pitch or length; inspect gaps, arc lengths and copper volume. Geometry is a model input.','修改结构、节距或长度；检查间隙、弧长与铜体积。几何是场模型的输入。'),
 ('peec','peec','Finite-length longitudinal PEEC','有限长度纵向 PEEC','Z=R+jωL; Zi=V1; 1ᵀi=It','P03','Change length or cross divisions; compare complex port constraints and power. The basis is longitudinal.','修改长度或横向离散，核对复端口约束与功率。基函数沿纵向。'),
 ('rt0','rt0','Vector RT0 volume PEEC','向量 RT0 体积 PEEC','(R+jωL)i+e=Cᵀv; Ci=b','P03','Choose field or transport excitation. The field case has 1 mT RMS imposed Bz and zero net transport.','选择外场或输运激励。外场算例为 1 mT RMS Bz、零净输运。'),
 ('aphi','aphi','Preserved A–φ field diagnostics','保存 A–φ 场诊断','J=−σ(jωA+∇φ); ∇·J=0','FEMDOC','Read actual saved fields and reproduce J, phi and gauge residuals. Original field parameters remain visible.','读取实际保存场，复算 J、电势与规范残差，保留原场参数。'),
 ('wolfram','wolfram','Wolfram environment and execution','Wolfram 环境与执行','Independent kernel execution and native frontend rendering','WOLFRAM; AGENTTOOLS','Probe the local kernel, then follow the MCP workflow for actual tool and Notebook operations.','检查本机内核，再按 MCP 工作流验收真实工具调用和 Notebook 操作。'),
 ('ansys','ansys','Ansys MCP and Maxwell workflow','Ansys MCP 与 Maxwell 工作流','Common terminal voltage and total RMS current','PYAEDTMCP; PYAEDT','Run resource preflight; execute the native seven-strand MCP example when Maxwell is available.','执行资源预检；Maxwell 可用时运行原生七股 MCP 案例。'),
 ('gpu','gpu','GPU execution and CPU comparison','GPU 执行与 CPU 对照','Same-input double-precision numerical comparison','CUDA','Run a small GPU/CPU comparison; retain toolchain and numerical error.','运行小型 GPU/CPU 对照，保存工具链和数值误差。'),
]

def main():
    requests=[];methods=json.loads((ROOT/'configs/route_methods.json').read_text(encoding='utf-8'))
    for route,model,en,zh,equation,refs,usage_en,usage_zh in ROUTES:
        home=ROOT/('adapters/'+route if route in {'wolfram','ansys','gpu'} else 'models/'+route)
        home.mkdir(parents=True,exist_ok=True);(home/'notebooks').mkdir(exist_ok=True);(home/'examples').mkdir(exist_ok=True)
        p=DEFAULTS[model];(home/'examples/tutorial.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
        metadata={'route':route,'model_id':model,'titles':{'en':en,'zh-CN':zh},'equation':equation,'references':refs.split('; '),'parameters':p,'tutorial_instructions':{'en':usage_en,'zh-CN':usage_zh},'fixed_conventions':'SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C','evidence_dataset':'common-terminal' if route=='common_terminal' else route}
        metadata['derivation']=methods[route]
        extra={'peec':['RUEHLI1974'],'rt0':['RUEHLI1974','RT1977','GMRES1986'],'aphi':['GMRES1986'],'fem2':['P04']}.get(route,[])
        metadata['references']+=extra
        metadata['history']='data/evidence/v1.0.0-rc.1/; litz-research data fetch '+('analytic' if route=='wolfram' else metadata['evidence_dataset'])
        (home/'model.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for lang,title,usage in [('en',en,usage_en),('zh-CN',zh,usage_zh)]:
            notebook=home/'notebooks'/(route+'_'+lang+'.nb')
            guide=['# '+title,'','Miao Yuxuan · Huainan Normal University','','## '+('Model and assumptions' if lang=='en' else '模型与假设'),'',equation,'',metadata['fixed_conventions'],'',usage,'','## '+('Run the tutorial' if lang=='en' else '运行教程'),'','```powershell','litz-research run '+model+' --case '+('diagnostic' if route=='aphi' else 'preflight' if route=='ansys' else 'tutorial')+' --parameters '+(home/'examples/tutorial.json').relative_to(ROOT).as_posix()+' --run-id '+route+'_example_01','```','','['+('Interactive Notebook' if lang=='en' else '交互研究 Notebook')+'](notebooks/'+notebook.name+')','','## '+('Result and acceptance' if lang=='en' else '结果与验收'),'','Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.','','## '+('Research continuation' if lang=='en' else '接续研究'),'','Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.','','## '+('Sources' if lang=='en' else '来源'),'',', '.join('['+k+']('+('../../' if route in {'wolfram','ansys','gpu'} else '../../')+'references/README.md)' for k in metadata['references']),'']
            if lang=='zh-CN':
                guide=[x.replace('Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.','读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。').replace('Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.','从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。') for x in guide]
            guide+=['## '+('Derivation and interpretation' if lang=='en' else '推导与结果解释'),'']+methods[route][lang]+['','## '+('Historical evidence' if lang=='en' else '历史证据'),'',metadata['history'],'']
            (home/('README.md' if lang=='en' else 'README.zh-CN.md')).write_text('\n'.join(guide),encoding='utf-8')
            requests.append(metadata|{'language':lang,'title':title,'usage':usage,'path':notebook.relative_to(ROOT).as_posix()})
    (ROOT/'configs/research_notebooks.json').write_text(json.dumps(requests,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Prepared',len(requests),'bilingual research Notebooks')

if __name__=='__main__':main()
