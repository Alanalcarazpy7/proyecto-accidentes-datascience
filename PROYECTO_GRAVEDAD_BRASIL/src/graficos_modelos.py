import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_recall_curve, roc_curve, confusion_matrix
from sklearn.calibration import calibration_curve
from common import OUT, save_json
from fase1 import save, COLORS


def main():
    result = json.loads((OUT/'fase3_resultados.json').read_text(encoding='utf8'))
    selected = result['seleccionado']
    metrics = pd.read_csv(OUT/'tables/metricas_prueba_2025.csv')
    main_rows = metrics[metrics.regla.eq('F1_validacion')].copy()
    dtype_file=OUT/'predicciones_dtypes.json'
    score_dtypes=json.loads(dtype_file.read_text(encoding='utf8')) if dtype_file.exists() else None
    predictions = pd.read_csv(OUT/'predicciones_prueba_2025.csv.gz',dtype=score_dtypes,float_precision='round_trip')
    y = predictions.fallecido.to_numpy()
    nice = {r.modelo: ('Solo sexo/edad (LGBM)' if r.familia=='LightGBM_sexo_edad' else 'Solo sexo/edad (logística)' if r.familia=='Logistica_sexo_edad' else r.familia) for r in main_rows.itertuples()}
    text = {}
    ordered=main_rows.sort_values('AP')
    fig, ax=plt.subplots(figsize=(8,4))
    ax.barh([nice[n] for n in ordered.modelo],ordered.AP,color=[COLORS[1] if n==selected else COLORS[0] for n in ordered.modelo])
    ax.axvline(y.mean(),color='#777777',linestyle='--',label=f'Prevalencia de fallecidos: {y.mean():.2%}')
    ax.set(xlabel='Average precision de fallecidos (AP)',title='Prueba 2025: mejora al incorporar información del siniestro')
    ax.legend(fontsize=8);save('f3_01_AP_modelos.png')
    base=main_rows.set_index('modelo').loc['LightGBM_solo_sexo_edad']
    best=main_rows.set_index('modelo').loc[selected]
    text['f3_01_AP_modelos.png']=f'El modelo seleccionado alcanza AP={best.AP:.3f}, frente a {base.AP:.3f} de LightGBM con solo sexo y edad y {y.mean():.3f} de un puntaje constante. Se comparan las mismas víctimas de 2025; AP no es porcentaje de aciertos ni precisión en un único umbral.'
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for row in main_rows.itertuples():
        if row.familia in ['Dummy','Logistica_sexo_edad']:continue
        p=predictions[row.modelo].to_numpy()
        pr,re,_=precision_recall_curve(y,p);fpr,tpr,_=roc_curve(y,p)
        axes[0].plot(re,pr,label=f'{nice[row.modelo]} AP {row.AP:.2f}')
        axes[1].plot(fpr,tpr,label=f'{nice[row.modelo]} AUC {row.ROC_AUC:.2f}')
    axes[0].axhline(y.mean(),color='#777',linestyle='--');axes[1].plot([0,1],[0,1],color='#777',linestyle='--')
    axes[0].set(xlabel='Recall de fallecidos',ylabel='Precisión de fallecidos',title='Curvas precisión-recall',xlim=(0,1),ylim=(0,1))
    axes[1].set(xlabel='Tasa de falsos positivos',ylabel='Tasa de verdaderos positivos',title='Curvas ROC',xlim=(0,1),ylim=(0,1))
    for ax in axes:ax.legend(fontsize=7)
    save('f3_02_curvas.png')
    text['f3_02_curvas.png']='El aumento de recall exige aceptar más falsas alarmas. La curva PR se concentra en la clase minoritaria y su referencia depende de la prevalencia; AUC-ROC resume ordenamiento de ambas clases. Ninguna curva garantiza utilidad clínica.'
    cm=confusion_matrix(y,predictions[selected].ge(best.umbral),labels=[0,1])
    fig,axes=plt.subplots(1,2,figsize=(9,3.7))
    sns.heatmap(cm,annot=True,fmt='d',cmap='Blues',cbar=False,ax=axes[0],xticklabels=['Herida','Fallecida'],yticklabels=['Herida','Fallecida'])
    sns.heatmap(cm/cm.sum(axis=1,keepdims=True),annot=True,fmt='.1%',vmin=0,vmax=1,cmap='Blues',cbar=False,ax=axes[1],xticklabels=['Herida','Fallecida'],yticklabels=['Herida','Fallecida'])
    for ax in axes:ax.set(xlabel='Predicción',ylabel='Desenlace registrado')
    axes[0].set_title('Prueba 2025: cantidades');axes[1].set_title('Porcentaje dentro de cada clase real')
    save('f3_03_confusion.png')
    text['f3_03_confusion.png']=f'Se detectan {int(best.TP):,} de {int(best.fallecidos):,} fallecimientos ({best.recall:.1%}); quedan {int(best.FN):,} sin detectar. Hay {int(best.FP):,} falsas alarmas entre heridos; {best.precision:.1%} de las predicciones de fallecimiento son correctas.'
    all_metrics=pd.read_csv(OUT/'tables/comparacion_train_validacion_prueba.csv')
    comparable=all_metrics[all_metrics.regla.eq('F1_validacion')]
    gap=comparable.pivot(index='modelo',columns='particion',values='AP').reindex(main_rows.modelo)
    gap.index=[nice[n] for n in gap.index]
    fig,ax=plt.subplots(figsize=(9,4));gap.rename(columns={'entrenamiento_2017_2023':'Entrenamiento','validacion_umbral_2024_H2':'Validación 2024 H2','prueba_2025':'Prueba 2025'}).plot.bar(ax=ax,color=['#a6bfca','#287c9b','#d75b47'])
    ax.set(ylabel='AP de fallecidos',xlabel='',title='Aprendizaje y generalización: AP en tres períodos');ax.tick_params(axis='x',rotation=20)
    save('f3_04_generalizacion.png')
    text['f3_04_generalizacion.png']='Entrenamiento mide ajuste sobre casos vistos; validación de 2024 también se utiliza para elegir el umbral. La prueba de 2025 es posterior y no se usa para modificar el modelo. Las diferencias pueden reflejar sobreajuste y cambios de población/registro, no solo tamaño de muestra.'
    fig,ax=plt.subplots(figsize=(6.5,4))
    for name in [selected,'LightGBM_solo_sexo_edad','Dummy_siempre_herido']:
        p=predictions[name].to_numpy();freq,mean=calibration_curve(y,p,n_bins=8,strategy='quantile')
        ax.plot(mean,freq,marker='o',label=f'{nice[name]}')
    ax.plot([0,1],[0,1],color='#777',linestyle='--');ax.set(xlabel='Probabilidad estimada media',ylabel='Proporción observada de fallecidos',title='Calibración en 2025; ajuste sigmoid realizado en 2024 H1',xlim=(0,.65),ylim=(0,.65));ax.legend(fontsize=8)
    save('f3_05_calibracion.png')
    text['f3_05_calibracion.png']=f'La calibración usa datos distintos de los empleados para elegir el umbral. El Brier de prueba es {best.Brier:.4f}; valores menores son mejores. Cercanía a la diagonal describe grupos de predicciones, no certeza sobre una persona.'
    imp=pd.read_csv(OUT/'tables/importancia_permutacion_validacion.csv').head(12).sort_values('caida_AP_media')
    fig,ax=plt.subplots(figsize=(8,4.7));ax.barh(imp.variable,imp.caida_AP_media,color=COLORS[0]);ax.axvline(0,color='#777',linewidth=.8)
    ax.set(xlabel='Caída media de AP al permutar (dos repeticiones)',title='Variables útiles para el modelo: validación 2024, muestra de 15.000')
    save('f3_06_importancia.png')
    text['f3_06_importancia.png']='La caída al permutar mide utilidad predictiva condicionada al modelo, no causalidad. Las variables correlacionadas pueden sustituirse y mostrar baja importancia individual. Se calcula en validación y no se elimina ninguna variable según el resultado de prueba.'
    chosen=metrics[metrics.modelo.eq(selected)].copy()
    chosen['regla']=chosen.regla.map({'F1_validacion':'F1 fallecidos en validación','umbral_05':'Umbral 0,50','recall80_validacion':'Recall ≥80% en validación'})
    fig,ax=plt.subplots(figsize=(8,4));chosen.set_index('regla')[['precision','recall','F1_fallecido']].rename(columns={'precision':'Precisión','recall':'Recall','F1_fallecido':'F1 fallecidos'}).plot.bar(ax=ax,color=['#287c9b','#d75b47','#a68b4b'])
    ax.set(ylabel='Puntuación',xlabel='',ylim=(0,1),title='Desbalance: efecto de tres umbrales fijados antes de la prueba');ax.tick_params(axis='x',rotation=10)
    save('f3_07_umbrales.png')
    text['f3_07_umbrales.png']='Bajar el umbral incrementa la detección y las falsas alarmas. El punto llamado recall 80% se eligió en validación; su recall en 2025 puede ser distinto. No es una meta clínica aprobada ni una selección realizada usando la prueba.'
    save_json(text,OUT/'interpretaciones_fase3.json')
    return text


if __name__=='__main__':main()
