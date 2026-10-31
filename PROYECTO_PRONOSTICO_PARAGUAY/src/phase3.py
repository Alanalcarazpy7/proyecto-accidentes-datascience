"""Busqueda temporal, congelacion, calibracion 2023 y prueba final 2024.

La seleccion se realiza ANTES de leer objetivos de prueba para evaluar. La
reproduccion usa la misma grilla fija; no busca alternativas tras ver 2024.
"""
import json
import platform

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.stats.diagnostic import acorr_ljungbox

from common import OUT, PROTOCOL, ROOT, SEED, load_series, plt, protocol_hash, save_figure, save_json, save_table, sha256
from models import FEATURES, fit_model, fitted_values, forecast, specifications, supervised


def metrics(actual,pred,scale=None):
    a=np.asarray(actual,float);p=np.asarray(pred,float)
    result=dict(MAE=mean_absolute_error(a,p),RMSE=np.sqrt(mean_squared_error(a,p)),
                MAPE=100*np.mean(np.abs((a-p)/a)) if np.all(a>0) else np.nan,
                R2=r2_score(a,p),sesgo=float(np.mean(p-a)),
                total_real=float(a.sum()),total_predicho=float(p.sum()),
                error_total=float(p.sum()-a.sum()))
    if scale is not None:result['MASE']=result['MAE']/scale if scale>0 else np.nan
    return result


def main(force=False):
    report=OUT/'fase3_resultados.json'
    fingerprint=sha256(ROOT/'data/processed/serie_mensual.csv')+'-'+protocol_hash()
    if report.exists() and not force:
        existing=json.loads(report.read_text(encoding='utf-8'))
        if existing.get('fingerprint')==fingerprint:
            print('Fase 3: resultados reproducibles existentes; no se repite seleccion ni prueba.')
            return existing
    data=load_series()
    dev=data.loc[:'2022-12-01','accidentes'].astype(float)
    specs=specifications();save_json('especificaciones_antes_ajuste.json',specs)
    grid=[];cv_records=[];fold_fits={};warnings_log=[]
    for spec in specs:
        predictions=[];actuals=[];ok=True
        for year in PROTOCOL['anos_validacion']:
            history=dev.loc[:f'{year-1}-12-01'];actual=dev.loc[f'{year}-01-01':f'{year}-12-01']
            try:
                fitted=fit_model(history,spec);pred=forecast(fitted)
                if len(actual)!=12:raise ValueError('Validacion incompleta.')
                predictions.extend(pred);actuals.extend(actual)
                fm=metrics(actual,pred)
                ins=fitted_values(fitted)
                fold_fits[(spec['id'],year)]=fitted
                for date,a,p in zip(actual.index,actual,pred):
                    cv_records.append(dict(id=spec['id'],familia=spec['familia'],ano_validacion=year,
                                           origen=str(history.index[-1].date()),fecha=str(date.date()),real=a,prediccion=p))
                warnings_log.extend(dict(id=spec['id'],ano=year,advertencia=w) for w in fitted['warnings'])
                grid.append(dict(id=spec['id'],familia=spec['familia'],parametros=json.dumps(spec['parametros']),
                                 ano_validacion=year,n_entrenamiento=len(history),n_supervisado=max(0,len(history)-12),
                                 MAE_entrenamiento=metrics(history.loc[ins.index],ins)['MAE'],**fm,estado='OK'))
            except Exception as exc:
                ok=False;grid.append(dict(id=spec['id'],familia=spec['familia'],parametros=json.dumps(spec['parametros']),
                                          ano_validacion=year,estado=f'ERROR: {type(exc).__name__}: {exc}'))
        print('Validacion',spec['id'],spec['familia'],'OK' if ok else 'con fallo',flush=True)
    grid_df=pd.DataFrame(grid);save_table('busqueda_completa_por_corte.csv',grid_df)
    cv_df=pd.DataFrame(cv_records);save_table('predicciones_validacion_todas.csv',cv_df)
    eligible=grid_df.groupby('id').filter(lambda g:len(g)==4 and (g.estado=='OK').all())
    ranking=eligible.groupby(['id','familia'],as_index=False).agg(MAE_CV=('MAE','mean'),
                     RMSE_CV=('RMSE',lambda x:float(np.sqrt(np.mean(np.asarray(x)**2)))),
                     MAE_CV_desvio_entre_anos=('MAE','std'))
    ranking=ranking.sort_values(['MAE_CV','id']).reset_index(drop=True)
    best_family=ranking.drop_duplicates('familia').copy()
    spec_map={s['id']:s for s in specs}
    best_family['parametros']=best_family.id.map(lambda i:json.dumps(spec_map[i]['parametros']))
    save_table('ranking_configuraciones_CV.csv',ranking);save_table('mejores_por_familia_CV.csv',best_family)
    selected_id=ranking.iloc[0]['id'];selected=spec_map[selected_id]
    learned=best_family.loc[~best_family.familia.str.startswith('Referencia')]
    best_learned_id=learned.iloc[0]['id']
    # Este archivo precede a la calibracion y evaluacion de prueba.
    frozen=dict(seleccion=selected,mejor_aprendido=spec_map[best_learned_id],
                criterio=PROTOCOL['criterio_seleccion'],huella_datos_protocolo=fingerprint,
                ranking=best_family.to_dict('records'),periodo_usado_hasta='2022-12',
                prueba_no_usada_para_elegir=True)
    save_json('seleccion_congelada_antes_prueba.json',frozen)
    calibration_actual=data.loc['2023-01-01':'2023-12-01','accidentes'].astype(float)
    calibration_fit=fit_model(dev,selected);calibration_pred=forecast(calibration_fit)
    calibration_errors=np.abs(calibration_actual.to_numpy()-calibration_pred.to_numpy())
    # Orden ceil((n+1)*0.9)=12: maximo de doce residuos. Cobertura no garantizada.
    order=min(len(calibration_errors),int(np.ceil((len(calibration_errors)+1)*.9)))
    width=float(np.sort(calibration_errors)[order-1])
    save_table('calibracion_2023.csv',pd.DataFrame(dict(fecha=calibration_actual.index,
               real=calibration_actual.to_numpy(),prediccion=calibration_pred.to_numpy(),error_absoluto=calibration_errors)))
    training=data.loc[:'2023-12-01','accidentes'].astype(float)
    scale=float(np.abs(training.to_numpy()[12:]-training.to_numpy()[:-12]).mean())
    fitted_models={};train_metrics=[]
    for _,row in best_family.iterrows():
        model=fit_model(training,spec_map[row.id]);fitted_models[row.id]=model
        ins=fitted_values(model);train_metrics.append(dict(id=row.id,familia=row.familia,
               escenario='Ajuste en muestra, un paso con historial real',n=len(ins),
               **metrics(training.loc[ins.index],ins,scale)))
    save_table('metricas_entrenamiento.csv',pd.DataFrame(train_metrics))
    # Un unico bloque de evaluacion 2024, con modelos y parametros congelados.
    actual_test=data.loc['2024-01-01':'2024-12-01','accidentes'].astype(float)
    predictions={};test_rows=[];prediction_rows=[]
    for _,row in best_family.iterrows():
        pred=forecast(fitted_models[row.id]);predictions[row.id]=pred
        test_rows.append(dict(id=row.id,familia=row.familia,**metrics(actual_test,pred,scale)))
        for horizon,(date,a,p) in enumerate(zip(actual_test.index,actual_test,pred),1):
            prediction_rows.append(dict(id=row.id,familia=row.familia,horizonte=horizon,
                                        fecha=str(date.date()),real=a,prediccion=p,error=p-a,error_absoluto=abs(p-a)))
    test_df=pd.DataFrame(test_rows);save_table('metricas_prueba_2024.csv',test_df)
    test_pred=pd.DataFrame(prediction_rows);save_table('predicciones_prueba_2024.csv',test_pred)
    chosen=test_df.loc[test_df.id==selected_id].iloc[0]
    selected_test=predictions[selected_id];error=selected_test.to_numpy()-actual_test.to_numpy()
    low=np.maximum(0,selected_test.to_numpy()-width);high=selected_test.to_numpy()+width
    coverage=float(np.mean((actual_test.to_numpy()>=low)&(actual_test.to_numpy()<=high)))
    save_table('bandas_empiricas_prueba_2024.csv',pd.DataFrame(dict(fecha=actual_test.index,
               real=actual_test.to_numpy(),prediccion=selected_test.to_numpy(),inferior=low,superior=high)))
    worst=test_pred.loc[test_pred.id==selected_id].nlargest(5,'error_absoluto')
    save_table('cinco_errores_mayores_2024.csv',worst)
    joined=best_family[['id','familia','MAE_CV','RMSE_CV','parametros']].merge(
        pd.DataFrame(train_metrics)[['id','MAE','RMSE']].rename(columns={'MAE':'MAE_train','RMSE':'RMSE_train'}),on='id',validate='one_to_one')
    joined=joined.merge(test_df[['id','MAE','RMSE','MAPE','R2','MASE']].rename(columns={'MAE':'MAE_test','RMSE':'RMSE_test'}),on='id',validate='one_to_one')
    joined['seleccionado_por_CV']=joined.id==selected_id;save_table('comparacion_train_CV_test.csv',joined)
    # Interpretacion de variables sin consultar prueba: perturbacion en los cuatro cortes CV.
    learned_spec=spec_map[best_learned_id]
    perturb_rows=[]
    if learned_spec['familia'] in ['Ridge','Random Forest','SVR']:
        rng=np.random.default_rng(SEED+3)
        for column in FEATURES:
            impacts=[]
            for year in PROTOCOL['anos_validacion']:
                model=fold_fits[(best_learned_id,year)];xx,_=supervised(model['history'])
                actual=dev.loc[f'{year}-01-01':f'{year}-12-01']
                baseline=mean_absolute_error(actual,forecast(model))
                for _ in range(5):
                    altered=forecast(model,perturb=(column,xx[column].to_numpy()),rng=rng)
                    impacts.append(mean_absolute_error(actual,altered)-baseline)
            perturb_rows.append(dict(variable=column,aumento_MAE_medio=np.mean(impacts),
                                      desvio=np.std(impacts),metodo='Perturbacion marginal de entradas en recursion; validacion, no prueba'))
    save_table('importancia_perturbacion_CV.csv',pd.DataFrame(perturb_rows))
    for _,row in best_family.iterrows():
        if row.familia=='Ridge':
            est=fitted_models[row.id]['estimator']
            save_table('coeficientes_Ridge.csv',pd.DataFrame(dict(variable=FEATURES,coeficiente_por_desvio_X=est[-1].coef_)))
        if row.familia=='Random Forest':
            save_table('importancia_RF.csv',pd.DataFrame(dict(variable=FEATURES,importancia_impureza=fitted_models[row.id]['estimator'].feature_importances_)))
    fig,ax=plt.subplots(figsize=(9,3.8));xx=np.arange(len(joined));widthbar=.24
    for shift,col,label,color in [(-1,'MAE_train','Entrenamiento (ajuste)','#9ca7af'),(0,'MAE_CV','Validacion 12 meses','#38698a'),(1,'MAE_test','Prueba 2024','#ba7730')]:
        ax.bar(xx+shift*widthbar,joined[col],widthbar,label=label,color=color)
    ax.set_xticks(xx,joined.familia,rotation=15,ha='right');ax.set(title='Aprendizaje aparente y capacidad de pronostico',ylabel='MAE (siniestros/mes)');ax.legend(fontsize=8)
    save_figure('f3_01_comparacion.png',fig)
    fig,ax=plt.subplots(figsize=(9,3.7));ax.plot(actual_test.index,actual_test,'o-',label='Real 2024',color='#233c4d')
    colors=['#ba7730','#3d8b66','#8b6ab1']
    show_ids=list(dict.fromkeys([selected_id,'M00',best_learned_id]))
    for i,model_id in enumerate(show_ids):
        ax.plot(actual_test.index,predictions[model_id],'--',label=spec_map[model_id]['familia'],color=colors[i])
    ax.set(title='Prueba: doce meses emitidos desde diciembre de 2023',ylabel='Siniestros por mes',xlabel='Mes de 2024');ax.legend(fontsize=8);ax.grid(alpha=.15)
    save_figure('f3_02_prueba.png',fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.5));axes[0].plot(actual_test.index,error,'o-',color='#38698a');axes[0].axhline(0,color='black',linewidth=.8)
    axes[0].set(title='Error del modelo seleccionado',xlabel='Mes 2024',ylabel='Predicho menos real')
    axes[1].scatter(selected_test,error,color='#38698a');axes[1].axhline(0,color='black',linewidth=.8);axes[1].set(title='Residuos frente a prediccion',xlabel='Siniestros predichos',ylabel='Predicho menos real')
    save_figure('f3_03_residuos.png',fig)
    fig,ax=plt.subplots(figsize=(9,3.5));cv_best=eligible.loc[eligible.id==selected_id]
    ax.plot(cv_best.ano_validacion,cv_best.MAE,'o-',label='MAE de pronostico a doce meses',color='#38698a')
    ax.plot(cv_best.ano_validacion,cv_best.MAE_entrenamiento,'o--',label='MAE de ajuste en entrenamiento',color='#ba7730')
    ax.set(title='Comportamiento retrospectivo del modelo elegido',xlabel='Ano pronosticado (cada origen agrega historial)',ylabel='MAE (siniestros/mes)');ax.legend(fontsize=8);save_figure('f3_04_cortes.png',fig)
    if perturb_rows:
        imp=pd.DataFrame(perturb_rows).sort_values('aumento_MAE_medio');fig,ax=plt.subplots(figsize=(8,4))
        ax.barh(imp.variable,imp.aumento_MAE_medio,color='#38698a');ax.axvline(0,color='black',linewidth=.8)
        ax.set(title=f'Perturbacion en validacion: {learned_spec["familia"]}',xlabel='Cambio en MAE (siniestros/mes)');save_figure('f3_05_importancia.png',fig)
    else:
        fig,ax=plt.subplots(figsize=(8,3.7));ax.bar(cv_best.ano_validacion.astype(str),cv_best.MAE,color='#38698a');ax.set(title='Errores por corte de la familia elegida',xlabel='Ano',ylabel='MAE');save_figure('f3_05_importancia.png',fig)
    # Despues de evaluar, se reajusta la misma especificacion con todo el historial.
    full=data.accidentes.astype(float);production=fit_model(full,selected);future=forecast(production)
    future_frame=pd.DataFrame(dict(fecha=future.index,prediccion=future.to_numpy(),
               banda_inferior=np.maximum(0,future.to_numpy()-width),banda_superior=future.to_numpy()+width,
               origen='2024-12-01',nota='Proyeccion retrospectiva de 2025; bandas empiricas sin cobertura garantizada'))
    save_table('pronostico_2025_corte_2024.csv',future_frame)
    artifact=dict(model=production,selected_spec=selected,origen='2024-12-01',features=FEATURES,
                  protocolo=PROTOCOL,version_python=platform.python_version(),band_width=width,
                  evaluacion_original=chosen.to_dict(),nota='Solo cargar artefactos de procedencia confiable.')
    (OUT/'models').mkdir(parents=True,exist_ok=True)
    joblib.dump(artifact,OUT/'models/modelo_pronostico.joblib')
    joblib.dump(dict(model=fitted_models[selected_id],selected_spec=selected,origen='2023-12-01',
                     band_width=width,features=FEATURES),OUT/'models/modelo_evaluado_2024.joblib')
    fig,ax=plt.subplots(figsize=(9,3.7));ax.plot(full.index[-24:],full.iloc[-24:],label='Observado 2023-2024',color='#233c4d')
    ax.plot(future.index,future,'--',label='Proyeccion de 2025 con corte 2024',color='#ba7730')
    ax.fill_between(future.index,future_frame.banda_inferior,future_frame.banda_superior,alpha=.18,color='#ba7730',label='Banda empirica aproximada')
    ax.set(title='Proyeccion posterior al ultimo dato verificado',xlabel='Mes',ylabel='Siniestros por mes');ax.legend(fontsize=8);save_figure('f3_06_proyeccion.png',fig)
    errors_by_horizon=test_pred.groupby('horizonte',as_index=False).agg(error_absoluto_medio=('error_absoluto','mean'))
    save_table('errores_por_horizonte_todas_familias.csv',errors_by_horizon)
    fig,ax=plt.subplots(figsize=(7,3.5));ax.bar(np.arange(1,13),np.abs(error),color='#38698a')
    ax.set(title='Error por horizonte: solo una realizacion anual de prueba',xlabel='Meses desde el origen',ylabel='Error absoluto (siniestros/mes)');save_figure('f3_07_horizonte.png',fig)
    lbtest=acorr_ljungbox(error,lags=[1,3],return_df=True)
    save_table('diagnostico_residuos_prueba.csv',lbtest.reset_index().rename(columns={'index':'lag'}))
    ref=test_df.loc[test_df.id=='M00'].iloc[0]
    meanref=test_df.loc[test_df.id=='M01'].iloc[0]
    summary=dict(fingerprint=fingerprint,seleccion=selected,mejor_aprendido=learned_spec,
                 configuraciones=len(specs),cortes=4,predicciones_CV_por_config=48,
                 distribucion=dict(desarrollo=84,calibracion=12,prueba=12),
                 ranking_CV=best_family.to_dict('records'),comparacion=joined.to_dict('records'),
                 metricas_prueba_seleccionado=chosen.to_dict(),
                 mejora_MAE_vs_estacional_pct=100*(ref.MAE-chosen.MAE)/ref.MAE,
                 mejora_MAE_vs_media12_pct=100*(meanref.MAE-chosen.MAE)/meanref.MAE,
                 calibracion=dict(ano=2023,n=12,radio_banda=width,orden_residuo=order,
                                  MAE=mean_absolute_error(calibration_actual,calibration_pred),
                                  cobertura_observada_2024=coverage,
                                  advertencia='Banda orientativa: errores temporalmente dependientes y no intercambiables garantizados.'),
                 proyeccion=dict(origen='2024-12',ano=2025,total=future.sum(),minimo=future.min(),maximo=future.max(),
                                 advertencia='No es un pronostico actualizado de 2027 ni esta validado con datos de 2025.'),
                 errores_mayores=worst.to_dict('records'),advertencias_ajustes=warnings_log,
                 limites=['Solo un ano de prueba y cuatro cortes para elegir hiperparametros.',
                          'El ajuste en entrenamiento utiliza historias reales a un paso; CV y prueba son doce pasos recursivos.',
                          'El mejor modelo por validacion no tiene por que ser el mejor en 2024. No se cambia tras observar prueba.',
                          'Las variables derivadas aportan representaciones de la historia, no nuevas observaciones independientes.'])
    save_json('fase3_resultados.json',summary)
    print('\nSELECCION FIJADA POR CV:',selected,flush=True)
    print(joined[['familia','MAE_train','MAE_CV','MAE_test','R2']].to_string(index=False),flush=True)
    print('Resultado seleccionado en prueba:',chosen.to_dict(),flush=True)
    return summary


if __name__=='__main__':main()
