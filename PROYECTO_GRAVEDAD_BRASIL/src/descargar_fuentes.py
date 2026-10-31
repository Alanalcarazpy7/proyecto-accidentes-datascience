"""Recupera fuentes publicas con hashes del corte auditado; no presenta pedidos."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import urllib.request
from common import ROOT, RAW


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    items=json.loads((ROOT/'data/manifiesto_origenes.json').read_text(encoding='utf8'))
    def get(item):
        f=RAW/item['archivo']
        if f.exists():data=f.read_bytes()
        else:
            req=urllib.request.Request(item['url'],headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=90) as response:data=response.read()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError(f'{f.name}: fuente distinta del corte guardado. No reemplazar silenciosamente; documentar nueva version.')
        if not f.exists():f.write_bytes(data)
        print('Verificado',f.name,flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(get,items))


if __name__=='__main__':main()
