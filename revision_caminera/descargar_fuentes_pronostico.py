"""Descarga muestras oficiales para evaluar la viabilidad de un pronostico."""
import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'viabilidad_pronostico' / 'fuentes'
FILES = {
    'INE_2017_causas_2015_2017.xlsx': 'https://www.ine.gov.py/assets/documento/4e329Cuadro-12.2.3.xlsx',
    'INE_2017_tipologia_2016_2017.xlsx': 'https://www.ine.gov.py/assets/documento/7cbe1Cuadro-12.2.2.xlsx',
    'INE_2018_tipologia_2017_2018.xlsx': 'https://www.ine.gov.py/assets/documento/46630Cuadro_12.2.2.xlsx',
    'INE_2019_tipologia_2018_2019.xlsx': 'https://www.ine.gov.py/assets/documento/0207012.2.2_AEP_2019.xlsx',
    'INE_2021_tipologia_2020_2021.xlsx': 'https://www.ine.gov.py/assets/documento/0/12.2.2_AEP2021.xlsx',
    'INE_2022_tipologia_2021_2022.xlsx': 'https://www.ine.gov.py/assets/documento/61/12.2.2_AE2022.xlsx',
    'INE_2023_tipologia_2022_2023.xlsx': 'https://www.ine.gov.py/assets/documento/0/12.2.2_AE2023.xlsx',
    'INE_2024_tipologia_2023_2024.xlsx': 'https://www.ine.gov.py/assets/documento/0/12.2.2_AE2024.xlsx',
    'INE_2024_horas.xlsx': 'https://www.ine.gov.py/assets/documento/0/12.2.4_AE2024.xlsx',
    'INE_2024_motociclistas_2019_2024.xlsx': 'https://www.ine.gov.py/assets/documento/0/12.2.11_AE2024.xlsx',
    'PRF_datatran2025.zip': 'https://drive.google.com/uc?export=download&id=1-G3MdmHBt6CprDwcW99xxC4BZ2DU5ryR',
}


def download(pair):
    name, url = pair
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as response:
            content = response.read()
            final_url = response.url
        if not content.startswith(b'PK'):
            raise ValueError('La respuesta no es un ZIP/XLSX')
        (OUT / name).write_bytes(content)
        return dict(archivo=name, url=url, url_final=final_url, bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), estado='OK')
    except Exception as exc:
        return dict(archivo=name, url=url, estado=str(exc))


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(download, FILES.items()))
    (OUT.parent / 'fuentes_descargadas.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    for result in results:
        print(result['archivo'], result['estado'], result.get('bytes', 0), flush=True)
