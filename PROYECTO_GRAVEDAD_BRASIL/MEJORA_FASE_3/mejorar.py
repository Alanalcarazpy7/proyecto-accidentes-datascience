"""Ronda acotada reproducible. Conserva el experimento anterior sin modificarlo.

python MEJORA_FASE_3/mejorar.py
La prueba nueva se abre solo despues de guardar congelamiento.json.
"""
from pathlib import Path
from datetime import datetime,timezone
import sys
import gc
import hashlib
import json
import time
import zipfile
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import average_precision_score,roc_auc_score,f1_score,precision_score,recall_score
from lightgbm import LGBMClassifier

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE/'src'))
from common import RAW,load_data
from preparar import CAT,NUM,FEATURES,PERSON_FIELDS,EVENT_FIELDS,norm,number
from modelado import metrics,calibrate,thresholds

OUT=HERE/'output';DATA=HERE/'data';MODELS=HERE/'models'
for p in [OUT,DATA,MODELS,OUT/'figures']:p.mkdir(parents=True,exist_ok=True)
PROTOCOL=json.loads((HERE/'protocolo.json').read_text(encoding='utf8'))
EXTRA_NUM=['n_vehiculos_declarados','n_vehiculos_identificados','n_otros_vehiculos','otros_pesados','otras_motos','otros_ligeros']
ROAD=['CURVA','RETA','DECLIVE','ACLIVE','INTERSECAO','PONTE','VIADUTO','ROTATORIA','TUNEL','DESVIO']
ROAD_FIELDS=['via_'+x.lower() for x in ROAD]
LAYOUTS={'base':(CAT,NUM),'contexto':(CAT+['familia_otro_vehiculo'],NUM+EXTRA_NUM),
         'enriquecido':(CAT+['familia_otro_vehiculo','marca_prefijo'],NUM+EXTRA_NUM+ROAD_FIELDS)}
AUDIT_FILES=['models/modelo_seleccionado.joblib','protocolo.json','output/fase3_resultados.json','output/tables/metricas_prueba_2025.csv']


def writej(obj,path):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf8')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def log(s):print(s,flush=True)
def now():return datetime.now(timezone.utc).isoformat()
def table(d,name):d.to_csv(OUT/name,index=False,encoding='utf-8-sig')


def read(kind,year,columns=None):
    if year==2026:
        assert (OUT/'congelamiento.json').exists(),'Prohibido abrir prueba nueva antes de congelar'
        path=DATA/'raw_2026'/f'{kind}_{year}.zip'
        manifests=json.loads((HERE/'manifiesto_2026.json').read_text(encoding='utf8'))
    else:
        path=RAW/f'{kind}_{year}.zip'
        manifests=json.loads((BASE/'data/manifiesto_origenes.json').read_text(encoding='utf8'))
    expected=next(r['sha256'] for r in manifests if r['archivo']==path.name)
    assert digest(path)==expected,f'Hash de origen distinto: {path.name}'
    with zipfile.ZipFile(path) as z:
        with z.open(next(n for n in z.namelist() if n.lower().endswith('.csv'))) as f:
            d=pd.read_csv(f,sep=';',encoding='latin1',dtype=str,keep_default_na=False,usecols=columns)
    for c in ['id','pesid','id_veiculo']:
        if c in d:d[c]=d[c].str.strip().str.replace(r'\.0$','',regex=True)
    return d


def family(series):
    return pd.Series(np.select([
        series.isin(['CAMINHAO','CAMINHAO-TRATOR','ONIBUS','MICRO-ONIBUS']),
        series.isin(['MOTOCICLETA','MOTONETA','CICLOMOTOR']),
        series.isin(['AUTOMOVEL','CAMINHONETE','CAMIONETA','UTILITARIO']),
    ],['PESADO','MOTO','LIGERO'],default='OTRO'),index=series.index)


def add_context(base,p,o,year):
    assert o.id.is_unique
    v=p.loc[pd.to_numeric(p.id_veiculo,errors='coerce').gt(0),['id','id_veiculo','tipo_veiculo']].drop_duplicates(['id','id_veiculo']).copy()
    v['tipo']=v.tipo_veiculo.map({x:norm(x) for x in v.tipo_veiculo.unique()})
    v['familia']=family(v.tipo)
    v['es_pesado']=v.familia.eq('PESADO').astype('int16')
    v['es_moto']=v.familia.eq('MOTO').astype('int16')
    v['es_ligero']=v.familia.eq('LIGERO').astype('int16')
    counts=v.groupby('id').agg(n_vehiculos_identificados=('id_veiculo','size'),n_pesados=('es_pesado','sum'),n_motos=('es_moto','sum'),n_ligeros=('es_ligero','sum'))
    q=p.loc[p.estado_fisico.isin(['Lesões Leves','Lesões Graves','Óbito']),['id','pesid','id_veiculo','tipo_veiculo','marca']].copy()
    assert pd.to_numeric(q.pesid,errors='coerce').gt(0).all() and q.pesid.is_unique
    q=q.merge(o[['id','veiculos']],on='id',how='left',validate='many_to_one',indicator=True)
    assert q['_merge'].eq('both').all()
    q=q.drop(columns='_merge').join(counts,on='id')
    own_valid=pd.to_numeric(q.id_veiculo,errors='coerce').gt(0)
    own_type=q.tipo_veiculo.map({x:norm(x) for x in q.tipo_veiculo.unique()})
    own_family=family(own_type)
    q['n_vehiculos_declarados']=number(q.veiculos).where(number(q.veiculos).gt(0))
    q['n_vehiculos_identificados']=q.n_vehiculos_identificados.fillna(0)
    q['n_otros_vehiculos']=q.n_vehiculos_identificados-own_valid.astype(int)
    q['otros_pesados']=q.n_pesados.fillna(0)-(own_valid&own_family.eq('PESADO')).astype(int)
    q['otras_motos']=q.n_motos.fillna(0)-(own_valid&own_family.eq('MOTO')).astype(int)
    q['otros_ligeros']=q.n_ligeros.fillna(0)-(own_valid&own_family.eq('LIGERO')).astype(int)
    assert q[['n_otros_vehiculos','otros_pesados','otras_motos','otros_ligeros']].ge(0).all().all()
    q['familia_otro_vehiculo']=np.select([
        q.n_otros_vehiculos.eq(0),q.n_otros_vehiculos.gt(1),q.otros_pesados.eq(1),q.otras_motos.eq(1),q.otros_ligeros.eq(1)
    ],['NINGUNO_IDENTIFICADO','MULTIPLES','PESADO','MOTO','LIGERO'],default='OTRO')
    brand=q.marca.map({x:norm(x) for x in q.marca.unique()}).str.split('/').str[0].str.strip()
    q['marca_prefijo']=brand.where(~brand.isin(['NAO INFORMADO','DESCONOCIDO','','0']),'DESCONOCIDO')
    for c in ['id','pesid']:q[c]=pd.to_numeric(q[c],errors='raise').astype('int64')
    for c in EXTRA_NUM:q[c]=q[c].astype('float32')
    added=q[['id','pesid']+EXTRA_NUM+['familia_otro_vehiculo','marca_prefijo']]
    d=base.merge(added,on=['id','pesid'],how='left',validate='one_to_one',indicator=True)
    assert d['_merge'].eq('both').all() and len(d)==len(base)
    d.drop(columns='_merge',inplace=True)
    for word,c in zip(ROAD,ROAD_FIELDS):d[c]=d.tracado_via.astype(str).str.contains(word,regex=False).astype('int8')
    audit=dict(ano=year,victimas=len(d),accidentes=int(d.id.nunique()),fallecidos=int(d.fallecido.sum()),
               filas_fuente_personas=len(p),vehiculos_identificados_sin_duplicar=len(v),sin_union=0,
               duplicados_clave=int(d.duplicated(['id','pesid']).sum()),
               filas_numero_vehiculos_informado=int(d.n_vehiculos_declarados.notna().sum()),
               cantidad_max_vehiculos_declarados=float(d.n_vehiculos_declarados.max()))
    return d,audit


def prepare_development():
    target=DATA/'victimas_contexto_2017_2025.parquet'
    if target.exists():return pd.read_parquet(target)
    original=load_data()
    frames,audits=[],[]
    for year in range(2017,2026):
        p=read('pessoas',year,['id','pesid','id_veiculo','tipo_veiculo','marca','estado_fisico'])
        o=read('ocorrencias',year,['id','veiculos'])
        d,a=add_context(original[original.ano.eq(year)].copy(),p,o,year)
        frames.append(d);audits.append(a)
        log(f'Contexto {year}: {len(d):,} victimas, union sin expansion')
        del p,o,d;gc.collect()
    d=pd.concat(frames,ignore_index=True)
    for c in LAYOUTS['enriquecido'][0]:d[c]=d[c].astype('category')
    assert len(d)==754098 and d.pesid.is_unique
    d.sort_values(['fecha','id','pesid'],inplace=True,ignore_index=True)
    d.to_parquet(target,index=False,compression='zstd')
    table(pd.DataFrame(audits),'auditoria_nuevas_variables_2017_2025.csv')
    writej({k:{'categoricas':v[0],'numericas':v[1],'total':len(v[0])+len(v[1])} for k,v in LAYOUTS.items()},OUT/'diccionario_bloques.json')
    return d


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
    freeze=dict(protocolo_sha256=digest(HERE/'protocolo.json'),seleccionado=name,seleccion_solo_CV=True,modelos=[],prueba2026_leida=False)
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


def prepare_2026():
    # La barrera temporal tambien se comprueba dentro de read().
    p=read('pessoas',2026,list(dict.fromkeys(PERSON_FIELDS+['marca'])))
    o=read('ocorrencias',2026,EVENT_FIELDS+['veiculos'])
    assert o.id.is_unique
    q=p.loc[p.estado_fisico.isin(['Lesões Leves','Lesões Graves','Óbito']),PERSON_FIELDS].copy()
    assert pd.to_numeric(q.pesid,errors='coerce').gt(0).all() and q.pesid.is_unique
    q=q.merge(o[EVENT_FIELDS],on='id',how='left',validate='many_to_one',indicator=True)
    assert q['_merge'].eq('both').all();q.drop(columns='_merge',inplace=True)
    q['fallecido']=q.estado_fisico.eq('Óbito').astype('int8')
    q['fecha']=pd.to_datetime(q.data_inversa,format='%Y-%m-%d',errors='raise');q['ano']=q.fecha.dt.year.astype('int16')
    assert q.ano.eq(2026).all()
    age=number(q.idade);q['idade']=age.where(age.between(1,110)).astype('float32')
    vy=number(q.ano_fabricacao_veiculo);q['idade_veiculo']=(2026-vy).where(vy.between(1900,2026)).astype('float32')
    h=pd.to_timedelta(q.horario,errors='coerce').dt.total_seconds()/3600;h=h.where(h.between(0,24,inclusive='left'))
    q['hora']=h.astype('float32');q['hora_sin']=np.sin(2*np.pi*h/24).astype('float32');q['hora_cos']=np.cos(2*np.pi*h/24).astype('float32')
    q['mes_sin']=np.sin(2*np.pi*(q.fecha.dt.month-1)/12).astype('float32');q['mes_cos']=np.cos(2*np.pi*(q.fecha.dt.month-1)/12).astype('float32')
    q['dia_semana']=q.fecha.dt.dayofweek.astype(str)
    for c,lo,hi in [('latitude',-34,6),('longitude',-74,-34),('km',0,10000)]:
        v=number(q[c]);q[c]=v.where(v.between(lo,hi)).astype('float32')
    for c in CAT:q[c]=q[c].map({x:norm(x) for x in q[c].unique()})
    q.loc[q.br.isin(['0','0.0']),'br']='DESCONOCIDO'
    for c in ['id','pesid','id_veiculo']:q[c]=pd.to_numeric(q[c],errors='raise').astype('int64')
    base=q[['id','pesid','id_veiculo','fecha','ano','fallecido']+FEATURES]
    result,audit=add_context(base,p,o,2026)
    for c in LAYOUTS['enriquecido'][0]:result[c]=result[c].astype('category')
    result.sort_values(['fecha','id','pesid'],inplace=True,ignore_index=True)
    dates=pd.to_datetime(o.data_inversa,format='%Y-%m-%d',errors='raise')
    audit.update(fecha_min_archivo=str(dates.min().date()),fecha_max_archivo=str(dates.max().date()),
        fecha_min_victimas=str(result.fecha.min().date()),fecha_max_victimas=str(result.fecha.max().date()),
        dias_con_accidentes=int(dates.nunique()),filas_ocurrencias=len(o),filas_personas=len(p),
        estados_fisicos={str(k):int(v) for k,v in p.estado_fisico.value_counts().items()},
        fecha_lectura_nueva_prueba_UTC=now(),nota='Periodo publicado; no se presume anio completo ni seguimiento hospitalario a 30 dias')
    writej(audit,OUT/'auditoria_2026.json')
    result.to_parquet(DATA/'prueba_2026_preparada.parquet',index=False,compression='zstd')
    return result,audit


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
    assert freeze['protocolo_sha256']==digest(HERE/'protocolo.json')
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
        nota='2025 es comparacion retrospectiva; 2026 se abrio despues de congelar sin ajustes posteriores. Periodo incompleto publicado.')
    writej(result,target)
    return result


def main():
    snapshot=OUT/'integridad_experimento_original_antes.json'
    if not snapshot.exists():writej({name:digest(BASE/name) for name in AUDIT_FILES},snapshot)
    d=prepare_development();freeze=select_and_freeze(d);evaluate_once(d,freeze)
    old=json.loads(snapshot.read_text(encoding='utf8'))
    assert all(digest(BASE/name)==h for name,h in old.items())
    writej({'estado':'OK','archivos_originales_sin_cambios':old,'seleccion':freeze['seleccionado'],'presupuesto_respetado':len(pd.read_csv(OUT/'validacion_temporal.csv'))==24},OUT/'verificacion.json')
    log('Ronda finalizada. Proyecto original intacto; ninguna decision cambiada despues de la prueba nueva.')


if __name__=='__main__':main()
