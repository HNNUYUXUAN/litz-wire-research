"""Render the editable evidence report to a Chinese PDF; no network or TeX."""
from pathlib import Path
import argparse, html, re, os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def render(source, target, font):
    pdfmetrics.registerFont(TTFont('EvidenceChinese',str(font),subfontIndex=0))
    styles=getSampleStyleSheet()
    for name in ('Normal','Title','Heading1','Heading2','Heading3'):
        styles[name].fontName='EvidenceChinese'
        styles[name].wordWrap='CJK'
    styles['Normal'].fontSize=10; styles['Normal'].leading=16
    styles['Normal'].spaceAfter=7
    styles['Title'].fontSize=19; styles['Title'].leading=27
    styles['Heading1'].fontSize=15; styles['Heading1'].leading=22
    styles['Heading2'].fontSize=12; styles['Heading2'].leading=19
    small=ParagraphStyle('EvidenceTable',parent=styles['Normal'],fontSize=8,leading=12,spaceAfter=0)
    def clean(text):
        text=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',text)
        text=text.replace('`','').replace('**','')
        return html.escape(text)
    lines=source.read_text(encoding='utf-8-sig').splitlines(); story=[]; i=0
    while i<len(lines):
        line=lines[i].strip(); i+=1
        if not line: continue
        if line.startswith('|'):
            rows=[]
            while True:
                if not re.match(r'^\|[\s:|\-]+\|?$',line):
                    rows.append([Paragraph(clean(v.strip()),small) for v in line.strip('|').split('|')])
                if i>=len(lines) or not lines[i].strip().startswith('|'): break
                line=lines[i].strip(); i+=1
            if rows:
                n=max(map(len,rows)); rows=[r+[Paragraph('',small)]*(n-len(r)) for r in rows]
                table=Table(rows,colWidths=[(A4[0]-88)/n]*n,repeatRows=1,hAlign='LEFT')
                table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef5')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b9c5d2')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
                story.extend([table,Spacer(1,10)])
            continue
        if line.startswith('```'): continue
        level=len(line)-len(line.lstrip('#'))
        style=styles['Title' if level==1 else 'Heading1' if level==2 else 'Heading2' if level>=3 else 'Normal']
        text=line[level:].strip() if level else line
        if text.startswith('- '): text='• '+text[2:]
        story.append(Paragraph(clean(text),style))
    def footer(canvas,doc):
        canvas.setFont('EvidenceChinese',8)
        canvas.setFillColor(colors.HexColor('#536478'))
        canvas.drawString(44,25,'Litz 本地证据报告 · 2026-10-05 · 未完成项按实记录')
        canvas.drawRightString(A4[0]-44,25,str(doc.page))
    target.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(target),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=42,bottomMargin=44,title='Litz 四题解答与三维验收记录',author='项目本地证据汇编').build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('target',type=Path)
    p.add_argument('--font',type=Path,default=Path(os.getenv('LITZ_CJK_FONT',str(Path(os.environ.get('WINDIR','/usr/share/fonts'))/'Fonts/simsun.ttc'))))
    a=p.parse_args();render(a.source,a.target,a.font)
