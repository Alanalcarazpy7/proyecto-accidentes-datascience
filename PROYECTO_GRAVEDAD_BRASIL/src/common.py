from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
SHARED_RAW = ROOT.parent / 'INVESTIGACION_DATASETS/fuentes_brasil'
RAW = SHARED_RAW if (SHARED_RAW / 'pessoas_2017.zip').exists() else ROOT / 'data/raw'
OUT = ROOT / 'output'
DATA = ROOT / 'data/processed'
for folder in [OUT / 'tables', OUT / 'figures', OUT / 'reports', OUT / 'html', DATA, ROOT / 'models', ROOT / 'notebooks']:
    folder.mkdir(parents=True, exist_ok=True)
PROTOCOL = json.loads((ROOT / 'protocolo.json').read_text(encoding='utf8'))
SEED = PROTOCOL['semilla']
os.environ.setdefault('OMP_NUM_THREADS', '6')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '6')


def save_json(obj, path):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding='utf8')


def table(df, name):
    df.to_csv(OUT / 'tables' / name, index=False, encoding='utf-8-sig')


def load_data():
    import joblib
    if (DATA / 'victimas_modelado.joblib').exists():
        return joblib.load(DATA / 'victimas_modelado.joblib')
    import pandas as pd
    if (DATA / 'victimas_limpias.parquet').exists():
        return pd.read_parquet(DATA / 'victimas_limpias.parquet')
    raise FileNotFoundError('Ejecutar python src/descargar_fuentes.py y python src/preparar.py primero')


def log(message):
    print(message, flush=True)
