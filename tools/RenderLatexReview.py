"""Render every compiled manuscript page for an auditable visual review."""
import argparse
import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from litz_research.latex_publication import save, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run = (root / 'outputs' / args.run_id).resolve()
    if not run.is_relative_to((root / 'outputs').resolve()):
        raise ValueError('Run directory escapes outputs')
    receipt = json.loads((run / 'compile-receipt.json').read_text(encoding='utf-8'))
    index = []
    for row in receipt:
        pdf = run / 'pdf' / row['id'] / 'main.pdf'
        if sha(pdf) != row['pdf_sha256']:
            raise ValueError('Compiled PDF changed: ' + row['id'])
        directory = run / 'pages' / row['id']
        directory.mkdir(parents=True, exist_ok=True)
        document = pdfium.PdfDocument(str(pdf))
        previews = []
        for number in range(len(document)):
            page = document[number]
            bitmap = page.render(scale=1.5)
            image = bitmap.to_pil().convert('RGB')
            path = directory / f'{number+1:03}.png'
            image.save(path)
            previews.append(path)
            bitmap.close()
            page.close()
        document.close()
        sheets = []
        for offset in range(0, len(previews), 4):
            sheet = Image.new('RGB', (1800, 2520), '#d0d0d0')
            draw = ImageDraw.Draw(sheet)
            for cell, path in enumerate(previews[offset:offset+4]):
                image = Image.open(path)
                image.thumbnail((880, 1200))
                x, y = (cell % 2) * 900 + 10, (cell // 2) * 1260 + 35
                sheet.paste(image, (x, y))
                draw.text((x, y-25), f'{row["id"]} / {offset+cell+1}', fill='black')
            path = directory / f'sheet-{offset//4+1:02}.jpg'
            sheet.save(path, quality=92)
            sheets.append(path.relative_to(run).as_posix())
        index.append({'document': row['id'], 'pdf_sha256': row['pdf_sha256'],
                      'pages': [p.relative_to(run).as_posix() for p in previews],
                      'sheets': sheets, 'visual_review': 'pending'})
        save(run / 'page-review.json', index)
        print(row['id'], len(previews), 'pages rendered', flush=True)


if __name__ == '__main__':
    main()
