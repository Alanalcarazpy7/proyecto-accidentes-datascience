"""Aplica el unico modelo final a caracteristicas preparadas, sin objetivo."""
import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.special import logit

OUT=Path(__file__).resolve().parents[1]/'output'


def predict(bundle,d):
    """Usa el modelo y la calibracion guardados, sin volver a entrenar."""
    prob=bundle['pipeline'].predict_proba(d[bundle['features']])[:,1]
    if bundle.get('calibrador') is not None:
        prob=bundle['calibrador'].predict_proba(logit(np.clip(prob,1e-7,1-1e-7)).reshape(-1,1))[:,1]
    return np.asarray(prob,dtype=np.float64)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--entrada',required=True);p.add_argument('--salida',required=True);a=p.parse_args()
    b=joblib.load(OUT/'modelo/modelo_final.joblib')
    columns={name:list(cols) for name,transformer,cols in b['pipeline']['prep'].transformers}
    CAT,NUM=columns['cat'],columns['num']
    d=pd.read_csv(a.entrada,dtype={c:str for c in CAT})
    missing=set(b['features'])-set(d.columns)
    if missing:raise ValueError('Faltan caracteristicas preparadas: '+str(sorted(missing)))
    for c in CAT:d[c]=d[c].fillna('DESCONOCIDO')
    for c in NUM:d[c]=pd.to_numeric(d[c],errors='raise')
    prob=predict(b,d);r=d[[c for c in ['id','pesid'] if c in d]].copy()
    r['p_fallecimiento_registrado']=prob;r['clase_predicha']=pd.Series(prob>=b['umbral']).map({True:'Fallecida',False:'Herida'});r['umbral']=b['umbral']
    Path(a.salida).parent.mkdir(parents=True,exist_ok=True)
    r.to_csv(a.salida,index=False,encoding='utf-8-sig');print(r.to_string(index=False))


if __name__=='__main__':main()
