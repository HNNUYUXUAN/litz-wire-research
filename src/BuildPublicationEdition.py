"""Source-bound bilingual publication builds; CPU postprocessing only.

Each plotting panel is exported independently by Wolfram. PDF/SVG composition
reads those files and never calls a plotting function. Markdown sources and the shared publication manifest define the scholarly editions.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import PreManuscriptClosure as control

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "outputs/closure_20261005_manuscript_bundle_final_02"
TABLES = ROOT / "data/publication/tables"
SCIENCE_FILES = (ROOT / "docs/总控/当前运行索引.json", ROOT / "outputs/prewrite_closure_state.json")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def asset_path(run, asset):
    return run / asset['path_relative_to_run'] if asset.get('path_relative_to_run') else Path(asset['path'])


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def array_from_descriptor(desc):
    path = BUNDLE / desc["path"]
    if desc.get("sha256") and sha(path) != desc["sha256"]:
        raise ValueError("Changed frozen numeric attachment: " + desc["path"])
    rows = csv_rows(path)
    values = [float(row["value"]) for row in rows]
    dims = desc["dimensions"]
    if len(values) != math.prod(dims):
        raise ValueError("Frozen array size mismatch")
    def reshape(v, shape):
        if len(shape) == 1:
            return v
        stride = math.prod(shape[1:])
        return [reshape(v[i:i+stride], shape[1:]) for i in range(0, len(v), stride)]
    return reshape(values, dims)


def prepare_specimen(run, languages):
    source = TABLES / "q1_analytic_profile.csv"
    rows = csv_rows(source)
    radial = [(float(r["r_mm"]), float(r["abs_J_A_per_mm2"])) for r in rows]
    def interpolate(r):
        index = min(int(r / radial[-1][0] * (len(radial)-1)), len(radial)-2)
        while radial[index+1][0] < r:
            index += 1
        x0, y0 = radial[index]; x1, y1 = radial[index+1]
        return y0 + (y1-y0) * (r-x0)/(x1-x0)
    # Map the already frozen axisymmetric magnitude profile to a display grid.
    density = [[i/55, j/55, interpolate(math.hypot(i/55, j/55))]
               for j in range(-55,56) for i in range(-55,56) if i*i+j*j <= 55*55]
    geometry_path = BUNDLE / "routes/closure_geometry/data.json"
    geometry = next(g for g in read(geometry_path)["geometries"]
                    if g["kind"] == "multilevel" and g["axial_sample_segments"] == 1600)
    full_paths = array_from_descriptor(geometry["paths"])
    # An actual 3 mm interval, with no axis deformation. Endpoint subsampling
    # affects display only; the original trajectory files remain untouched.
    paths = [[[1000*v for v in p] for k,p in enumerate(line)
              if p[2] <= .003 + 1e-12 and k % 4 == 0] for line in full_paths]
    numeric = {"radial":radial,"phase":[[float(r["r_mm"]),float(r["phase_unwrapped_deg"])] for r in rows],
               "density":density,"geometry_paths_mm":paths}
    write(run / "specimen_numeric_data.json", numeric)
    data_hash = sha(run / "specimen_numeric_data.json")
    texts = {
      "zh-CN": {"x":"半径 r (mm)","j":"电流密度 |Jz| (A/mm²)","phase":"连续相位 (°)",
        "xy":["x (mm)","y (mm)"],"bar":"|Jz| (A/mm²)",
        "curve_caption":"图 1  单圆线解析校准：200 kHz、20 A RMS、直径 2 mm。由冻结径向数据重绘。",
        "field_caption":"图 2  圆截面上的解析幅值。冻结径向幅值作线性插值后按轴对称关系映射；不是新三维场解。",
        "geometry_caption":"图 3  24 股传统多级中心线的 3 mm 局部视图，铜径 0.100 mm。蓝色为股线 1、9、17，铜色为其余股线。几何展示不构成电磁性能排名。"},
      "en": {"x":"Radius r (mm)","j":"Current density |Jz| (A/mm²)","phase":"Unwrapped phase (°)",
        "xy":["x (mm)","y (mm)"],"bar":"|Jz| (A/mm²)",
        "curve_caption":"Fig. 1. Round-wire analytical calibration at 200 kHz, 20 A RMS and 2 mm diameter, redrawn from frozen radial data.",
        "field_caption":"Fig. 2. Axisymmetric cross-sectional magnitude mapped by linear interpolation of the frozen radial profile; this is not a new three-dimensional field solution.",
        "geometry_caption":"Fig. 3. A 3 mm detail of the archived 24-strand multilevel geometry, with 0.100 mm copper diameter. Strands 1, 9 and 17 are blue. Geometry alone does not establish an electromagnetic ranking."}}
    panels=[]
    for language in languages:
        t=texts[language]
        common={"language":language,"data_sha256":data_hash,"source_run_id":"closure_20261005_analytic_01","source_model":"frozen_Bessel_radial_profile"}
        for key, pts, label in [("q1_magnitude",radial,t["j"]),("q1_phase",numeric["phase"],t["phase"])]:
            panels.append(dict(common,id=key,kind="curve",series=[{"points":pts,"label":label,"color":"#265B8F"}],x_label=t["x"],y_label=label,caption=t["curve_caption"]))
        panels.append(dict(common,id="q1_cross_section",kind="density",points=density,minimum=min(v for _,v in radial),maximum=max(v for _,v in radial),x_label=t["xy"][0],y_label=t["xy"][1],color_label=t["bar"],caption=t["field_caption"]))
        panels.append({**common,"id":"multilevel_detail","kind":"geometry","paths_mm":paths,"radius_mm":.05,"highlight_ids":[1,9,17],"source_run_id":"closure_20261005_geometry_01","source_model":"archived_geometric_trajectories_only","caption":t["geometry_caption"]})
    write(run / "render_request.json", {"run_id":run.name,"output_directory":str(run),"panels":panels})
    source_rows=[{"path":str(p.relative_to(ROOT)).replace('\\','/'),"sha256":sha(p)} for p in [source,geometry_path,BUNDLE/geometry["paths"]["path"]]]
    write(run / "source_manifest.json", {"sources":source_rows,"display_transformations":{"cross_section":"piecewise linear radial magnitude interpolation; circular support","geometry":"SI to mm; actual z <= 3 mm; every fourth source sample; no axis scaling","phase":"archived nearest-360-degree unwrapped phase"},"data_sha256":data_hash,"frozen_science_sha256":{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in SCIENCE_FILES}})


def native_run(run, request, script="BuildPublicationFigures.wls", suffix=""):
    import ctypes,time
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    if not kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),(1<<min(8,os.cpu_count() or 1))-1):raise ctypes.WinError(ctypes.get_last_error())
    monitor=run / ("monitor_"+Path(script).stem+suffix+'_'+time.strftime('%H%M%S'))
    monitor.mkdir()
    actual=control.hardware()
    budget=min(24*control.GIB,actual["free_RAM_bytes"]-8*control.GIB)
    if budget <= 0:
        raise RuntimeError("System free reserve preflight failed")
    write(monitor / "environment.json", actual)
    environment=dict(os.environ,CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="8",MKL_NUM_THREADS="8",OPENBLAS_NUM_THREADS="8",PYTHONIOENCODING="utf-8")
    from litz_research.common import tool
    executable=tool(ROOT,"wolframscript")
    if not executable:raise RuntimeError("Wolfram stage requires LITZ_WOLFRAMSCRIPT or wolframscript on PATH")
    command=[executable,"-file",str(ROOT/"src"/script),str(request)]
    sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src'/script,ROOT/'src/PublicationStyles.wl',ROOT/'src/BuildPublicationEdition.py',ROOT/'src/PublicationLineArt.wl']}
    snapshot=monitor/'source_snapshot';snapshot.mkdir()
    for p in [ROOT/'src'/script,ROOT/'src/PublicationStyles.wl',ROOT/'src/BuildPublicationEdition.py',ROOT/'src/PublicationLineArt.wl']:shutil.copy2(p,snapshot/p.name)
    write(monitor/'source_binding_before.json',sources)
    result=control.run_custom_monitored(command,monitor,environment,budget)
    changed=[p for p,h in sources.items() if sha(ROOT/p)!=h]
    write(monitor/'source_binding_after.json',{'sources':sources,'changed':changed,'actual_child_exit_code':result.returncode})
    if changed:raise RuntimeError('Sources changed during native stage: '+str(changed))
    if result.returncode:
        raise RuntimeError("Native stage failed; actual exit %s, log %s" % (result.returncode, monitor/"run_log.txt"))


def compose(run):
    from pypdf import PdfReader, PdfWriter, Transformation
    manifest=read(run/"panel_manifest.json")
    groups=read(run/'render_request.json').get('composition_groups',[("q1_profile",["q1_magnitude","q1_phase"]),("field_geometry",["q1_cross_section","multilevel_detail"])])
    rows=[]
    for language in sorted({p["language"] for p in manifest["panels"]}):
        for group,ids in groups:
            panels=[next(p for p in manifest["panels"] if p["language"]==language and p["id"]==i) for i in ids]
            target=run/"composites"/language/group;target.parent.mkdir(parents=True,exist_ok=True)
            writer=PdfWriter();width=182/25.4*72;gap=4.2/25.4*72;panel_width=252
            readers=[PdfReader(next(asset_path(run,a) for a in p["assets"] if a["format"]=="pdf")) for p in panels]
            sizes=[(float(r.pages[0].mediabox.width),float(r.pages[0].mediabox.height)) for r in readers]
            heights=[h*panel_width/w for w,h in sizes];columns=2;row_count=math.ceil(len(panels)/columns)
            row_heights=[max(heights[k*columns:(k+1)*columns])+15 for k in range(row_count)]
            row_offsets=[sum(row_heights[:k])+k*gap for k in range(row_count)]
            height=sum(row_heights)+(row_count-1)*gap
            page=writer.add_blank_page(width=width,height=height)
            for i,(reader,(w,h)) in enumerate(zip(readers,sizes)):
                col=i%columns;row=i//columns
                page.merge_transformed_page(reader.pages[0],Transformation().scale(panel_width/w).translate(col*(panel_width+gap),height-row_offsets[row]-15-heights[i]),expand=False)
                letter='abcd'[i]
                label=PdfReader(run/'annotations'/f'{letter}.pdf')
                page.merge_transformed_page(label.pages[0],Transformation().translate(col*(panel_width+gap)+(panel_width-30)/2,height-row_offsets[row]-15),expand=False)
            with target.with_suffix('.pdf').open('wb') as f:writer.write(f)
            # Nest exported independent SVGs with isolated ID namespaces.
            outer=ET.Element('{http://www.w3.org/2000/svg}svg',{'width':'182mm','height':f'{height/72*25.4:.6f}mm','viewBox':f'0 0 {width} {height}'})
            for i,p in enumerate(panels):
                source=next(asset_path(run,a) for a in p['assets'] if a['format']=='svg')
                svg=ET.parse(source).getroot();prefix=f'{group}_{i}_'
                ids_in={e.get('id'):prefix+e.get('id') for e in svg.iter() if e.get('id')}
                for e in svg.iter():
                    for k,v in list(e.attrib.items()):
                        if k=='id':e.set(k,ids_in[v])
                        else:
                            for old,new in ids_in.items():v=v.replace('url(#'+old+')','url(#'+new+')').replace('#'+old,'#'+new)
                            e.set(k,v)
                col=i%columns;row=i//columns
                svg.set('x',str(col*(panel_width+gap)));svg.set('y',str(row_offsets[row]+15));svg.set('width',str(panel_width));svg.set('height',str(heights[i]));outer.append(svg)
                label=ET.parse(run/'annotations'/f'{"abcd"[i]}.svg').getroot()
                label_ids={e.get('id'):f'label_{group}_{i}_'+e.get('id') for e in label.iter() if e.get('id')}
                for e in label.iter():
                    for k,v in list(e.attrib.items()):
                        if k=='id':e.set(k,label_ids[v])
                        else:
                            for old,new in label_ids.items():v=v.replace('url(#'+old+')','url(#'+new+')').replace('#'+old,'#'+new)
                            e.set(k,v)
                label.set('x',str(col*(panel_width+gap)+(panel_width-30)/2));label.set('y',str(row_offsets[row]));label.set('width','30');label.set('height','15');outer.append(label)
            ET.ElementTree(outer).write(target.with_suffix('.svg'),encoding='utf-8',xml_declaration=True)
            rows.append({'id':group,'language':language,'width_mm':182,'panel_ids':ids,'source_pdf_sha256':[sha(asset_path(run,a)) for p in panels for a in p['assets'] if a['format']=='pdf'],'layout':{'gap_mm':4.2,'label_band_pt':15,'rows':row_count,'columns':columns,'panel_width_mm':88.9},'pdf':str(target.with_suffix('.pdf')),'svg':str(target.with_suffix('.svg')),'pdf_relative_to_run':target.with_suffix('.pdf').relative_to(run).as_posix(),'svg_relative_to_run':target.with_suffix('.svg').relative_to(run).as_posix(),'plotting_calls':0})
    write(run/'composite_manifest.json',{'composites':rows,'plotting_calls':0,'composition_engine':'pypdf; original exported panel content retained'})


def normalize_export_sizes(run):
    """Set physical dimensions without redrawing. Preserve native export bytes."""
    from pypdf import PdfReader,PdfWriter,Transformation
    manifest=read(run/'panel_manifest.json')
    write(run/'native_panel_manifest.json',manifest)
    def pdf_scale(path,width):
        reader=PdfReader(path);page=reader.pages[0];before=(float(page.mediabox.width),float(page.mediabox.height))
        native=path.with_name(path.stem+'.native.pdf');shutil.copy2(path,native)
        scale=width/before[0];writer=PdfWriter();target=writer.add_blank_page(width=width,height=before[1]*scale)
        target.merge_transformed_page(page,Transformation().scale(scale),expand=False)
        with path.open('wb') as stream:writer.write(stream)
        return {'native_export':str(native),'native_sha256':sha(native),'scale':scale,'width_pt_before':before[0],'width_pt_after':width}
    for panel in manifest['panels']:
        transforms=[]
        for asset in panel['assets']:
            path=Path(asset['path'])
            if asset['format']=='pdf':transforms.append(pdf_scale(path,252))
            if asset['format']=='svg':
                native=path.with_name(path.stem+'.native.svg');shutil.copy2(path,native)
                tree=ET.parse(path);root=tree.getroot();box=[float(v) for v in root.get('viewBox').replace(',',' ').split()]
                root.set('width','88.9mm');root.set('height',str(88.9*box[3]/box[2])+'mm');tree.write(path,encoding='utf-8',xml_declaration=True)
            asset.update(sha256=sha(path),bytes=path.stat().st_size)
            asset['path_relative_to_run']=path.relative_to(run).as_posix()
        panel['physical_size_normalization']=transforms
    for path in (run/'annotations').glob('*.pdf'):pdf_scale(path,30)
    manifest['normalization_engine']='pypdf physical page scaling; SVG physical root size; no data or plotting changes'
    manifest['portable_path_base']='run_root; use path_relative_to_run when relocated'
    write(run/'panel_manifest.json',manifest)


def verify_panels(run):
    from pypdf import PdfReader
    from PIL import Image
    manifest=read(run/'panel_manifest.json');checks=[]
    for panel in manifest['panels']:
        assets=panel['assets'];checks.append({'name':panel['language']+'/'+panel['id']+'/exports','passed':{a['format'] for a in assets}=={'pdf','svg','png'}})
        for asset in assets:checks.append({'name':asset['path']+'/sha256','passed':sha(asset_path(run,asset))==asset['sha256']})
        pdf=PdfReader(next(asset_path(run,a) for a in assets if a['format']=='pdf'))
        checks.append({'name':panel['language']+'/'+panel['id']+'/physical_width','passed':abs(float(pdf.pages[0].mediabox.width)-252)<1e-6,'actual_width_mm':float(pdf.pages[0].mediabox.width)/72*25.4})
        png=Image.open(next(asset_path(run,a) for a in assets if a['format']=='png'))
        checks.append({'name':panel['language']+'/'+panel['id']+'/actual_raster_resolution','passed':png.width>=2100,'pixels':list(png.size),'minimum_width_pixels':2100})
        fonts=[]
        for page in pdf.pages:
            resources=page.get('/Resources',{}).get_object()
            font_resources=resources.get('/Font',{})
            if hasattr(font_resources,'get_object'):font_resources=font_resources.get_object()
            for ref in font_resources.values():
                font=ref.get_object();desc=font.get('/FontDescriptor')
                if desc is None and font.get('/DescendantFonts'):desc=font['/DescendantFonts'][0].get_object().get('/FontDescriptor')
                desc=desc.get_object() if desc else {}
                fonts.append({'name':str(font.get('/BaseFont','')),'embedded':any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3'])})
        checks.append({'name':panel['language']+'/'+panel['id']+'/embedded_fonts','passed':all(f['embedded'] for f in fonts),'fonts':fonts})
        if panel['kind']!='geometry':
            checks.append({'name':panel['language']+'/'+panel['id']+'/Times_New_Roman_present','passed':any('TimesNewRoman' in f['name'] for f in fonts)})
        if panel['language']=='zh-CN' and panel['kind']=='curve':
            checks.append({'name':panel['language']+'/'+panel['id']+'/SimSun_present','passed':any('SimSun' in f['name'] for f in fonts)})
    before=read(run/'source_manifest.json')['frozen_science_sha256']
    for p in SCIENCE_FILES:checks.append({'name':'unchanged/'+str(p.relative_to(ROOT)),'passed':sha(p)==before[str(p.relative_to(ROOT)).replace('\\','/')]})
    result={'checks':checks,'failed_checks':sum(not c['passed'] for c in checks),'physical_solver_executed':False,'GPU_compute_used':False,'visual_review':'pending'}
    write(run/'panel_verification.json',result)
    if result['failed_checks']:raise RuntimeError('Panel verification failed')


def main():
    from PublicationManuscripts import main as build
    return build()


if __name__=="__main__":
    raise SystemExit(main())
