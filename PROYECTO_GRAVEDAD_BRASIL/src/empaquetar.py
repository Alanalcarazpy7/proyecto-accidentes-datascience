"""Paquete acumulativo sin originales voluminosos ni caches duplicados."""
from pathlib import Path
import hashlib
import json
import zipfile
from common import ROOT,OUT,save_json


def main():
    check=json.loads((OUT/'verificacion_final.json').read_text(encoding='utf8'))
    assert check['estado']=='OK'
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/'Fase3_DataScience_Alcaraz-Ferreira-Rios_Brasil.zip'
    files=[]
    for f in ROOT.rglob('*'):
        rel=f.relative_to(ROOT)
        if not f.is_file() or any(c in {'dist','qa','tmp','raw','.git','__pycache__','.ipynb_checkpoints'} for c in rel.parts):continue
        if f.name in {'victimas_modelado.joblib','victimas_limpias.csv.gz','CV_preliminar_categorias_ordenadas_NO_USAR.json','paquete_final.json'}:continue
        files.append((f,rel))
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f,rel in files:z.write(f,Path(ROOT.name)/rel)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        names=z.namelist()
        for required in ['README.md','ABRIR_RESULTADOS.html','data/processed/victimas_limpias.parquet','models/modelo_seleccionado.joblib','src/pdf_layout.py','src/descargar_fuentes.py','output/reports/Fase_3_Modelado_y_Evaluacion.pdf']:
            assert f'{ROOT.name}/{required}' in names
    save_json(dict(archivo=str(target.relative_to(ROOT)),archivos=len(files),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),nota='Originales >25 MB excluidos; dataset limpio Parquet incluido; fuentes y descargador con hashes incluidos; no publicacion externa'),OUT/'paquete_final.json')
    print('ZIP verificado',target,'MB',round(target.stat().st_size/1e6,2),'archivos',len(files))


if __name__=='__main__':main()
