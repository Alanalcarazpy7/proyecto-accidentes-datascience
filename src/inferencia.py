"""Aplica el unico modelo final a caracteristicas preparadas, sin objetivo."""
import argparse
import joblib
import pandas as pd
from common import OUT
from preparar import CAT,NUM
from modelado import predict


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--entrada',required=True);p.add_argument('--salida',required=True);a=p.parse_args()
    b=joblib.load(OUT/'modelo/modelo_final.joblib');d=pd.read_csv(a.entrada,dtype={c:str for c in CAT})
    missing=set(b['features'])-set(d.columns)
    if missing:raise ValueError('Faltan caracteristicas preparadas: '+str(sorted(missing)))
    for c in CAT:d[c]=d[c].fillna('DESCONOCIDO')
    for c in NUM:d[c]=pd.to_numeric(d[c],errors='raise')
    prob=predict(b,d);r=d[[c for c in ['id','pesid'] if c in d]].copy()
    r['p_fallecimiento_registrado']=prob;r['clase_predicha']=pd.Series(prob>=b['umbral']).map({True:'Fallecida',False:'Herida'});r['umbral']=b['umbral']
    r.to_csv(a.salida,index=False,encoding='utf-8-sig');print(r.to_string(index=False))


if __name__=='__main__':main()
