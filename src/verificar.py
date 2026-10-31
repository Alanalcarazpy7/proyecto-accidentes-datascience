"""Integridad de la entrega unica y reconciliacion de resultados registrados."""
import json,hashlib
import joblib
import nbformat
import numpy as np
import pandas as pd
from pypdf import PdfReader
from common import ROOT,OUT,DATA,load_data,save_json
from preparar import FEATURES
from modelado import predict
from comparacion import metrics


def main():
    checks=[];d=load_data()
    assert len(d)==821689 and d.pesid.is_unique and int(d.fallecido.sum())==55435
    assert len(d.columns)==37 and len(FEATURES)==31
    assert d.ano.le(2025).sum()==754098 and d.ano.eq(2026).sum()==67591
    partitions=[set(g.id) for _,g in d.assign(split=np.select([d.ano.le(2023),d.ano.eq(2024),d.ano.eq(2025)],['train','val','retro'],default='test')).groupby('split')]
    assert all(not partitions[i]&partitions[j] for i in range(len(partitions)) for j in range(i))
    checks.append('Unico dataset de 821689 participaciones, claves unicas y particiones sin accidentes compartidos')
    models=list((OUT/'modelo').glob('*.joblib'));assert len(models)==1
    b=joblib.load(models[0]);assert len(b['features'])==31 and set(b['features'])==set(FEATURES)
    f=json.loads((ROOT/'data/metodologia/congelamiento_final_original.json').read_text(encoding='utf8'))
    selected=next(x for x in f['modelos'] if x['nombre']==f['seleccionado'])
    assert hashlib.sha256(models[0].read_bytes()).hexdigest()==selected['sha256']
    assert not set(b['features'])&{'id','pesid','id_veiculo','estado_fisico','mortos','ilesos','feridos','feridos_leves','feridos_graves','classificacao_acidente','causa_acidente'}
    checks.append('Unico modelo final de 31 entradas, hash identico al ganador registrado y sin variables prohibidas')
    predicted=pd.read_csv(OUT/'modelado/final/predicciones_2026.csv.gz',float_precision='round_trip')
    t=d[d.ano.eq(2026)].merge(predicted[['pesid',f['seleccionado']]],on='pesid',how='left',validate='one_to_one')
    assert len(t)==67591 and t[f['seleccionado']].notna().all()
    # Una muestra verifica el traslado del modelo/datos, no selecciona nada.
    sample=t.sample(100,random_state=42)
    np.testing.assert_allclose(predict(b,sample),sample[f['seleccionado']],rtol=0,atol=1e-12)
    rows=pd.read_csv(OUT/'modelado/final/metricas_evaluacion.csv',float_precision='round_trip')
    for row in rows[rows.particion.eq('2026_prueba_nueva')].itertuples():
        computed=metrics(predicted.fallecido.to_numpy(),predicted[row.modelo].to_numpy(),row.umbral)
        for key in ['AP','ROC_AUC','precision','recall','F1_macro','accuracy','Brier','TP','FP','TN','FN']:
            assert np.isclose(computed[key],getattr(row,key),atol=1e-12)
    checks.append('Resultados y predicciones de 2026 conservados; inferencia trasladada coincide con el modelo elegido')
    audit=pd.read_csv(OUT/'tables/auditoria_preparacion_por_anio.csv');assert audit.sin_union.eq(0).all() and audit.duplicados_clave.eq(0).all() and audit.victimas.sum()==len(d)
    assert len(pd.read_csv(OUT/'tables/diccionario_original.csv'))==65
    assert len(pd.read_csv(OUT/'tables/diccionario_final.csv'))==37
    assert len(pd.read_csv(OUT/'tables/contrastes_fase2.csv'))==4
    assert len(json.loads((OUT/'fase1_resultados.json').read_text(encoding='utf8'))['interpretaciones'])>=8
    checks.append('Auditoria, diccionarios original/final, bitacora, cuatro contrastes y diez visualizaciones exploratorias')
    for name in ['Fase_1_Preparacion_EDA','Fase_2_Inferencia','Fase_3_Modelado']:
        book=nbformat.read(ROOT/'notebooks'/f'{name}.ipynb',as_version=4)
        assert all(c.execution_count is not None and not any(x.output_type=='error' for x in c.outputs) for c in book.cells if c.cell_type=='code')
        assert (OUT/'html'/f'{name}.html').exists()
    checks.append('Exactamente tres notebooks ejecutados sin errores y tres HTML')
    limits={'Comprension_del_problema.pdf':3,'Fase_1_Preparacion_y_EDA.pdf':20,'Fase_2_Inferencia.pdf':15,'Fase_3_Modelado_y_Evaluacion.pdf':15,'Informe_Integrador.pdf':30}
    pages={}
    for name,limit in limits.items():
        r=PdfReader(OUT/'reports'/name);pages[name]=len(r.pages);assert len(r.pages)<=limit
        assert all(len(p.extract_text() or '')>50 for p in r.pages)
    checks.append('Cinco PDF dentro de los limites de la catedra')
    # Ningun modulo depende de las carpetas que se eliminan durante la limpieza.
    for path in (ROOT/'src').glob('*.py'):
        text=path.read_text(encoding='utf8');compile(text,str(path),'exec')
        if path.name!=__file__.split('\\')[-1].split('/')[-1]:
            assert all(x not in text for x in ['INVESTIGACION_DATASETS','PROYECTO_GRAVEDAD_BRASIL/','PROYECTO_PRONOSTICO_PARAGUAY','MEJORA_FASE_3/']),path.name
    checks.append('Codigo compilable y sin dependencias de carpetas descartadas')
    save_json(dict(estado='OK',comprobaciones=checks,paginas=pages,modelo='output/modelo/modelo_final.joblib',datos='data/processed/victimas_limpias.parquet',pendiente_humano='Legajos y revision/comprension del grupo; exposicion oral de cierre'),OUT/'verificacion_final.json')
    for c in checks:print('OK',c)
    print('Paginas:',pages)


if __name__=='__main__':main()
