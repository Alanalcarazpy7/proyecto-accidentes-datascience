"""Complemento para extraer dentro del proyecto original; no cambia su ZIP."""
from pathlib import Path
import json
import zipfile
import shutil
from mejorar import HERE,BASE,OUT,digest,writej


def main():
    check=json.loads((OUT/'verificacion_final.json').read_text(encoding='utf8'));assert check['estado']=='OK'
    frozen=json.loads((OUT/'congelamiento.json').read_text(encoding='utf8'))
    winner=next(x for x in frozen['modelos'] if x['nombre']==frozen['seleccionado'])
    shutil.copy2(HERE/winner['archivo'],HERE/'models/modelo_mejorado.joblib')
    target=HERE/'dist/Complemento_Mejora_Fase3_Brasil.zip';target.parent.mkdir(exist_ok=True)
    files=[]
    for f in HERE.rglob('*'):
        rel=f.relative_to(HERE)
        if not f.is_file() or any(c in {'dist','qa','tmp','__pycache__','.ipynb_checkpoints'} for c in rel.parts):continue
        if f.name in {'victimas_contexto_2017_2025.parquet','paquete_final.json'}:continue
        files.append((f,rel))
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f,rel in files:z.write(f,Path(BASE.name)/HERE.name/rel)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name in ['ABRIR_MEJORA.html','README.md','mejorar.py','output/Mejora_Fase_3.ipynb','output/INFORME_MEJORA_FASE_3.pdf','models/modelo_mejorado.joblib']:
            assert f'{BASE.name}/{HERE.name}/{name}' in z.namelist()
    writej(dict(archivo=str(target.relative_to(HERE)),archivos=len(files),bytes=target.stat().st_size,sha256=digest(target),tipo='Complemento; extraer junto a la carpeta original PROYECTO_GRAVEDAD_BRASIL; requiere sus modulos y datos 2017-2025 para recalcular desde cero'),OUT/'paquete_final.json')
    print('Complemento ZIP verificado:',round(target.stat().st_size/1e6,2),'MB;',len(files),'archivos')


if __name__=='__main__':main()
