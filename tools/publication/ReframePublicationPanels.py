"""Reframe native publication panels on a shared, physical-size canvas."""
from pathlib import Path
import argparse, copy, json, re, shutil
from BuildPublicationEdition import ROOT, read, write, sha, native_run


def build(run_id, selected=None, source_run='data/publication'):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', run_id):
        raise ValueError('Run ID uses letters, numbers, underscores and hyphens')
    run = ROOT / 'outputs' / run_id
    run.mkdir(parents=True, exist_ok=False)
    shutil.copy2(Path(__file__), run / Path(__file__).name)
    from litz_research.common import resolve_read_path
    base = resolve_read_path(ROOT,source_run)
    ids = {'q1_cross_section': 'field', 'q1_fem_error': 'curve',
           'peec_length': 'curve', 'peec_cross_section': 'field', 'coax640_mesh': 'curve'}
    if selected:
        ids = {key: value for key,value in ids.items() if key in selected}
    layouts = {
        'field': {'canvas_pt': [252, 198], 'frame_pt': [144, 144],
                  'padding_pt': [[40, 24], [40, 14]], 'plot_image_pt': [208, 198]},
        'curve': {'canvas_pt': [252, 198], 'frame_pt': [192, 144],
                  'padding_pt': [[52, 8], [40, 14]], 'plot_image_pt': [252, 198]},
    }
    panels = []
    for record in read(base / 'panel_manifest.json')['panels']:
        if record['id'] not in ids:
            continue
        panel = copy.deepcopy(record)
        source = base / 'panels' / panel['language'] / (panel['id'] + '.wl')
        panel.update(source_expression=str(source), source_expression_sha256=sha(source),
                     layout=layouts[ids[panel['id']]], layout_kind=ids[panel['id']],
                     legend_anchor='right' if panel['id']=='q1_fem_error' else 'left')
        panels.append(panel)
    write(run / 'render_request.json', {'run_id': run_id, 'output_directory': str(run),
          'source_manifest_sha256': sha(base / 'panel_manifest.json'), 'panels': panels})
    native_run(run, run / 'render_request.json', 'ReframePublicationPanels.wls')
    result = read(run / 'panel_manifest.json')
    if result['failures'] or len(result['panels']) != 2*len(ids):
        raise RuntimeError('Bilingual exports required for each selected panel')
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    for panel in result['panels']:
        pdf = next(a for a in panel['assets'] if a['format']=='pdf')
        path = Path(pdf['path'])
        page = PdfReader(path).pages[0]
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        factor = 252 / width
        page.scale_by(factor)
        for box in ('mediabox','cropbox','trimbox','bleedbox','artbox'):
            setattr(page, box, RectangleObject([0, 0, 252, height*factor]))
        writer = PdfWriter(); writer.add_page(page)
        temp = path.with_suffix('.sized.pdf')
        with temp.open('wb') as stream: writer.write(stream)
        temp.replace(path)
        panel['pdf_physical_size'] = dict(native_export_sha256=pdf['sha256'],
              content_scale_factor=factor, width_pt=252, height_pt=height*factor,
              vector_content_preserved=True)
        pdf.update(sha256=sha(path), bytes=path.stat().st_size)

        if panel['layout_kind']=='field':
            from PIL import Image
            png=next(a for a in panel['assets'] if a['format']=='png')
            with Image.open(png['path']) as im:
                rgb=im.convert('RGB'); w,h=rgb.size
                x=round(212/252*w)
                samples=[rgb.getpixel((x,round(h-(40+144*t)/198*h))) for t in (.1,.5,.9)]
            if sum(samples[0])-sum(samples[-1]) < 120:
                raise RuntimeError('Rendered color-bar contrast: '+panel['id'])
            panel['rendered_color_bar_rgb']=samples

            for key in ('color_range','color_function_sha256','color_endpoint_rgb'):
                if key not in panel:raise RuntimeError('Color mapping diagnostic: ' + key)
        if panel['source_plot_range'] != panel['output_plot_range']:
            raise RuntimeError('Plot range identity: ' + panel['id'])
        if not panel['numeric_graphics_preserved']:
            raise RuntimeError('Source graphics identity check: ' + panel['id'])
        for asset in panel['assets']:
            if sha(asset['path']) != asset['sha256']:
                raise RuntimeError('Export hash mismatch')
    write(run / 'panel_manifest.json', result)
    print(json.dumps({'run_id': run_id, 'panels': len(result['panels']), 'verified': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--panel', action='append', choices=['q1_cross_section','q1_fem_error','peec_length','peec_cross_section','coax640_mesh'])
    parser.add_argument('--source-run',default='data/publication')
    args=parser.parse_args()
    build(args.run_id,args.panel,args.source_run)
