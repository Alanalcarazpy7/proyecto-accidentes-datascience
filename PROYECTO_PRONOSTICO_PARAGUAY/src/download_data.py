"""Restaurar originales desde sus URL, verificando la version exacta por hash."""
import hashlib
import json
import urllib.request

from common import ROOT


def main():
    raw=ROOT/'data/raw'
    catalog=json.loads((raw/'catalogo_fuentes.json').read_text(encoding='utf-8'))
    for row in catalog:
        if 'tipologia' not in row['archivo']:continue
        target=raw/row['archivo']
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256']:
            print('Original verificado:',target.name);continue
        with urllib.request.urlopen(urllib.request.Request(row['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as response:
            data=response.read()
        if hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError(f'La version remota cambio: {row["archivo"]}. Documentar revision antes de reemplazar datos.')
        target.write_bytes(data);print('Descargado y verificado:',target.name)


if __name__=='__main__':main()
