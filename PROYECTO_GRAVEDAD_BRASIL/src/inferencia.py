"""Aplica el pipeline guardado a filas nuevas YA preparadas, sin objetivo.

python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida output/ejemplo_predicciones.csv
La preparacion determinista esta documentada en preparar.py; no acepta el
CSV PRF bruto como si sus campos fueran las 24 caracteristicas transformadas.
"""
import argparse
import joblib
import pandas as pd
from common import ROOT
from modelado import probabilities
from preparar import CAT, NUM


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrada',required=True)
    parser.add_argument('--salida',required=True)
    args=parser.parse_args()
    d=pd.read_csv(args.entrada,dtype={c:str for c in CAT})
    for c in CAT:
        if c in d:d[c]=d[c].fillna('DESCONOCIDO')
    for c in NUM:
        if c in d:d[c]=pd.to_numeric(d[c],errors='raise')
    bundle=joblib.load(ROOT/'models/modelo_seleccionado.joblib')
    missing=set(bundle['features'])-set(d.columns)
    if missing:raise ValueError('Faltan caracteristicas preparadas: '+', '.join(sorted(missing)))
    p=probabilities(bundle,d)
    out=d[[c for c in ['id','pesid'] if c in d]].copy()
    out['p_fallecimiento_registrado']=p
    out['clase_predicha']=pd.Series(p>=bundle['umbral']).map({False:'Herida',True:'Fallecida'})
    out['umbral']=bundle['umbral']
    out.to_csv(args.salida,index=False,encoding='utf-8-sig')
    print(out.to_string(index=False))


if __name__=='__main__':main()
