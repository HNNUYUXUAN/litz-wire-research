"""Generate bilingual editable templates using the manuscript layout renderer."""
from pathlib import Path
import sys, shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/publication'))
from ScholarlyLatex import render, LAYOUTS
from PublicationManuscripts import tex_escape, reference_text
from litz_research.references import publication_references

def main():
    refs=publication_references(ROOT,['BESSEL'])
    for lang in ['en','zh-CN']:
        zh=lang=='zh-CN'; folder=ROOT/'latex/templates'/lang; folder.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'latex/IEEEtran.cls',folder/'IEEEtran.cls')
        d=dict(language=lang,form='merged',title='研究论文模板' if zh else 'Research manuscript template',author='作者姓名' if zh else 'Author name',affiliation='单位名称' if zh else 'Institution',references=['BESSEL'],citation_keys=['BESSEL'])
        d['cells']=[dict(type='heading',text='摘要' if zh else 'Abstract'),dict(type='text',text='概述研究问题、方法、主要结果和适用范围。' if zh else 'Summarize the question, method, principal findings and scope.'),dict(type='text',text='关键词：模型；验证' if zh else 'Keywords: modeling; validation'),dict(type='heading',level=1,tag='chapter-01',text='1 方法' if zh else '1 Methods'),dict(type='text',text='使用 SI 单位和 RMS 相量。圆线解的特殊函数定义见文献 [1]。' if zh else 'Use SI units and RMS phasors. Reference [1] defines the special functions used by the round-wire solution.'),dict(type='equation'),dict(type='table',title='符号及单位' if zh else 'Symbols and units',rows=[['Symbol','Unit'],['f','Hz'],['σ','S/m']]),dict(type='heading',level=1,tag='chapter-02',text='2 结果与讨论' if zh else '2 Results and discussion'),dict(type='text',text='将图件替换为可追溯的研究结果，说明比较条件、误差与结论。' if zh else 'Replace the illustration with traceable results and explain comparison conditions, errors and conclusions.')]
        for layout in LAYOUTS:
            text=render({'references':refs},d,layout,tex_escape,lambda c:r'\begin{equation}\delta=\frac{1}{\sqrt{\pi f\mu\sigma}}\label{eq:skin}\end{equation}',reference_text)
            caption='图件位置示例；请替换为实际结果。' if zh else 'Figure placement example; replace with actual results.'
            figure=r'\begin{figure}[!htbp]\centering\fbox{\rule{0pt}{22mm}\rule{.8\linewidth}{0pt}}\caption{'+caption+r'}\label{fig:example}\end{figure}'
            text=text.replace(r'\begin{thebibliography}',figure+'\n'+r'\begin{thebibliography}')
            (folder/(layout+'.tex')).write_text(text,encoding='utf-8')
    for lang in ['en','zh-CN']:
        zh=lang=='zh-CN'
        text=('# 可独立编译的 LaTeX 模板\n\n每种语言含 single、ieee-journal、ieee-conference 三种模板。使用 XeLaTeX 编译；在所选语言目录执行 `latexmk -xelatex single.tex`。需要宋体与 Times New Roman。作者和单位为待填写字段；示例公式采用 SI 单位。题录来自项目统一文献库。\n\n' if zh else '# Standalone LaTeX templates\n\nEach language includes single, ieee-journal and ieee-conference templates. Compile with XeLaTeX: run `latexmk -xelatex single.tex` in the chosen language directory. SimSun and Times New Roman are required. Replace the author and institution fields. The example uses SI units and a reference from the canonical library.\n\n')
        text+='[English](README.md) · [简体中文](README.zh-CN.md)\n'
        (ROOT/'latex/templates'/('README.zh-CN.md' if zh else 'README.md')).write_text(text,encoding='utf-8')

if __name__=='__main__':main()
