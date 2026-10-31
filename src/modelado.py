"""Seleccion final y reproduccion del experimento registrado.
Con los resultados guardados no vuelve a ajustar ni a elegir con 2026.
Una reproduccion completa es retrospectiva: no crea una prueba ciega nueva.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,time,gc,hashlib,shutil
import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import average_precision_score,roc_auc_score,f1_score,precision_score,recall_score
from lightgbm import LGBMClassifier
from common import ROOT,OUT as OUTPUT,DATA,load_data,save_json
from preparar import BASE_CAT as CAT,BASE_NUM as NUM,BASE_FEATURES as FEATURES,EXTRA_NUM,ROAD_FIELDS,prepare
from comparacion import metrics,calibrate,thresholds
HERE=ROOT;BASE=ROOT;OUT=OUTPUT/'modelado/final';MODELS=ROOT/'tmp/modelos_ajuste'
OUT.mkdir(parents=True,exist_ok=True)
PROTOCOL=json.loads((ROOT/'data/metodologia/protocolo_final.json').read_text(encoding='utf8'))
LAYOUTS={'base':(CAT,NUM),'contexto':(CAT+['familia_otro_vehiculo'],NUM+EXTRA_NUM),'enriquecido':(CAT+['familia_otro_vehiculo','marca_prefijo'],NUM+EXTRA_NUM+ROAD_FIELDS)}
def writej(o,p):save_json(o,p)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def log(s):print(s,flush=True)
def table(d,n):d.to_csv(OUT/n,index=False,encoding='utf-8-sig')
def prepare_development():return prepare(variantes=True)
def prepare_2026():
    d=load_data();test=d[d.ano.eq(2026)].copy()
    return test,json.loads((OUT/'auditoria_2026.json').read_text(encoding='utf8'))
def specs():
    common=dict(hojas=15,arboles=240,tasa=.06,min_hoja=120,l2=8,peso='raiz')
    return [
        dict(nombre='Referencia_24_original',bloque='base',**common),
        dict(nombre='Contexto_mismo_ajuste',bloque='contexto',**common),
        dict(nombre='Enriquecido_mismo_ajuste',bloque='enriquecido',**common),
        dict(nombre='Contexto_regularizado',bloque='contexto',hojas=15,arboles=400,tasa=.04,min_hoja=300,l2=25,peso='raiz'),
        dict(nombre='Contexto_regularizado_natural',bloque='contexto',hojas=15,arboles=400,tasa=.04,min_hoja=300,l2=25,peso='natural'),
        dict(nombre='Enriquecido_regularizado',bloque='enriquecido',hojas=15,arboles=400,tasa=.04,min_hoja=300,l2=25,peso='raiz'),
        dict(nombre='Enriquecido_31_hojas',bloque='enriquecido',hojas=31,arboles=400,tasa=.04,min_hoja=300,l2=25,peso='raiz'),
        dict(nombre='Enriquecido_7_hojas',bloque='enriquecido',hojas=7,arboles=450,tasa=.05,min_hoja=500,l2=40,peso='raiz'),
    ]

def make_model(s,y):
    cats,nums=LAYOUTS[s['bloque']]
    pre=ColumnTransformer([('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1,dtype=np.float32),cats),('num','passthrough',nums)])
    ratio=float((y==0).sum()/(y==1).sum())
    clf=LGBMClassifier(n_estimators=s['arboles'],learning_rate=s['tasa'],num_leaves=s['hojas'],
        min_child_samples=s['min_hoja'],reg_lambda=s['l2'],colsample_bytree=.9,
        scale_pos_weight=np.sqrt(ratio) if s['peso']=='raiz' else 1,
        random_state=42,n_jobs=4,verbosity=-1,deterministic=True,force_col_wise=True)
    return Pipeline([('prep',pre),('modelo',clf)])

def features(s):return list(LAYOUTS[s['bloque']][0])+list(LAYOUTS[s['bloque']][1])

def fit(model,s,X,y):
    cats=LAYOUTS[s['bloque']][0]
    model.fit(X[features(s)],y,modelo__categorical_feature=list(range(len(cats))))
    assert model['modelo'].booster_.params.get('categorical_column')==list(range(len(cats)))

def predict(bundle,d,calibrated=True):
    from scipy.special import logit
    p=bundle['pipeline'].predict_proba(d[bundle['features']])[:,1]
    if calibrated and bundle.get('calibrador') is not None:
        p=bundle['calibrador'].predict_proba(logit(np.clip(p,1e-7,1-1e-7)).reshape(-1,1))[:,1]
    return np.asarray(p,dtype=np.float64)

def select_and_freeze(d):
    target=OUT/'congelamiento.json'
    if target.exists():return json.loads(target.read_text(encoding='utf8'))
    grid=specs();writej(grid,OUT/'grilla_fijada.json')
    rows=[]
    cache=OUT/'cv_checkpoint.json'
    if cache.exists():rows=json.loads(cache.read_text(encoding='utf8'))
    done={(x['modelo'],x['validar']) for x in rows}
    for s in grid:
        for cut in PROTOCOL['CV']:
            if (s['nombre'],cut['validar']) in done:continue
            tr=d[d.ano.le(cut['train_hasta'])];va=d[d.ano.eq(cut['validar'])]
            start=time.perf_counter();model=make_model(s,tr.fallecido)
            fit(model,s,tr,tr.fallecido)
            p=model.predict_proba(va[features(s)])[:,1]
            row=dict(modelo=s['nombre'],bloque=s['bloque'],train_hasta=cut['train_hasta'],validar=cut['validar'],
                     n_train=len(tr),n_validacion=len(va),AP=float(average_precision_score(va.fallecido,p)),
                     ROC_AUC=float(roc_auc_score(va.fallecido,p)),segundos=time.perf_counter()-start)
            rows.append(row);writej(rows,cache);table(pd.DataFrame(rows),'validacion_temporal.csv')
            log(f"CV {s['nombre']} {cut['validar']}: AP {row['AP']:.4f}, AUC {row['ROC_AUC']:.4f}, {row['segundos']:.1f}s")
            del tr,va,model,p;gc.collect()
    cv=pd.DataFrame(rows)
    ref=cv[cv.modelo.eq('Referencia_24_original')].set_index('validar')
    rank=cv.groupby(['modelo','bloque'],sort=False).agg(AP_media=('AP','mean'),AP_sd=('AP','std'),AUC_media=('ROC_AUC','mean')).reset_index()
    rank['cortes_supera_referencia']=[int((cv[cv.modelo.eq(n)].set_index('validar').AP-ref.AP).gt(0).sum()) for n in rank.modelo]
    ref_mean=float(rank.loc[rank.modelo.eq('Referencia_24_original'),'AP_media'].iloc[0])
    rank['ganancia_AP_media']=rank.AP_media-ref_mean
    rank['elegible']=rank.ganancia_AP_media.gt(0)&rank.cortes_supera_referencia.ge(2)
    rank.sort_values('AP_media',ascending=False,kind='stable',inplace=True)
    table(rank,'ranking_CV.csv')
    name=rank.loc[rank.elegible,'modelo'].iloc[0] if rank.elegible.any() else 'Referencia_24_original'
    selected=next(s for s in grid if s['nombre']==name)
    tr=d[d.ano.le(2023)];cal=d[d.ano.eq(2024)&d.fecha.lt('2024-07-01')];val=d[d.ano.eq(2024)&d.fecha.ge('2024-07-01')]
    freeze=dict(protocolo_sha256=digest(ROOT/'data/metodologia/protocolo_final.json'),seleccionado=name,seleccion_solo_CV=True,modelos=[],prueba2026_ya_conocida=True,reproduccion_retrospectiva=True)
    train_scores=[]
    for s in [grid[0],selected] if name!=grid[0]['nombre'] else [grid[0]]:
        model=make_model(s,tr.fallecido);fit(model,s,tr,tr.fallecido)
        bundle=dict(pipeline=model,features=features(s),spec=s,calibrador=None)
        bundle['calibrador']=calibrate(predict(bundle,cal,False),cal.fallecido)
        p=predict(bundle,val);bundle['umbrales']=thresholds(val.fallecido,p);bundle['umbral']=bundle['umbrales']['F1_fallecido']
        artifact=MODELS/(s['nombre']+'.joblib');joblib.dump(bundle,artifact,compress=3)
        freeze['modelos'].append(dict(nombre=s['nombre'],spec=s,features=bundle['features'],umbral=bundle['umbral'],umbrales=bundle['umbrales'],archivo=str(artifact.relative_to(HERE)),sha256=digest(artifact)))
        for label,frame in [('entrenamiento_2017_2023',tr),('validacion_umbral_2024_H2',val)]:
            train_scores.append(dict(modelo=s['nombre'],particion=label,regla='F1_validacion',**metrics(frame.fallecido.to_numpy(),predict(bundle,frame),bundle['umbral'])))
        log(f"Congelado {s['nombre']}: {len(bundle['features'])} predictores, umbral {bundle['umbral']:.4f}")
        del model,bundle;gc.collect()
    table(pd.DataFrame(train_scores),'metricas_train_validacion.csv')
    freeze['fecha_congelamiento_UTC']=now();writej(freeze,target)
    log('Selección y umbrales fijados antes de leer la nueva prueba de 2026.')
    return freeze

def bootstrap(test,p_ref,p_new,t_ref,t_new):
    codes,ids=pd.factorize(test.id);n=len(ids);rng=np.random.default_rng(42);y=test.fallecido.to_numpy()
    rows=[]
    for b in range(300):
        wg=np.bincount(rng.integers(0,n,size=n),minlength=n);w=wg[codes]
        row={'replica':b}
        for name,fn in [('AP',average_precision_score),('ROC_AUC',roc_auc_score)]:row['delta_'+name]=float(fn(y,p_new,sample_weight=w)-fn(y,p_ref,sample_weight=w))
        for name,fn,kwargs in [('F1_macro',f1_score,{'average':'macro'}),('precision',precision_score,{'zero_division':0}),('recall',recall_score,{})]:
            row['delta_'+name]=float(fn(y,p_new>=t_new,sample_weight=w,**kwargs)-fn(y,p_ref>=t_ref,sample_weight=w,**kwargs))
        rows.append(row)
    frame=pd.DataFrame(rows);table(frame,'bootstrap_pareado_2026.csv')
    ci=pd.DataFrame([dict(metrica=c,IC95_bajo=float(frame[c].quantile(.025)),IC95_alto=float(frame[c].quantile(.975))) for c in frame if c!='replica'])
    table(ci,'intervalos_mejora_2026.csv')
    return ci.to_dict('records')

def evaluate_once(d,freeze):
    target=OUT/'resultados.json'
    if target.exists():return json.loads(target.read_text(encoding='utf8'))
    assert freeze['protocolo_sha256']==digest(ROOT/'data/metodologia/protocolo_final.json')
    test,audit=prepare_2026()
    assert set(test.id).isdisjoint(set(d.id)) and set(test.pesid).isdisjoint(set(d.pesid))
    rows=[];preds=test[['id','pesid','fecha','fallecido']].copy();new_probs={}
    for item in freeze['modelos']:
        assert digest(HERE/item['archivo'])==item['sha256']
        b=joblib.load(HERE/item['archivo'])
        for label,frame in [('2025_retroactivo_ya_conocido',d[d.ano.eq(2025)]),('2026_prueba_nueva',test)]:
            p=predict(b,frame)
            for rule,t in [('F1_validacion',item['umbral']),('umbral_05',.5),('recall80_validacion',item['umbrales']['recall80'])]:
                rows.append(dict(modelo=item['nombre'],particion=label,regla=rule,**metrics(frame.fallecido.to_numpy(),p,t)))
            if label=='2026_prueba_nueva':preds[item['nombre']]=p;new_probs[item['nombre']]=p
            r=rows[-3];log(f"{label} {item['nombre']}: AP {r['AP']:.4f}, AUC {r['ROC_AUC']:.4f}, F1macro {r['F1_macro']:.4f}, precision {r['precision']:.3f}, recall {r['recall']:.3f}")
    table(pd.DataFrame(rows),'metricas_evaluacion.csv')
    train=pd.read_csv(OUT/'metricas_train_validacion.csv')
    table(pd.concat([train,pd.DataFrame(rows)],ignore_index=True),'comparacion_completa.csv')
    predpath=OUT/'predicciones_2026.csv.gz';preds.to_csv(predpath,index=False,compression='gzip')
    ref=freeze['modelos'][0];sel=next(x for x in freeze['modelos'] if x['nombre']==freeze['seleccionado'])
    intervals=bootstrap(test,new_probs[ref['nombre']],new_probs[sel['nombre']],ref['umbral'],sel['umbral'])
    result=dict(seleccionado=freeze['seleccionado'],referencia=ref['nombre'],auditoria_prueba=audit,
        metricas=rows,intervalos_delta=intervals,protocolo_sha256=freeze['protocolo_sha256'],
        predicciones_sha256=digest(predpath),alcance=PROTOCOL['alcance'],
        nota='Reproduccion retrospectiva del experimento registrado; su congelamiento original precedio la primera lectura de 2026. No es una nueva prueba ciega.')
    writej(result,target)
    return result

def main(reentrenar=False):
    model_path=OUTPUT/'modelo/modelo_final.joblib'
    if (OUT/'resultados.json').exists() and model_path.exists() and not reentrenar:
        log('Resultados finales registrados: se reutilizan sin una nueva seleccion.')
        return json.loads((OUT/'resultados.json').read_text(encoding='utf8'))
    MODELS.mkdir(parents=True,exist_ok=True)
    if reentrenar:
        for name in ['cv_checkpoint.json','congelamiento.json','resultados.json']:
            (OUT/name).unlink(missing_ok=True)
    d=prepare_development();frozen=select_and_freeze(d);result=evaluate_once(d,frozen)
    selected=next(x for x in frozen['modelos'] if x['nombre']==frozen['seleccionado'])
    shutil.copy2(HERE/selected['archivo'],model_path)
    return result

if __name__=='__main__':main()
