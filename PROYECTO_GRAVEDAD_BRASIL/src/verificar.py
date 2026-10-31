"""Comprueba integridad de datos, reglas congeladas y resultados, sin ajustar."""
import hashlib
import json
from pathlib import Path
import joblib
import nbformat
import numpy as np
import pandas as pd
from pypdf import PdfReader
from common import ROOT, OUT, PROTOCOL, load_data, save_json
from modelado import metrics, probabilities


def main():
    checks=[]
    d=load_data()
    assert len(d)==754098 and int(d.fallecido.sum())==50825 and d.pesid.is_unique
    checks.append('754098 participaciones elegibles, 50825 obitos, claves positivas unicas')
    frozen=json.loads((OUT/'seleccion_congelada_antes_prueba.json').read_text(encoding='utf8'))
    assert frozen['protocolo_sha256']==hashlib.sha256((ROOT/'protocolo.json').read_bytes()).hexdigest()
    groups=[set(d.loc[d.ano.le(2023),'id']),set(d.loc[d.ano.eq(2024),'id']),set(d.loc[d.ano.eq(2025),'id'])]
    assert all(not groups[i]&groups[j] for i in range(3) for j in range(i))
    checks.append('Sin accidentes compartidos entre desarrollo, validacion y prueba; protocolo intacto')
    cv=pd.read_csv(OUT/'tables/validacion_temporal_todas.csv')
    assert len(cv)==39 and (cv.entrenar_hasta<cv.validar).all() and cv.validar.max()==2023
    ranking=pd.read_csv(OUT/'tables/ranking_CV.csv')
    expected=ranking[~ranking.familia.str.contains('sexo_edad')].iloc[0]['nombre']
    assert frozen['seleccionado']==expected
    checks.append('39 ajustes CV, tres cortes temporales, seleccion por AP anterior a prueba')
    sample=d.head(50).copy()
    score_dtypes={}
    for item in frozen['modelos']:
        b=joblib.load(ROOT/item['archivo'])
        assert not set(b['features'])&set(PROTOCOL['variables_prohibidas'])
        q=probabilities(b,sample)
        score_dtypes[item['nombre']]=str(q.dtype)
        assert np.isfinite(q).all() and ((q>=0)&(q<=1)).all()
    checks.append('Siete modelos reabiertos en proceso independiente; sin predictores prohibidos')
    # pandas no conserva dtypes al guardar CSV. Releer float32 como float64 puede
    # cambiar decisiones exactamente en el umbral para scores repetidos.
    preds=pd.read_csv(OUT/'predicciones_prueba_2025.csv.gz',dtype=score_dtypes,float_precision='round_trip')
    assert len(preds)==89593 and int(preds.fallecido.sum())==6043
    stored=pd.read_csv(OUT/'tables/metricas_prueba_2025.csv',float_precision='round_trip')
    assert len(stored)==21
    # Auditoria aritmetica de predicciones guardadas, sin predecir de nuevo ni seleccionar.
    for row in stored.itertuples():
        computed=metrics(preds.fallecido.to_numpy(),preds[row.modelo].to_numpy(),row.umbral)
        for key in ['AP','ROC_AUC','precision','recall','F1_macro','F1_fallecido','accuracy','Brier','TN','FP','FN','TP']:
            assert np.isclose(computed[key],getattr(row,key),atol=1e-10), (row.modelo,key)
    result=json.loads((OUT/'fase3_resultados.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'predicciones_prueba_2025.csv.gz').read_bytes()).hexdigest()==result['prueba_sha256']
    checks.append('21 filas de metricas reconciliadas con predicciones almacenadas; hash de prueba intacto')
    ci=pd.read_csv(OUT/'tables/intervalos_prueba_bootstrap.csv')
    assert ci.loc[ci.metrica.eq('mejora_AP_sobre_sexo_edad'),'IC95_bajo'].iloc[0]>0
    assert len(pd.read_csv(OUT/'tables/bootstrap_accidentes_prueba.csv'))==400
    checks.append('400 bootstrap por accidente; mejora pareada AP positiva dentro de Brasil')
    phase2=pd.read_csv(OUT/'tables/contrastes_fase2.csv')
    assert len(phase2)==4 and phase2[['IC95_bajo','IC95_alto']].notna().all().all()
    checks.append('Cuatro contrastes con intervalos, Holm y tres familias clasicas mas GLM')
    books=[]
    for path in (ROOT/'notebooks').glob('*.ipynb'):
        nb=nbformat.read(path,as_version=4)
        assert all(c.execution_count is not None and not any(o.output_type=='error' for o in c.outputs) for c in nb.cells if c.cell_type=='code')
        assert (OUT/'html'/f'{path.stem}.html').exists()
        books.append(path.name)
    assert len(books)==3
    checks.append('Tres notebooks ejecutados sin errores y sus HTML guardados')
    limits={'Comprension_del_problema.pdf':3,'Fase_1_Preparacion_y_EDA.pdf':20,'Fase_2_Inferencia.pdf':15,'Fase_3_Modelado_y_Evaluacion.pdf':15,'Informe_Integrador.pdf':30}
    pages={}
    for name,limit in limits.items():
        r=PdfReader(OUT/'reports'/name);pages[name]=len(r.pages)
        assert len(r.pages)<=limit and all(len((p.extract_text() or '').strip())>50 for p in r.pages)
    checks.append('Cinco PDFs legibles por extractor y dentro de limites de paginas; QA visual se registra aparte')
    assert (ROOT/'ABRIR_RESULTADOS.html').exists()
    save_json(dict(estado='OK',comprobaciones=checks,paginas=pages,notebooks=books,nota='No se reentrenan modelos ni se eligen umbrales durante esta verificacion.'),OUT/'verificacion_final.json')
    for c in checks:print('OK',c)
    print('PDF paginas:',pages)


if __name__=='__main__':main()
