"""Preparacion reproducible de victimas y contexto vehicular desde fuentes PRF.
El corte 2026 ya fue evaluado en el experimento registrado; reconstruirlo no es
una prueba ciega nueva. No se editan datos manualmente ni se imputa el objetivo.
"""
import json,zipfile,hashlib,unicodedata
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from common import ROOT,RAW,DATA,OUT,save_json,table,log
PERSON_FIELDS = ['id', 'pesid', 'id_veiculo', 'estado_fisico', 'idade', 'sexo', 'tipo_envolvido', 'tipo_veiculo', 'ano_fabricacao_veiculo']
EVENT_FIELDS = ['id', 'data_inversa', 'horario', 'uf', 'br', 'km', 'municipio', 'tipo_acidente', 'fase_dia', 'sentido_via', 'condicao_metereologica', 'tipo_pista', 'tracado_via', 'uso_solo', 'latitude', 'longitude']
CAT = ['sexo', 'tipo_envolvido', 'tipo_veiculo', 'uf', 'br', 'municipio', 'tipo_acidente', 'fase_dia', 'sentido_via', 'condicao_metereologica', 'tipo_pista', 'tracado_via', 'uso_solo', 'dia_semana']
NUM = ['idade', 'idade_veiculo', 'hora', 'hora_sin', 'hora_cos', 'mes_sin', 'mes_cos', 'latitude', 'longitude', 'km']
FEATURES = NUM + CAT
UNKNOWN = {'', 'NA', 'NAN', 'NULL', 'NAO INFORMADO', 'IGNORADO', 'INVALIDO'}
BASE_CAT=CAT.copy()
BASE_NUM=NUM.copy()
BASE_FEATURES=FEATURES.copy()
EXTRA_NUM=['n_vehiculos_declarados','n_vehiculos_identificados','n_otros_vehiculos','otros_pesados','otras_motos','otros_ligeros']
ROAD=['CURVA','RETA','DECLIVE','ACLIVE','INTERSECAO','PONTE','VIADUTO','ROTATORIA','TUNEL','DESVIO']
ROAD_FIELDS=['via_'+x.lower() for x in ROAD]
CAT=BASE_CAT+["familia_otro_vehiculo"]
NUM=BASE_NUM+EXTRA_NUM
FEATURES=NUM+CAT

def norm(value):
    s = ' '.join(str(value).strip().upper().split())
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    return 'DESCONOCIDO' if s in UNKNOWN else s

def number(s):
    return pd.to_numeric(s.astype(str).str.replace(',', '.', regex=False), errors='coerce')

def now():return datetime.now(timezone.utc).isoformat()
def read(kind,year,columns=None):
    path=RAW/f'{kind}_{year}.zip'
    manifest=json.loads((ROOT/'data/fuentes.json').read_text(encoding='utf8'))
    expected=next(r['sha256'] for r in manifest if r['archivo']==path.name)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,f'Hash distinto: {path.name}'
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

def clean_year(year):
    # La barrera temporal tambien se comprueba dentro de read().
    p=read('pessoas',year,list(dict.fromkeys(PERSON_FIELDS+['marca'])))
    o=read('ocorrencias',year,EVENT_FIELDS+['veiculos'])
    assert o.id.is_unique
    q=p.loc[p.estado_fisico.isin(['Lesões Leves','Lesões Graves','Óbito']),PERSON_FIELDS].copy()
    assert pd.to_numeric(q.pesid,errors='coerce').gt(0).all() and q.pesid.is_unique
    q=q.merge(o[EVENT_FIELDS],on='id',how='left',validate='many_to_one',indicator=True)
    assert q['_merge'].eq('both').all();q.drop(columns='_merge',inplace=True)
    q['fallecido']=q.estado_fisico.eq('Óbito').astype('int8')
    q['fecha']=pd.to_datetime(q.data_inversa,format='%Y-%m-%d',errors='raise');q['ano']=q.fecha.dt.year.astype('int16')
    assert q.ano.eq(year).all()
    age=number(q.idade);q['idade']=age.where(age.between(1,110)).astype('float32')
    vy=number(q.ano_fabricacao_veiculo);q['idade_veiculo']=(year-vy).where(vy.between(1900,year)).astype('float32')
    h=pd.to_timedelta(q.horario,errors='coerce').dt.total_seconds()/3600;h=h.where(h.between(0,24,inclusive='left'))
    q['hora']=h.astype('float32');q['hora_sin']=np.sin(2*np.pi*h/24).astype('float32');q['hora_cos']=np.cos(2*np.pi*h/24).astype('float32')
    q['mes_sin']=np.sin(2*np.pi*(q.fecha.dt.month-1)/12).astype('float32');q['mes_cos']=np.cos(2*np.pi*(q.fecha.dt.month-1)/12).astype('float32')
    q['dia_semana']=q.fecha.dt.dayofweek.astype(str)
    for c,lo,hi in [('latitude',-34,6),('longitude',-74,-34),('km',0,10000)]:
        v=number(q[c]);q[c]=v.where(v.between(lo,hi)).astype('float32')
    for c in BASE_CAT:q[c]=q[c].map({x:norm(x) for x in q[c].unique()})
    q.loc[q.br.isin(['0','0.0']),'br']='DESCONOCIDO'
    for c in ['id','pesid','id_veiculo']:q[c]=pd.to_numeric(q[c],errors='raise').astype('int64')
    base=q[['id','pesid','id_veiculo','fecha','ano','fallecido']+BASE_FEATURES]
    result,audit=add_context(base,p,o,year)
    result.sort_values(['fecha','id','pesid'],inplace=True,ignore_index=True)
    dates=pd.to_datetime(o.data_inversa,format='%Y-%m-%d',errors='raise')
    audit.update(fecha_min_archivo=str(dates.min().date()),fecha_max_archivo=str(dates.max().date()),
        fecha_min_victimas=str(result.fecha.min().date()),fecha_max_victimas=str(result.fecha.max().date()),
        dias_con_accidentes=int(dates.nunique()),filas_ocurrencias=len(o),filas_personas=len(p),
        estados_fisicos={str(k):int(v) for k,v in p.estado_fisico.value_counts().items()},
        fecha_preparacion_UTC=now(),nota='Periodo publicado; no se presume anio completo ni seguimiento hospitalario a 30 dias')
    return result,audit

DESCRIPTIONS = {
    'id': 'Identificador real del accidente; clave de union, nunca predictor', 'pesid': 'Identificador positivo de participacion; no identidad civil longitudinal',
    'id_veiculo': 'Identificador del vehiculo, cero desconocido/no aplicable; nunca predictor', 'fecha': 'Fecha del siniestro; permite particion cronologica',
    'ano': 'Anio de siniestro; particion y auditoria', 'fallecido': 'Objetivo binario; 1 obito, 0 lesiones leves/graves',
    'idade': 'Edad en anios; 0 ambiguo, negativos y >110 a faltante', 'idade_veiculo': 'Antiguedad del vehiculo en anios al siniestro',
    'hora': 'Hora del dia decimal 0..24', 'hora_sin': 'Seno del ciclo horario, sin unidad', 'hora_cos': 'Coseno del ciclo horario, sin unidad',
    'mes_sin': 'Seno del ciclo mensual, sin unidad', 'mes_cos': 'Coseno del ciclo mensual, sin unidad', 'latitude': 'Latitud decimal en grados',
    'longitude': 'Longitud decimal en grados', 'km': 'Kilometro de carretera BR', 'sexo': 'Sexo registrado', 'tipo_envolvido': 'Rol de participacion: conductor, pasajero, peaton, etc.',
    'tipo_veiculo': 'Tipo de vehiculo asociado', 'uf': 'Unidad federativa del siniestro', 'br': 'Identificador de carretera federal, categoria',
    'municipio': 'Municipio del siniestro', 'tipo_acidente': 'Tipo principal del evento, conocido al observar el siniestro', 'fase_dia': 'Fase del dia registrada',
    'sentido_via': 'Sentido de circulacion', 'condicao_metereologica': 'Condicion meteorologica observada', 'tipo_pista': 'Tipo de calzada',
    'tracado_via': 'Trazado, a veces compuesto por varios elementos separados por punto y coma', 'uso_solo': 'SIM urbano; NAO rural', 'dia_semana': 'Dia de semana calculado: 0 lunes, 6 domingo',
}

DESCRIPTIONS.update({
    'n_vehiculos_declarados':'Cantidad de vehiculos declarada por accidente; no cantidad de victimas',
    'n_vehiculos_identificados':'Vehiculos con ID positivo distintos en la exportacion completa',
    'n_otros_vehiculos':'Vehiculos identificados descontando el propio cuando existe',
    'otros_pesados':'Otros camiones, camiones-tractor, omnibus o micro-omnibus identificados',
    'otras_motos':'Otras motocicletas, motonetas o ciclomotores identificados',
    'otros_ligeros':'Otros automoviles, camionetas o utilitarios identificados',
    'familia_otro_vehiculo':'Familia del unico otro vehiculo identificado; ninguno o multiples en los demas casos',
})


def prepare(force=False,variantes=False):
    target=DATA/'victimas_limpias.parquet'
    if target.exists() and not force and not variantes:return pd.read_parquet(target)
    frames,audits=[],[]
    for year in range(2017,2026 if variantes else 2027):
        d,a=clean_year(year);frames.append(d);audits.append(a)
        log(f'Preparacion {year}: {len(d):,} victimas con union validada')
    d=pd.concat(frames,ignore_index=True)
    cats=CAT+(['marca_prefijo'] if variantes else [])
    for c in cats:d[c]=d[c].astype('category')
    d.sort_values(['fecha','id','pesid'],inplace=True,ignore_index=True)
    assert d.pesid.is_unique and not d.duplicated(['id','pesid']).any()
    if variantes:return d
    d=d[['id','pesid','id_veiculo','fecha','ano','fallecido']+FEATURES]
    assert len(d)==821689 and int(d.fallecido.sum())==55435
    d.to_parquet(target,index=False,compression='zstd')
    table(pd.DataFrame(audits),'auditoria_preparacion_por_anio.csv')
    split=np.select([d.ano.le(2023),d.fecha.lt('2024-07-01'),d.ano.eq(2024),d.ano.eq(2025)],
        ['desarrollo_2017_2023','calibracion_2024_H1','umbral_2024_H2','comparacion_retrospectiva_2025'],default='prueba_posterior_2026_ene_sep')
    part=d.assign(particion=split).groupby('particion').agg(filas=('pesid','size'),accidentes=('id','nunique'),fallecidos=('fallecido','sum'))
    part['heridos']=part.filas-part.fallecidos;part['proporcion_fallecidos']=part.fallecidos/part.filas
    table(part.reset_index(),'particiones.csv')
    dic=[]
    for c in d:
        x=d[c];missing=x.isna()
        if c in CAT:missing=missing|x.astype(str).eq('DESCONOCIDO')
        if c=='id_veiculo':missing=missing|x.eq(0)
        observed=x.dropna()
        example=(str(observed.min())+' .. '+str(observed.max())) if pd.api.types.is_numeric_dtype(x) or pd.api.types.is_datetime64_any_dtype(x) else '; '.join(x.value_counts().head(8).index.astype(str))
        dic.append(dict(variable=c,descripcion=DESCRIPTIONS[c],tipo=str(x.dtype),valores_distintos=int(x.nunique()),faltantes=int(missing.sum()),porcentaje_faltante=float(missing.mean()*100),rango_o_categorias_observadas=example,predictor=c in FEATURES))
    table(pd.DataFrame(dic),'diccionario_final.csv')
    bit=[]
    for a in audits:
        year=a['ano'];g=d[d.ano.eq(year)]
        bit += [dict(ano=year,decision='Excluir ilesos y estado desconocido del objetivo binario',filas=a['filas_personas']-len(g),fundamento='Comparacion entre heridas y fallecidas, sin inventar personas'),
                dict(ano=year,decision='Edad cero ambigua, negativa o mayor a 110 a faltante',filas=int(g.idade.isna().sum()),fundamento='Conservar victima; no imputar una edad de lactante'),
                dict(ano=year,decision='Anio de vehiculo no plausible a faltante',filas=int(g.idade_veiculo.isna().sum()),fundamento='No interpretar cero como antiguedad real'),
                dict(ano=year,decision='Union por accidente y participacion',filas=len(g),fundamento='Uno a uno para contexto; cero expansion y cero faltantes de union'),
                dict(ano=year,decision='Contexto a partir de todos los vehiculos, deduplicados por clave positiva',filas=len(g),fundamento='Incluye ilesos y vehiculos sin persona; no usa la gravedad para contar otros vehiculos')]
    table(pd.DataFrame(bit),'bitacora_limpieza.csv')
    save_json(dict(filas=len(d),base_principal_2017_2025=int(d.ano.le(2025).sum()),prueba_2026=int(d.ano.eq(2026).sum()),fallecidos=int(d.fallecido.sum()),heridos=int(d.fallecido.eq(0).sum()),predictores=FEATURES,union='id y (id,pesid) reales; sin expansion',imputacion='Solo en cada entrenamiento; el objetivo no se imputa',manifiesto='data/fuentes.json'),OUT/'auditoria_preparacion.json')
    return d


def original_dictionary():
    """Diccionario de ambas tablas, rangos y ausencias de los CSV originales."""
    extra={'data_inversa':'Fecha del siniestro ISO','horario':'Hora del siniestro HH:MM:SS','estado_fisico':'Desenlace registrado de la participacion; incluye desconocidos',
        'causa_acidente':'Atribucion principal de causa; excluida como predictor','classificacao_acidente':'Gravedad agregada del accidente; prohibida como predictor',
        'pessoas':'Total de involucrados declarado por accidente','mortos':'Cantidad de fallecidos en ocurrencias; indicador binario en personas',
        'feridos_leves':'Heridos leves: cantidad en ocurrencias, indicador en personas','feridos_graves':'Heridos graves: cantidad en ocurrencias, indicador en personas',
        'ilesos':'Ilesos: cantidad en ocurrencias, indicador en personas','ignorados':'Involucrados de estado desconocido','feridos':'Total de heridos declarado',
        'veiculos':'Cantidad de vehiculos declarada','marca':'Marca/modelo textual del vehiculo; no queda en el modelo elegido',
        'ano_fabricacao_veiculo':'Anio de fabricacion, cero no informado','regional':'Regional de PRF','delegacia':'Delegacion de PRF','uop':'Unidad operacional de PRF'}
    numeric={'id','pesid','id_veiculo','idade','ano_fabricacao_veiculo','pessoas','mortos','feridos_leves','feridos_graves','ilesos','ignorados','feridos','veiculos','km','latitude','longitude','br'}
    rows=[]
    for kind in ['ocorrencias','pessoas']:
        agg={}
        for year in range(2017,2027):
            raw=read(kind,year)
            for c in raw:
                x=raw[c].str.strip();a=agg.setdefault(c,dict(n=0,missing=0,cardinality=0,min=None,max=None,examples=set()))
                missing=x.str.upper().isin(['','NA','NAN','NULL','NÃO INFORMADO','NAO INFORMADO','IGNORADO','INVÁLIDO','INVALIDO'])
                if c in ['pesid','id_veiculo','idade','ano_fabricacao_veiculo']:missing=missing|number(x).eq(0)
                a['n']+=len(x);a['missing']+=int(missing.sum());a['cardinality']=max(a['cardinality'],int(x.nunique()))
                if c in numeric:
                    values=number(x).dropna()
                    if len(values):
                        lo=float(values.min());hi=float(values.max())
                        a['min']=lo if a['min'] is None else min(a['min'],lo);a['max']=hi if a['max'] is None else max(a['max'],hi)
                elif len(a['examples'])<12:a['examples'].update(x.drop_duplicates().head(12).tolist())
        for c,a in agg.items():
            values=f"{a['min']} .. {a['max']}" if c in numeric else '; '.join(sorted(a['examples'])[:12])
            rows.append(dict(tabla=kind,variable=c,descripcion=extra.get(c,DESCRIPTIONS.get(c,c)),tipo_esperado='numerico' if c in numeric else 'fecha ISO' if c=='data_inversa' else 'hora' if c=='horario' else 'categoria',n=a['n'],faltantes_o_codigos_ambiguos=a['missing'],porcentaje_faltante=100*a['missing']/a['n'],cardinalidad_maxima_por_archivo=a['cardinality'],rango_global_o_ejemplos=values))
    table(pd.DataFrame(rows),'diccionario_original.csv')
    return rows


if __name__=='__main__':
    prepare(force=True);original_dictionary()
