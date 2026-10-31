"""Descarga fuentes publicas del corte registrado, sin pedidos institucionales."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,urllib.request
from common import ROOT,RAW


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    items=json.loads((ROOT/'data/fuentes.json').read_text(encoding='utf8'))
    def get(r):
        path=RAW/r['archivo']
        if path.exists():data=path.read_bytes()
        else:
            req=urllib.request.Request(r['url'],headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=90) as response:data=response.read()
        assert hashlib.sha256(data).hexdigest()==r['sha256'],f"Fuente distinta del corte auditado: {r['archivo']}. No reemplazar silenciosamente."
        if not path.exists():path.write_bytes(data)
        print('Verificado',path.name,flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(get,items))


if __name__=='__main__':main()
