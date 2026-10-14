"""Build bilingual editable overview diagrams and inspectable layout candidates."""
from pathlib import Path
import json,hashlib,html

ROOT=Path(__file__).resolve().parents[1]
PALETTES=[('#31556a','#b57043','#f2f6f8'),('#294956','#ad784c','#f8f5f0'),('#3b5264','#a8623a','#f5f7f8')]
DIAGRAMS={
 'connections':{
 'title':('从研究任务到可复核产物','From research task to reviewable artifacts'),
 'subtitle':('工作流组织任务 · MCP 连接工具 · 运行器保存证据','Workflows organize tasks · MCP connects tools · Runners preserve evidence'),
 'nodes':[
 ('task',80,155,290,95,'研究问题与物理约定','Question and constraints','参数 · 模型 · 验收门槛','Parameters · model · acceptance'),
 ('agent',455,155,290,95,'Codex / MCP 客户端','Codex / MCP client','读取工作流 · 编辑源码','Read workflows · edit source'),
 ('tools',830,155,290,95,'Wolfram / Ansys MCP','Wolfram / Ansys MCP','工具发现 · 调用与返回','Discover · invoke · read back'),
 ('source',80,365,290,95,'物理模型与保存输入','Models and saved inputs','源码身份 · SI 与 RMS','Source identity · SI and RMS'),
 ('runner',455,365,290,95,'受控运行器','Bounded runner','任务号 · 资源 · 日志','Run ID · resources · logs'),
 ('evidence',830,365,290,95,'结果与独立验收','Results and acceptance','数值 · 图件 · 稿件','Values · figures · manuscripts')],
 'edges':[('task','agent'),('agent','tools'),('agent','source'),('source','runner'),('tools','runner'),('runner','evidence')]},
 'research-loop':{
 'title':('可接续的自动化研究循环','A research loop that can be continued'),
 'subtitle':('每次修订对应保存输入、源码差异和新的运行身份','Every revision retains inputs, a source difference, and a new run identity'),
 'nodes':[
 ('question',80,160,290,95,'定义问题','Define the question','工况 · 比较量 · 容差','Conditions · observables · tolerance'),
 ('model',455,160,290,95,'建立或扩展模型','Build or extend the model','推导 · 源码 · 针对性测试','Derivation · source · targeted tests'),
 ('run',830,160,290,95,'执行任务','Execute the task','MCP · CLI · Notebook','MCP · CLI · Notebook'),
 ('next',80,365,290,95,'整理结果与后续问题','Results and next questions','引用 · 适用范围 · 研究入口','Citations · scope · research entry'),
 ('revise',455,365,290,95,'解释与修订','Interpret and revise','错误依据 · 修订记录','Error evidence · revision record'),
 ('check',830,365,290,95,'读取结果并验收','Read results and check','电流 · 功率 · 敏感性','Current · power · sensitivity')],
 'edges':[('question','model'),('model','run'),('run','check'),('check','revise'),('revise','next'),('revise','model')]},
 'model-hierarchy':{
 'title':('七条模型路线与各自的观测量','Seven modeling routes and their observables'),
 'subtitle':('根据问题选择自由度、激励与边界条件','Choose degrees of freedom, excitation, and boundaries for the question'),
 'nodes':[
 ('analytic',65,145,330,90,'解析圆线','Analytical round wire','Bessel · 内部阻抗与径向电流','Bessel · internal impedance · radial J'),
 ('fem',435,145,330,90,'二维 FEM','Two-dimensional FEM','内场校准 · 网格与功率','Internal-field calibration · mesh · power'),
 ('common',805,145,330,90,'多股共端场路','Common-terminal coupling','共同电压 · 逐股复电流','Common voltage · complex strand currents'),
 ('geometry',65,275,330,90,'股线几何','Strand geometry','身份 · 换位 · 弧长与铜体积','Identity · transposition · length · volume'),
 ('peec',435,275,330,90,'有限长度 PEEC','Finite-length PEEC','纵向电流 · 长度与积分敏感性','Axial currents · length · quadrature'),
 ('rt0',805,275,330,90,'三分量 RT0','Three-component RT0','面通量 · 连续性 · 外场吸收','Face flux · continuity · field absorption'),
 ('aphi',435,405,330,90,'三维 A–φ','Three-dimensional A–φ','场势诊断 · 规范残差','Field–potential diagnostics · gauge')],
 'edges':[]},
 'cross-solver':{
 'title':('Wolfram—Maxwell 共同端口比较','Wolfram–Maxwell common-port comparison'),
 'subtitle':('七股直束 · 受控铜回流 · 共同端电压与总电流','Seven straight strands · controlled copper return · common voltage and total current'),
 'nodes':[
 ('inputs',360,130,480,90,'对齐输入与观测量','Align inputs and observables','几何 · 材料 · 频率 · RMS · 边界','Geometry · material · frequency · RMS · boundaries'),
 ('wolfram',90,290,430,90,'Wolfram 场路实现','Wolfram field–circuit model','独立网格与求解记录','Independent mesh and solution record'),
 ('maxwell',680,290,430,90,'Maxwell 原生模型','Native Maxwell model','MCP → PyAEDT → AEDT','MCP → PyAEDT → AEDT'),
 ('compare',360,455,480,90,'复电流 · 损耗 · Rac · 数值范围','Complex currents · loss · Rac · numerical scope','相同定义下比较，结合网格与边界敏感性解释','Compare like quantities; interpret mesh and boundary sensitivity')],
 'edges':[('inputs','wolfram'),('inputs','maxwell'),('wolfram','compare'),('maxwell','compare')]}
}

def render(key,lang,variant):
    d=DIAGRAMS[key];zh=lang=='zh-CN';blue,copper,fill=PALETTES[variant];height=600
    esc=html.escape
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',f'<title id="title">{esc(d["title"][0 if zh else 1])}</title>',f'<desc id="desc">{esc(d["subtitle"][0 if zh else 1])}</desc>',f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{blue}"/></marker></defs>', '<rect width="1200" height="600" fill="white"/>']
    def text(x,y,value,size=20,color=blue,weight='normal'):
        out.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,Microsoft YaHei,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{esc(value)}</text>')
    text(600,57,d['title'][0 if zh else 1],32,weight='bold');text(600,95,d['subtitle'][0 if zh else 1],17)
    nodes={n[0]:n for n in d['nodes']}
    for a,b in d['edges']:
        _,x,y,w,h,*_=nodes[a];_,xx,yy,ww,hh,*_=nodes[b]
        if y==yy:
            start=(x+w,y+h/2) if xx>x else (x,y+h/2);end=(xx,yy+hh/2) if xx>x else (xx+ww,yy+hh/2)
        else:
            start=(x+w/2,y+h) if yy>y else (x+w/2,y);end=(xx+ww/2,yy) if yy>y else (xx+ww/2,yy+hh)
        out.append(f'<path d="M{start[0]},{start[1]} L{end[0]},{end[1]}" stroke="{blue}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
    for _,x,y,w,h,z,e,sz,se in d['nodes']:
        radius=[10,0,22][variant]
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{blue}" stroke-width="1.5"/>')
        out.append(f'<path d="M{x+20},{y+17} H{x+60}" stroke="{copper}" stroke-width="4"/>')
        text(x+w/2,y+43,z if zh else e,21 if zh else 19,weight='bold');text(x+w/2,y+70,sz if zh else se,15 if zh else 13)
    out.append('</svg>');return '\n'.join(out)+'\n'

def main():
    records=[]
    for key in DIAGRAMS:
        for variant in range(3):
            for lang in ('en','zh-CN'):
                content=render(key,lang,variant)
                p=ROOT/'outputs/review/visual-candidates'/f'{key}-{lang}-{variant+1}.svg';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')
                records.append(dict(theme=key,language=lang,variant=variant+1,path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(content.encode()).hexdigest(),selected=variant==0))
                if variant==0:
                    dest=ROOT/'publications/assets/overview'/lang/(key+'.svg');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content,encoding='utf-8')
    target=ROOT/'provenance/editorial/vector-visuals.json';target.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(records)} bilingual candidate assets; eight selected SVG diagrams.')
if __name__=='__main__':main()
