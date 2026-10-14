"""LaTeX layouts for the shared scholarly document tree."""
import re

LAYOUTS = ('single', 'ieee-journal', 'ieee-conference')


def render(manifest, document, layout, escape, equation, reference):
    layout = 'ieee-journal' if layout == 'ieee' else layout
    if layout not in LAYOUTS:
        raise ValueError('Unknown scholarly layout: ' + layout)
    ieee = layout.startswith('ieee-')
    zh = document['language'] == 'zh-CN'
    tex = [r'\documentclass[' + ('conference' if layout == 'ieee-conference' else 'journal,10pt') + r']{IEEEtran}'] if ieee else [
        r'\documentclass[11pt,a4paper]{article}',
        r'\usepackage[textwidth=182mm,top=20mm,bottom=22mm]{geometry}']
    tex += [r'\usepackage{amsmath,amssymb,newtxmath}', r'\usepackage[no-math]{fontspec}',
            r'\setmainfont{Times New Roman}', r'\usepackage{xeCJK}',
            r'\setCJKmainfont[AutoFakeBold=2]{SimSun}',
            r'\usepackage{graphicx,booktabs,array,tabularx,seqsplit,xurl,hyperref}',
            r'\hypersetup{hidelinks,unicode=true,pdftitle={' + escape(document['title']) + r'},pdfauthor={' + escape(document['author']) + r'}}',
            r'\setlength{\emergencystretch}{2em}', r'\raggedbottom',
            r'\renewcommand{\arraystretch}{1.15}']
    if not ieee:
        tex += [r'\usepackage{caption}',r'\captionsetup[figure]{font=small,justification=centering,singlelinecheck=false}',
                r'\linespread{1.16}', r'\setlength{\parindent}{2em}', r'\setlength{\parskip}{3pt plus 1pt}',
                r'\renewcommand{\topfraction}{0.92}', r'\renewcommand{\textfraction}{0.08}',
                r'\renewcommand{\floatpagefraction}{0.75}']
    if zh:
        tex += [r'\renewcommand{\figurename}{图}', r'\renewcommand{\tablename}{表}', r'\renewcommand{\abstractname}{摘要}']
    tex += [r'\begin{document}', r'\title{' + escape(document['title']) + '}']
    author, affiliation = escape(document['author']), escape(document['affiliation'])
    if layout == 'ieee-conference':
        tex += [r'\author{\IEEEauthorblockN{' + author + r'}\IEEEauthorblockA{' + affiliation + '}}']
    elif ieee:
        tex += [r'\author{' + author + r'\thanks{' + affiliation + '}}']
    else:
        tex += [r'\author{' + author + r'\\' + affiliation + '}', r'\date{}']
    tex += [r'\maketitle']
    cells = document['cells']
    if document['form'] == 'merged':
        tex += [r'\begin{abstract}', escape(cells[1]['text']), r'\end{abstract}']
        keywords = re.sub(r'^(关键词：|Keywords:\s*)', '', cells[2]['text'])
        tex += ([r'\begin{IEEEkeywords}', escape(keywords), r'\end{IEEEkeywords}'] if ieee else
                [r'\noindent\textbf{' + ('关键词：' if zh else 'Keywords: ') + '}' + escape(keywords) + r'\par'])
        cells = cells[3:]
    appendix = False
    for cell in cells:
        kind = cell['type']
        if kind == 'heading':
            title = re.sub(r'^(?:\d+(?:\.\d+)*|[A-Z]\d*(?:\.\d+)*)\s+', '', cell['text'])
            chapter_id = cell['tag'].removeprefix('chapter-')
            if cell['level'] == 1 and cell['tag'].startswith('chapter-') and not chapter_id.isdigit() and not appendix:
                tex += [r'\appendices' if ieee else r'\appendix']; appendix = True
            command = 'section' if cell['level'] == 1 else 'subsection'
            tex += ['\\' + command + '{' + escape(title) + '}', r'\hypertarget{' + cell['tag'] + '}{}']
        elif kind == 'text':
            text = escape(cell['text'])
            for link in cell.get('links', []):
                text = text.replace(link['text'], r'\hyperlink{' + link['tag'] + '}{' + link['text'] + '}')
            tex += [text, '']
        elif kind == 'equation':
            tex += [equation(cell)]
        elif kind == 'figure':
            full = cell['width_mm'] > 90
            env = 'figure*' if ieee and full else 'figure'
            width = r'\linewidth' if ieee or full else '88.9mm'
            caption = re.sub(r'^(?:图|Fig\.)\s*\d+\.\s*', '', cell['title'])
            tex += [r'\begin{' + env + '}[!htbp]', r'\centering',
                    r'\includegraphics[width=' + width + r',height=.72\textheight,keepaspectratio]{../../../' + cell['pdf'] + '}',
                    r'\setcounter{figure}{' + str(cell['number'] - 1) + '}',
                    r'\caption{' + escape(caption) + ('. ' + escape(cell['description']) if ieee else '') + '}',
                    r'\label{fig:' + cell['id'] + '}', r'\hypertarget{fig-' + cell['id'] + '}{}']
            if not ieee:tex += [r'{\small\raggedright ' + escape(cell['description']) + r'\par}']
            tex += [r'\end{' + env + '}']
        elif kind == 'table':
            rows = cell['rows']; count = len(rows[0]); env = 'table*' if ieee else 'table'
            tex += [r'\begin{' + env + '}[!htbp]', r'\centering', r'\caption{' + escape(cell['title']) + '}',
                    r'\begingroup\footnotesize', r'\begin{tabularx}{\textwidth}{' + '>{\\raggedright\\arraybackslash}X' * count + '}', r'\toprule']
            for index, row in enumerate(rows):
                tex += [' & '.join(r'\seqsplit{' + value + '}' if re.fullmatch('[0-9a-f]{64}', value) else escape(value).replace(r'\_', r'\_\allowbreak ') for value in row) + r'\\']
                if index == 0: tex += [r'\midrule']
            tex += [r'\bottomrule', r'\end{tabularx}\endgroup', r'\end{' + env + '}']
    keys = document.get('citation_keys', document['references'])
    references = {item['id']: item for item in manifest['references']}
    if document['references']:
        tex += [r'\renewcommand{\refname}{' + ('参考文献' if zh else 'References') + '}', r'\begin{thebibliography}{99}']
        for number, key in enumerate(keys, 1):
            if key in document['references']:
                entry = reference(references[key], number).split('] ', 1)[1]
                formatted=''.join(r'\url{' + part + '}' if part.startswith(('https://','http://')) else escape(part) for part in re.split(r'(https?://\S+)',entry))
                tex += [r'\bibitem[' + str(number) + ']{' + key + '} ' + formatted]
        tex += [r'\end{thebibliography}']
    return '\n'.join(tex + [r'\end{document}', ''])
