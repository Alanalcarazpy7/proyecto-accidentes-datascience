from pathlib import Path
import json
import os

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output';DATA=ROOT/'data/processed';RAW=ROOT/'data/raw'
PROTOCOL=json.loads((ROOT/'protocolo.json').read_text(encoding='utf8'))
SEED=42
os.environ.setdefault('OMP_NUM_THREADS','4')
for p in [OUT/'tables',OUT/'figures',OUT/'reports',OUT/'html',OUT/'modelo',DATA]:p.mkdir(parents=True,exist_ok=True)


def save_json(obj,path):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf8')


def table(df,name):df.to_csv(OUT/'tables'/name,index=False,encoding='utf-8-sig')
def load_data():
    import pandas as pd
    return pd.read_parquet(DATA/'victimas_limpias.parquet')
def log(s):print(s,flush=True)
