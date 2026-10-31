"""Descarga opaca: no descomprime ni lee etiquetas de la nueva prueba."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import hashlib
import json
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'data/raw_2026'


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    manifest=ROOT/'manifiesto_2026.json'
    previous={r['archivo']:r for r in json.loads(manifest.read_text(encoding='utf8'))} if manifest.exists() else {}
    jobs=[('ocorrencias_2026.zip','1A3IirNm0AzRaSosA1IS94DOVmvKsn0Ol'),('pessoas_2026.zip','1B_rvx1kPHuFowP5rs84ZO-57gN8yUs85')]
    def get(job):
        name,ident=job;url=f'https://drive.google.com/uc?export=download&id={ident}'
        target=RAW/name
        if target.exists():
            data=target.read_bytes()
            if name in previous:
                assert hashlib.sha256(data).hexdigest()==previous[name]['sha256'],'Archivo existente distinto del corte registrado'
                return previous[name]
        else:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=90) as response:data=response.read()
            assert data.startswith(b'PK'),'Respuesta no corresponde a ZIP publico'
            target.write_bytes(data)
        return dict(archivo=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),descarga_UTC=datetime.now(timezone.utc).isoformat(),fuente='https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf',estado='ZIP descargado sin descomprimir ni leer etiquetas')
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(get,jobs))
    (ROOT/'manifiesto_2026.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    for r in rows:print(r['archivo'],r['bytes'],'bytes; descarga opaca verificada',flush=True)


if __name__=='__main__':main()
