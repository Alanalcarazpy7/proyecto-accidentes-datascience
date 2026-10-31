"""Analisis del unico modelo final; reutiliza la prueba historica registrada."""
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score
from sklearn.calibration import calibration_curve
from common import ROOT,OUT,load_data,save_json,table
from modelado import predict
from fase1 import save,COLORS


def main():
    folder=OUT/'modelado/final'
    r=json.loads((folder/'resultados.json').read_text(encoding='utf8'))
    chosen=r['seleccionado'];d=load_data();b=joblib.load(OUT/'modelo/modelo_final.joblib')
    predictions=pd.read_csv(folder/'predicciones_2026.csv.gz',float_precision='round_trip')
    test=d[d.ano.eq(2026)].merge(predictions[['pesid',chosen]],on='pesid',how='left',validate='one_to_one')
    assert test[chosen].notna().all()
    texts={
        '01_busqueda_CV.png':'Se compararon ocho configuraciones en tres cortes anteriores a prueba. La variante elegida supera la referencia en los tres cortes; la grilla no se amplio mirando 2026.',
        '02_comparacion_2026.png':'Sobre las mismas victimas de enero a septiembre de 2026, la version de 31 variables mejora AUC, AP, F1 macro, precision y recall. Los umbrales se fijaron con 2024 y se conserva prevalencia natural.',
        '03_curvas_2026.png':'La curva precision-recall del candidato muestra mejor ordenamiento de la clase minoritaria. La prevalencia sigue influyendo en precision y AP; AUC 0,845 no equivale a detectar el 84,5% de fallecidos.',
        '04_confusion_2026.png':'El modelo final detecta 1.953 de 4.610 fallecidos y omite 2.657; produce 3.277 falsas alarmas. Frente a la referencia son 132 detecciones mas y 717 falsas alarmas menos, sin cambiar reglas con prueba.',
    }
    metrics=pd.read_csv(folder/'comparacion_completa.csv')
    selected=metrics[metrics.modelo.eq(chosen)&metrics.regla.eq('F1_validacion')]
    labels={'entrenamiento_2017_2023':'Entrenamiento','validacion_umbral_2024_H2':'Validacion 2024 H2','2025_retroactivo_ya_conocido':'2025 retrospectivo','2026_prueba_nueva':'2026 posterior'}
    fig,ax=plt.subplots(figsize=(8,3.8));ax.bar([labels[x] for x in selected.particion],selected.AP,color=['#aac0cc','#287c9b','#689db1','#d75b47'])
    ax.set(ylabel='Average precision de fallecidos',title='Ajuste y generalizacion del modelo final');ax.tick_params(axis='x',rotation=10)
    save('f3_05_generalizacion.png')
    texts['f3_05_generalizacion.png']='AP de entrenamiento 0,456 frente a 0,358 en validacion y 0,352 en 2026 muestra optimismo del ajuste. La estabilidad entre periodos posteriores es favorable, sin garantizar que desaparezcan sobreajuste o cambios de registro.'
    fig,ax=plt.subplots(figsize=(6.7,4));freq,mean=calibration_curve(test.fallecido,test[chosen],n_bins=8,strategy='quantile')
    ax.plot(mean,freq,marker='o',color=COLORS[0]);ax.plot([0,1],[0,1],linestyle='--',color='#888')
    ax.set(xlabel='Probabilidad estimada media',ylabel='Proporcion observada de fallecidos',title='Calibracion del modelo final en el corte de 2026',xlim=(0,.7),ylim=(0,.7))
    save('f3_06_calibracion.png')
    texts['f3_06_calibracion.png']='La sigmoid se ajusto en 2024 H1 con prevalencia natural. El grafico evalua fiabilidad por grupos de puntuaciones; no implica certeza individual. Brier y log loss complementan, sin aislar calibracion de todos los otros componentes.'
    val=d[d.ano.eq(2024)&d.fecha.ge('2024-07-01')].sample(10000,random_state=42)
    ap=average_precision_score(val.fallecido,predict(b,val));rng=np.random.default_rng(42);imp=[]
    for c in b['features']:
        drops=[]
        for _ in range(2):
            x=val.copy();x[c]=rng.permutation(x[c].to_numpy());drops.append(ap-average_precision_score(val.fallecido,predict(b,x)))
        imp.append(dict(variable=c,caida_AP_media=float(np.mean(drops)),sd=float(np.std(drops)),particion='validacion_2024_H2',n=len(val)))
    importance=pd.DataFrame(imp).sort_values('caida_AP_media',ascending=False);table(importance,'importancia_modelo_final.csv')
    z=importance.head(12).sort_values('caida_AP_media');fig,ax=plt.subplots(figsize=(8,4.3));ax.barh(z.variable,z.caida_AP_media,color=COLORS[0]);ax.axvline(0,color='#999',linewidth=.8)
    ax.set(xlabel='Caida de AP al permutar',title='Informacion aprovechada por el modelo final: validacion')
    save('f3_07_importancia.png')
    texts['f3_07_importancia.png']='La importancia se calcula en 10.000 casos de validacion, con dos repeticiones; no se eligen variables usando prueba. Las variables correlacionadas pueden sustituirse y compartir importancia. Utilidad predictiva no demuestra causalidad.'
    m=pd.DataFrame(r['metricas']);m=m[m.modelo.eq(chosen)&m.particion.eq('2026_prueba_nueva')]
    m['regla']=m.regla.map({'F1_validacion':'F1 fallecidos elegido','umbral_05':'Umbral 0,50','recall80_validacion':'Recall alto elegido'})
    fig,ax=plt.subplots(figsize=(7.6,3.7));m.set_index('regla')[['precision','recall','F1_fallecido']].plot.bar(ax=ax,color=['#287c9b','#d75b47','#a18b53'])
    ax.set(ylabel='Puntuacion',xlabel='',ylim=(0,1),title='Compromiso entre deteccion y falsas alarmas');ax.tick_params(axis='x',rotation=8)
    save('f3_08_umbrales.png')
    texts['f3_08_umbrales.png']='El umbral principal detecta 42,36% de fallecidos con precision 37,34%. La regla de mayor deteccion alcanza 80,95% con precision 17,03%. Ambas se definieron con validacion; ninguna representa una politica clinica aprobada.'
    groups=[]
    test['grupo_edad']=pd.cut(test.idade,[0,17,29,44,59,110],labels=['1-17','18-29','30-44','45-59','60-110']).astype(str)
    from comparacion import metrics as score
    for c in ['sexo','grupo_edad','tipo_envolvido','tipo_veiculo','familia_otro_vehiculo','uf']:
        for value,g in test.groupby(c,observed=True):
            if len(g)<100 or g.fallecido.nunique()<2:continue
            groups.append(dict(variable=c,grupo=str(value),**score(g.fallecido.to_numpy(),g[chosen].to_numpy(),b['umbral'])))
    table(pd.DataFrame(groups),'errores_por_grupo_modelo_final.csv')
    errors=test.loc[test[chosen].ge(b['umbral']).ne(test.fallecido.astype(bool)),['id','pesid','fallecido','idade','sexo','tipo_envolvido','tipo_veiculo','familia_otro_vehiculo',chosen]].copy()
    errors['tipo_error']=np.where(errors.fallecido.eq(1),'FN','FP')
    errors['confianza_erronea']=np.where(errors.fallecido.eq(1),1-errors[chosen],errors[chosen])
    table(errors.sort_values('confianza_erronea',ascending=False).head(20),'errores_mayor_confianza_modelo_final.csv')
    selected_row=next(x for x in r['metricas'] if x['modelo']==chosen and x['particion']=='2026_prueba_nueva' and x['regla']=='F1_validacion')
    save_json(dict(seleccionado=chosen,prueba=selected_row,intervalos=r['intervalos_delta'],auditoria_prueba=r['auditoria_prueba'],predictores=b['features'],nota='Modelo final elegido en el experimento historico; 2025 es retrospectivo y 2026 fue posterior al congelamiento original.'),OUT/'fase3_resultados.json')
    save_json(texts,OUT/'interpretaciones_fase3.json')
    return texts


if __name__=='__main__':main()
