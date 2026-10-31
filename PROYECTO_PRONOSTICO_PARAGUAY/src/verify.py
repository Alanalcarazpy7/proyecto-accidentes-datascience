"""Verificacion de integridad de datos, protocolo y reproduccion de predicciones."""
import json

import joblib
import nbformat
import numpy as np
import pandas as pd
from pypdf import PdfReader

from common import ROOT,OUT,load_series,save_json
from models import FEATURES,forecast,supervised


def main(check_notebooks=True,check_pdf=True):
    results={}
    df=load_series();audit=json.loads((OUT/'auditoria_datos.json').read_text(encoding='utf-8'))
    assert len(df)==108 and df.index.is_unique
    assert df.index.equals(pd.date_range('2016-01-01','2024-12-01',freq='MS'))
    results['serie_completa_unica']=True
    assert audit['filas_extraidas']==168 and audit['duplicados_coincidentes']==60
    results['originales_y_versiones_validados']=True
    frozen=json.loads((OUT/'seleccion_congelada_antes_prueba.json').read_text(encoding='utf-8'))
    ranking=pd.read_csv(OUT/'tables/ranking_configuraciones_CV.csv')
    assert frozen['seleccion']['id']==ranking.iloc[0]['id']
    results['seleccion_por_validacion']=True
    cv=pd.read_csv(OUT/'tables/predicciones_validacion_todas.csv',parse_dates=['fecha','origen'])
    assert (cv.origen<cv.fecha).all() and cv.fecha.max()<pd.Timestamp('2023-01-01')
    results['origenes_CV_solo_pasado']=True
    evaluated=joblib.load(OUT/'models/modelo_evaluado_2024.joblib')
    assert evaluated['model']['history'].index.max()==pd.Timestamp('2023-12-01')
    results['modelo_prueba_no_entrenado_con_2024']=True
    pred=forecast(evaluated['model']);stored=pd.read_csv(OUT/'tables/predicciones_prueba_2024.csv')
    stored=stored.loc[stored.id==frozen['seleccion']['id']]
    assert np.allclose(pred,stored.prediccion,rtol=1e-10,atol=1e-10)
    results['prediccion_2024_reproducida_desde_modelo']=True
    actual=df.loc['2024','accidentes'].to_numpy();reported=json.loads((OUT/'fase3_resultados.json').read_text(encoding='utf-8'))['metricas_prueba_seleccionado']
    assert abs(np.mean(np.abs(actual-pred.to_numpy()))-reported['MAE'])<1e-10
    assert abs(np.sqrt(np.mean((actual-pred.to_numpy())**2))-reported['RMSE'])<1e-10
    results['metricas_verificadas_por_calculo_independiente']=True
    production=joblib.load(OUT/'models/modelo_pronostico.joblib')
    saved=pd.read_csv(OUT/'tables/pronostico_2025_corte_2024.csv')
    assert np.allclose(forecast(production['model']),saved.prediccion,rtol=1e-10,atol=1e-10)
    results['proyeccion_reproducida']=True
    X,_=supervised(df.loc[:'2022-12-01','accidentes'])
    assert list(X.columns)==FEATURES and not {'choque','tasa_diaria_mes','accidentes'}.intersection(X.columns)
    results['componentes_contemporaneos_excluidos']=True
    # Comprobar explicitamente que el objetivo de cada fila no entra en su propia X.
    altered=df.loc[:'2022-12-01','accidentes'].copy();altered.iloc[-1]=9999999
    Xaltered,_=supervised(altered)
    assert np.array_equal(X.iloc[-1].to_numpy(),Xaltered.iloc[-1].to_numpy())
    results['ultimo_objetivo_no_filtrado_en_sus_predictores']=True
    if check_notebooks:
        for path in (ROOT/'notebooks').glob('*.ipynb'):
            nb=nbformat.read(path,as_version=4);cells=[c for c in nb.cells if c.cell_type=='code']
            assert cells and all(c.execution_count is not None for c in cells)
            assert not any(o.output_type=='error' for c in cells for o in c.get('outputs',[]))
            assert (OUT/'html'/path.with_suffix('.html').name).exists()
        assert len(list((ROOT/'notebooks').glob('*.ipynb')))==3
        results['tres_notebooks_ejecutados_sin_errores_y_HTML']=True
    if check_pdf:
        limits={'Fase_1_Preparacion_y_EDA.pdf':20,'Fase_2_Inferencia.pdf':15,
                'Fase_3_Modelado_y_Evaluacion.pdf':15,'Informe_Integrador.pdf':30}
        counts={name:len(PdfReader(OUT/'reports'/name).pages) for name in limits}
        assert all(counts[name]<=limit for name,limit in limits.items())
        assert 2<=len(PdfReader(OUT/'reports/Comprension_del_problema.pdf').pages)<=3
        results['PDF_dentro_limites']=counts
    save_json('verificacion_final.json',results)
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return results


if __name__=='__main__':main()
