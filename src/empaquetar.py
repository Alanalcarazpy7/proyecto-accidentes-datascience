"""Un unico ZIP acumulativo de la entrega, sin fuentes originales >25 MB."""
import json,zipfile,hashlib
from common import ROOT,OUT


def main():
    check=json.loads((OUT/'verificacion_final.json').read_text(encoding='utf8'));assert check['estado']=='OK'
    target=ROOT/'dist/Fase3_DataScience_Alcaraz-Ferreira-Rios.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in ROOT.rglob('*'):
            rel=f.relative_to(ROOT)
            if not f.is_file() or any(c in {'.git','dist','tmp','qa','__pycache__','.ipynb_checkpoints','raw'} for c in rel.parts):continue
            z.write(f,rel)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name in ['README.md','requirements.txt','src/descargar_fuentes.py','output/modelo/modelo_final.joblib','output/reports/Informe_Integrador.pdf','data/processed/victimas_limpias.parquet']:
            assert name in z.namelist()
    print('Entrega ZIP verificada:',target.name,round(target.stat().st_size/1e6,2),'MB; SHA256',hashlib.sha256(target.read_bytes()).hexdigest())


if __name__=='__main__':main()
