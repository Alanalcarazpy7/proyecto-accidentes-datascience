"""Inventario reproducible de los PDF originales, sin modificar sus archivos.

Ejecutar desde cualquier directorio: python ruta/a/revision_caminera/auditar_pdf.py
Requiere pypdf. No descarga datos ni construye observaciones individuales.
"""
import collections
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


def main():
    output = Path(__file__).resolve().parent
    root = output.parent
    text_dir = output / 'texto_pdf'
    text_dir.mkdir(exist_ok=True)
    items = []
    hashes = collections.defaultdict(list)
    for folder in sorted(root.iterdir()):
        if not (folder.is_dir() and folder.name.isdigit() and len(folder.name) == 4):
            continue
        for file in sorted(folder.glob('*.pdf')):
            relative = str(file.relative_to(root))
            reader = PdfReader(file)
            texts = [page.extract_text() or '' for page in reader.pages]
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            hashes[digest].append(relative)
            target = text_dir / f'{folder.name}__{file.stem}.txt'
            target.write_text('\n\n'.join(
                f'=== PAGINA {i + 1} ===\n{text}' for i, text in enumerate(texts)
            ), encoding='utf-8')
            items.append(dict(
                archivo=relative, carpeta=folder.name, paginas=len(reader.pages),
                bytes=file.stat().st_size, sha256=digest,
                caracteres_texto=sum(map(len, texts)),
                paginas_sin_texto=[i + 1 for i, text in enumerate(texts) if not text.strip()],
            ))
    summary = dict(
        archivos=len(items), documentos_unicos=len(hashes),
        paginas=sum(item['paginas'] for item in items),
        paginas_unicas=sum(next(item['paginas'] for item in items
                                if item['sha256'] == digest) for digest in hashes),
        por_carpeta=dict(collections.Counter(item['carpeta'] for item in items)),
        duplicados=[files for files in hashes.values() if len(files) > 1],
        archivos_detalle=items,
    )
    (output / 'inventario_pdf.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in ('archivos_detalle', 'duplicados')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
