"""Aplicar la especificacion guardada; opcionalmente reajustar a nuevo historial.

python src/inference.py --meses 12 --salida output/tables/nuevo_pronostico.csv
python src/inference.py --historial nuevo.csv --meses 12
El historial debe tener fecha (mensual) y accidentes, sin huecos ni duplicados.
"""
import argparse

import joblib
import numpy as np
import pandas as pd

from common import ROOT
from models import fit_model,forecast


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo',default=str(ROOT/'output/models/modelo_pronostico.joblib'))
    parser.add_argument('--historial',default=None)
    parser.add_argument('--meses',type=int,default=12)
    parser.add_argument('--salida',default=str(ROOT/'output/tables/pronostico_inferencia.csv'))
    args=parser.parse_args()
    if not 1<=args.meses<=12:raise ValueError('Este diseno evalua horizontes de uno a doce meses.')
    artifact=joblib.load(args.modelo);model=artifact['model']
    if args.historial:
        raw=pd.read_csv(args.historial,parse_dates=['fecha'])
        if not {'fecha','accidentes'}.issubset(raw):raise ValueError('Faltan fecha o accidentes.')
        if raw.fecha.duplicated().any():raise ValueError('Hay meses duplicados.')
        raw=raw.sort_values('fecha');expected=pd.date_range(raw.fecha.iloc[0],raw.fecha.iloc[-1],freq='MS')
        if len(raw)<36 or not raw.fecha.reset_index(drop=True).equals(pd.Series(expected)):
            raise ValueError('Se requieren al menos 36 meses consecutivos, con fecha el primer dia del mes.')
        if raw.accidentes.isna().any() or (raw.accidentes<0).any() or not np.isfinite(raw.accidentes).all() or not np.equal(raw.accidentes,np.floor(raw.accidentes)).all():
            raise ValueError('Los conteos deben ser enteros no negativos.')
        model=fit_model(raw.set_index('fecha').accidentes,artifact['selected_spec'])
    pred=forecast(model,args.meses)
    frame=pd.DataFrame({'fecha':pred.index,'prediccion':pred.to_numpy(),
                        'origen':str(model['history'].index[-1].date())})
    frame.to_csv(args.salida,index=False,encoding='utf-8-sig')
    print(frame.to_string(index=False))
    print('Total del horizonte:',round(pred.sum(),2))


if __name__=='__main__':main()
