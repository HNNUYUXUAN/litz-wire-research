"""Construct and verify editions using the canonical Markdown document model."""
from types import SimpleNamespace
from BuildPublicationEdition import ROOT,read,write,sha
from PublicationManuscripts import build_documents,prepare_latex,verify as verify_edition
def build(run,edition="all",language="all",form="all",layout="all",source_manifest="manuscript/publication.json"):
    args=SimpleNamespace(edition=edition,language=language,form=form,layout=layout,source_manifest=source_manifest)
    manifest=read(ROOT/source_manifest)
    build_documents(run,manifest,args)
    prepare_latex(run,manifest,args)
def verify(run):
    return verify_edition(run,read(run/"input_manifest.json"))
def render_composites(run):
    import pypdfium2 as pdfium
    records=[]
    for item in read(run/"composite_manifest.json")["composites"]:
        path=run/item["pdf_relative_to_run"]
        doc=pdfium.PdfDocument(str(path));page=doc[0];bitmap=page.render(scale=600/72)
        image=bitmap.to_pil();image.save(path.with_suffix(".png"),dpi=(600,600))
        records.append(dict(id=item["id"],language=item["language"],source_pdf_sha256=sha(path),pixels=list(image.size)))
        bitmap.close();page.close();doc.close()
    write(run/"composite_raster_verification.json",dict(composites=records,plotting_calls=0))
