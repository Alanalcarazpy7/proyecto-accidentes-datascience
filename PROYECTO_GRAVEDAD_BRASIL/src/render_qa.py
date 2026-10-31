"""Renderiza todas las paginas y contactos para revision visual local."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output';QA=ROOT/'qa';QA.mkdir(exist_ok=True)
for source in (OUT/'reports').glob('*.pdf'):
    doc=pdfium.PdfDocument(source)
    thumbw,thumbh=190,285
    sheet=Image.new('RGB',(4*thumbw,((len(doc)+3)//4)*thumbh),'#d4dde3')
    for i in range(len(doc)):
        page=doc[i];im=page.render(scale=1.2).to_pil()
        im.save(QA/f'{source.stem}_p{i+1:02d}.png')
        thumb=im.copy();thumb.thumbnail((180,255))
        x=(i%4)*thumbw+5;y=(i//4)*thumbh+5
        sheet.paste(thumb,(x,y));ImageDraw.Draw(sheet).text((x,y+257),f'Pagina {i+1}',fill='#20323f')
    sheet.save(QA/f'CONTACTO_{source.stem}.png')
    doc.close()
    print('Renderizado',source.name)
