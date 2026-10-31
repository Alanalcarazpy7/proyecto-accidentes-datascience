"""Descarga archivos oficiales PRF por ocurrencia y persona, 2017-2025.

No descarga la variante de todas las causas/tipos: puede repetir personas.
"""
import concurrent.futures
import hashlib
import json
import re
import shutil
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'fuentes_brasil'


def get(job):
    name,url=job
    target=OUT/name
    if name=='ocorrencias_2025.zip' and not target.exists():
        previous=ROOT.parent/'revision_caminera/viabilidad_pronostico/fuentes/PRF_datatran2025.zip'
        if previous.exists():shutil.copy2(previous,target)
    for attempt in range(2):
        try:
            if target.exists():data=target.read_bytes();final=url;status='Existente verificado'
            else:
                req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(req,timeout=60) as response:data=response.read();final=response.url
                status='Descargado'
            expected=b'%PDF-' if name.endswith('.pdf') else b'PK'
            if not data.startswith(expected):raise ValueError('Respuesta no corresponde al archivo esperado')
            target.write_bytes(data)
            return dict(archivo=name,url=url,url_final=final,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),estado=status)
        except Exception as exc:
            if attempt==1:return dict(archivo=name,url=url,estado='ERROR',error=str(exc))
            time.sleep(1)


if __name__=='__main__':
    catalog=json.loads((ROOT/'catalogo_prf.json').read_text(encoding='utf-8'))
    jobs=[]
    for row in catalog:
        text=row['descricao']
        if 'Todas as causas' in text:continue
        year=re.search(r'20\d{2}',text).group()
        kind='pessoas' if 'por pessoa)' in text else 'ocorrencias'
        ident=re.search(r'/d/([^/]+)/',row['url']).group(1)
        jobs.append((f'{kind}_{year}.zip',f'https://drive.google.com/uc?export=download&id={ident}'))
    jobs += [('dicionario_pessoas_2017.pdf','https://drive.google.com/uc?export=download&id=11qwcs8wLghYymG8owRb2FwS2Hi_SjZMf'),
             ('dicionario_ocorrencias_2017.pdf','https://drive.google.com/uc?export=download&id=11pXLw_0D0hHVS8fiC8cv2dPX39vpuOH1')]
    OUT.mkdir(exist_ok=True)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(get,jobs):
            results.append(result);print(result['archivo'],result['estado'],result.get('bytes'),result.get('error',''),flush=True)
    (ROOT/'descargas_prf.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
