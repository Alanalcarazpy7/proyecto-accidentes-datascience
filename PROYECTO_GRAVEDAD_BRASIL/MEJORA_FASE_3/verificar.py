"""Verifica resultados almacenados, claves, cronologia y modelos reabiertos."""
import json
import hashlib
from datetime import datetime
import joblib
import nbformat
import numpy as np
import pandas as pd
from pypdf import PdfReader
from mejorar import HERE,BASE,OUT,DATA,LAYOUTS,metrics,predict,digest,writej


def main():
    checks=[]
    f=json.loads((OUT/'congelamiento.json').read_text(encoding='utf8'))
    r=json.loads((OUT/'resultados.json').read_text(encoding='utf8'))
    a=r['auditoria_prueba']
    assert f['protocolo_sha256']==digest(HERE/'protocolo.json')
    assert datetime.fromisoformat(f['fecha_congelamiento_UTC'])<datetime.fromisoformat(a['fecha_lectura_nueva_prueba_UTC'])
    checks.append('Protocolo intacto; congelamiento anterior a lectura de nueva prueba')
    before=json.loads((OUT/'integridad_experimento_original_antes.json').read_text(encoding='utf8'))
    assert all(digest(BASE/name)==sha for name,sha in before.items())
    checks.append('Modelo, protocolo y resultados del primer experimento sin cambios')
    cv=pd.read_csv(OUT/'validacion_temporal.csv')
    assert len(cv)==24 and cv.modelo.nunique()==8 and cv.validar.max()==2023 and cv.train_hasta.lt(cv.validar).all()
    ranking=pd.read_csv(OUT/'ranking_CV.csv')
    selected=ranking[ranking.elegible].iloc[0]['modelo'] if ranking.elegible.any() else 'Referencia_24_original'
    assert selected==f['seleccionado']
    checks.append('Presupuesto respetado: ocho configuraciones, 24 ajustes; seleccion solo por CV')
    d=pd.read_parquet(DATA/'victimas_contexto_2017_2025.parquet')
    test=pd.read_parquet(DATA/'prueba_2026_preparada.parquet')
    assert len(d)==754098 and len(test)==a['victimas'] and d.pesid.is_unique and test.pesid.is_unique
    assert set(test.id).isdisjoint(set(d.id)) and set(test.pesid).isdisjoint(set(d.pesid))
    assert test.fecha.min().strftime('%Y-%m-%d')==a['fecha_min_victimas'] and test.fecha.max().strftime('%Y-%m-%d')==a['fecha_max_victimas']
    assert int(test.fallecido.sum())==a['fallecidos']
    audits=pd.read_csv(OUT/'auditoria_nuevas_variables_2017_2025.csv')
    assert audits.sin_union.eq(0).all() and audits.duplicados_clave.eq(0).all() and audits.victimas.sum()==len(d)
    assert a['sin_union']==0 and a['duplicados_clave']==0
    checks.append('Uniones sin expansion; nueva prueba con claves disjuntas y cobertura reconciliada')
    forbidden={'estado_fisico','mortos','feridos','feridos_leves','feridos_graves','ilesos','classificacao_acidente','pessoas','ignorados','id','pesid','id_veiculo','causa_acidente'}
    for item in f['modelos']:
        assert digest(HERE/item['archivo'])==item['sha256']
        b=joblib.load(HERE/item['archivo'])
        assert not set(b['features'])&forbidden
        sample=d.head(20);p=predict(b,sample)
        assert len(p)==20 and np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
        assert set(b['features'])==set(sum((list(x) for x in LAYOUTS[b['spec']['bloque']]),[]))
    checks.append('Ambos pipelines reabiertos y aplicados en proceso independiente; sin predictores prohibidos')
    stored=pd.read_csv(OUT/'metricas_evaluacion.csv',float_precision='round_trip')
    preds=pd.read_csv(OUT/'predicciones_2026.csv.gz',float_precision='round_trip')
    assert digest(OUT/'predicciones_2026.csv.gz')==r['predicciones_sha256']
    assert len(preds)==len(test) and preds.fallecido.sum()==test.fallecido.sum()
    for row in stored[stored.particion.eq('2026_prueba_nueva')].itertuples():
        score=metrics(preds.fallecido.to_numpy(),preds[row.modelo].to_numpy(),row.umbral)
        for key in ['AP','ROC_AUC','precision','recall','F1_macro','F1_fallecido','accuracy','Brier','TN','FP','FN','TP']:
            assert np.isclose(score[key],getattr(row,key),atol=1e-12)
    checks.append('Metricas de tres umbrales reconciliadas con predicciones guardadas, sin reentrenar')
    old=pd.read_csv(BASE/'output/tables/metricas_prueba_2025.csv')
    original=json.loads((BASE/'output/fase3_resultados.json').read_text(encoding='utf8'))['seleccionado']
    old=old[(old.modelo==original)&old.regla.eq('F1_validacion')].iloc[0]
    fresh=stored[stored.modelo.eq(r['referencia'])&stored.particion.str.startswith('2025')&stored.regla.eq('F1_validacion')].iloc[0]
    for key in ['AP','ROC_AUC','precision','recall','F1_macro','TP','FP','FN','TN']:assert np.isclose(old[key],fresh[key],atol=1e-12)
    checks.append('La referencia reproduce exactamente las metricas originales de 2025')
    assert len(pd.read_csv(OUT/'bootstrap_pareado_2026.csv'))==300
    ci=pd.read_csv(OUT/'intervalos_mejora_2026.csv')
    assert ci.IC95_bajo.gt(0).all()
    checks.append('300 bootstrap pareados por accidente; intervalos de las cinco mejoras por encima de cero')
    book=nbformat.read(OUT/'Mejora_Fase_3.ipynb',as_version=4)
    assert all(c.execution_count is not None and not any(x.output_type=='error' for x in c.outputs) for c in book.cells if c.cell_type=='code')
    assert (OUT/'Mejora_Fase_3.html').exists()
    reader=PdfReader(OUT/'INFORME_MEJORA_FASE_3.pdf')
    assert len(reader.pages)<=5 and all(len(p.extract_text() or '')>100 for p in reader.pages)
    checks.append('Notebook ejecutado sin errores, HTML guardado e informe breve dentro de cinco paginas')
    writej(dict(estado='OK',checks=checks,paginas_pdf=len(reader.pages),modelos=f['seleccionado'],periodo_2026=[a['fecha_min_victimas'],a['fecha_max_victimas']],n_prueba=a['victimas'],nota='Verificacion aritmetica y de integridad, sin cambiar seleccion/umbrales; QA visual se informa aparte.'),OUT/'verificacion_final.json')
    for c in checks:print('OK',c)
    print('Paginas PDF:',len(reader.pages))


if __name__=='__main__':main()
