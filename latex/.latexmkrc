# Local XeLaTeX authoring; output directory may be overridden with -outdir.
$pdf_mode = 5;
$xelatex = 'xelatex --enable-installer -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape %O %S';
$bibtex = 'bibtex %O %B';
$out_dir = '../outputs/latex_work';
