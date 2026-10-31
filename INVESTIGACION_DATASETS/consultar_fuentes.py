"""Consultas publicas y descargas de muestras; no envia solicitudes ni mensajes."""
import concurrent.futures
import json
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(request,timeout=35) as response:
        return response.read(),response.url,response.status


def query_catalog(word):
    url='https://www.datos.gov.py/api/3/action/package_search?'+urllib.parse.urlencode({'q':word,'rows':100})
    try:
        data,final,status=fetch(url)
        obj=json.loads(data)
        result=obj.get('result',{})
        datasets=[]
        for item in result.get('results',[]):
            datasets.append(dict(name=item.get('name'),title=item.get('title'),
                organization=(item.get('organization') or {}).get('title'),
                resources=[dict(name=r.get('name'),format=r.get('format'),url=r.get('url')) for r in item.get('resources',[])]))
        return dict(consulta=word,url=url,status=status,count=result.get('count'),datasets=datasets)
    except Exception as exc:return dict(consulta=word,url=url,error=str(exc))


def page_links(pair):
    name,url=pair
    try:
        data,final,status=fetch(url)
        (ROOT/'fuentes_paraguay'/(name+'.html')).write_bytes(data)
        soup=BeautifulSoup(data,'html.parser')
        links=[dict(text=' '.join(a.get_text(' ',strip=True).split()),url=urllib.parse.urljoin(final,a['href']))
               for a in soup.find_all('a',href=True)]
        return dict(name=name,url=final,status=status,links=links)
    except Exception as exc:return dict(name=name,url=url,error=str(exc))


if __name__=='__main__':
    words=['accidentes','siniestros','transito','911','defunciones']
    pages=[('antsv','https://antsv.gov.py/'),('observatorio','https://antsv.gov.py/observatorio-vial/'),
           ('trauma','https://htrauma.gov.py/informe-semanal/'),
           ('PRF','https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf'),
           ('PRF_diccionario','https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        catalogs=list(pool.map(query_catalog,words))
        links=list(pool.map(page_links,pages))
    (ROOT/'catalogo_paraguay.json').write_text(json.dumps(catalogs,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'enlaces_oficiales.json').write_text(json.dumps(links,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in catalogs:
        print('CATALOGO',row['consulta'],row.get('count'),row.get('error',''),flush=True)
        for d in row.get('datasets',[]):print(' ',d['name'],len(d['resources']))
    for row in links:
        print('PAGINA',row['name'],'links',len(row.get('links',[])),row.get('error',''),flush=True)
        if row['name']=='antsv':
            for link in row.get('links',[]):
                if any(k in (link['text']+' '+link['url']).lower() for k in ['siat','dato','estad','tablero']):print(link)
