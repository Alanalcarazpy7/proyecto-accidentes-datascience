"""Inferencia del candidato con columnas preparadas y contexto completo del siniestro."""
import argparse
import json
import joblib
import pandas as pd
from mejorar import HERE,OUT,predict,LAYOUTS


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--entrada',required=True);ap.add_argument('--salida',required=True);args=ap.parse_args()
    f=json.loads((OUT/'congelamiento.json').read_text(encoding='utf8'))
    item=next(x for x in f['modelos'] if x['nombre']==f['seleccionado'])
    b=joblib.load(HERE/item['archivo']);cats,nums=LAYOUTS[b['spec']['bloque']]
    d=pd.read_csv(args.entrada,dtype={c:str for c in cats})
    missing=set(b['features'])-set(d.columns)
    if missing:raise ValueError('Faltan columnas preparadas: '+str(sorted(missing)))
    for c in cats:d[c]=d[c].fillna('DESCONOCIDO')
    for c in nums:d[c]=pd.to_numeric(d[c],errors='raise')
    p=predict(b,d);result=d[[c for c in ['id','pesid'] if c in d]].copy()
    result['p_fallecimiento_registrado']=p;result['clase_predicha']=pd.Series(p>=b['umbral']).map({False:'Herida',True:'Fallecida'});result['umbral']=b['umbral']
    result.to_csv(args.salida,index=False,encoding='utf-8-sig');print(result.to_string(index=False))


if __name__=='__main__':main()
