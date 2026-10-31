"""Lee originales, audita la union y conserva personas reales sin imputar desenlace."""
import json
import zipfile
import unicodedata
import hashlib
import joblib
import numpy as np
import pandas as pd
from common import ROOT, RAW, DATA, OUT, save_json, table, log

PERSON_FIELDS = ['id', 'pesid', 'id_veiculo', 'estado_fisico', 'idade', 'sexo', 'tipo_envolvido', 'tipo_veiculo', 'ano_fabricacao_veiculo']
EVENT_FIELDS = ['id', 'data_inversa', 'horario', 'uf', 'br', 'km', 'municipio', 'tipo_acidente', 'fase_dia', 'sentido_via', 'condicao_metereologica', 'tipo_pista', 'tracado_via', 'uso_solo', 'latitude', 'longitude']
CAT = ['sexo', 'tipo_envolvido', 'tipo_veiculo', 'uf', 'br', 'municipio', 'tipo_acidente', 'fase_dia', 'sentido_via', 'condicao_metereologica', 'tipo_pista', 'tracado_via', 'uso_solo', 'dia_semana']
NUM = ['idade', 'idade_veiculo', 'hora', 'hora_sin', 'hora_cos', 'mes_sin', 'mes_cos', 'latitude', 'longitude', 'km']
FEATURES = NUM + CAT
UNKNOWN = {'', 'NA', 'NAN', 'NULL', 'NAO INFORMADO', 'IGNORADO', 'INVALIDO'}


def norm(value):
    s = ' '.join(str(value).strip().upper().split())
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    return 'DESCONOCIDO' if s in UNKNOWN else s


def read(kind, year):
    path = RAW / f'{kind}_{year}.zip'
    with zipfile.ZipFile(path) as z:
        with z.open(next(n for n in z.namelist() if n.lower().endswith('.csv'))) as f:
            return pd.read_csv(f, sep=';', encoding='latin1', dtype=str, keep_default_na=False)


def number(s):
    return pd.to_numeric(s.astype(str).str.replace(',', '.', regex=False), errors='coerce')


def prepare(force=False):
    target = DATA / 'victimas_modelado.joblib'
    if target.exists() and not force:
        return load_existing()
    frames, audits, bitacora = [], [], []
    manifests = json.loads((ROOT / 'data/manifiesto_origenes.json').read_text(encoding='utf8'))
    hashes = {x['archivo']: x['sha256'] for x in manifests}
    for year in range(2017, 2026):
        for kind in ['ocorrencias', 'pessoas']:
            f = RAW / f'{kind}_{year}.zip'
            assert hashlib.sha256(f.read_bytes()).hexdigest() == hashes[f.name], f'Hash distinto: {f}'
        o, p = read('ocorrencias', year), read('pessoas', year)
        assert o['id'].is_unique
        eligible = p.estado_fisico.isin(['Lesões Leves', 'Lesões Graves', 'Óbito'])
        q = p.loc[eligible, PERSON_FIELDS].copy()
        assert pd.to_numeric(q.pesid).gt(0).all()
        assert not q.duplicated(['id', 'pesid']).any()
        q = q.merge(o[EVENT_FIELDS], on='id', how='left', validate='many_to_one', indicator=True)
        assert q['_merge'].eq('both').all()
        q.drop(columns='_merge', inplace=True)
        q['fallecido'] = q.estado_fisico.eq('Óbito').astype('int8')
        q['fecha'] = pd.to_datetime(q.data_inversa, format='%Y-%m-%d', errors='raise')
        q['ano'] = q.fecha.dt.year.astype('int16')
        assert q.ano.eq(year).all()
        age = number(q.idade)
        bad_age = ~age.between(1, 110)
        q['idade'] = age.mask(bad_age).astype('float32')
        vy = number(q.ano_fabricacao_veiculo)
        bad_vy = ~vy.between(1900, year)
        q['idade_veiculo'] = (year - vy).mask(bad_vy).astype('float32')
        h = pd.to_timedelta(q.horario, errors='coerce').dt.total_seconds() / 3600
        h = h.where(h.between(0, 24, inclusive='left'))
        q['hora'] = h.astype('float32')
        q['hora_sin'] = np.sin(2 * np.pi * h / 24).astype('float32')
        q['hora_cos'] = np.cos(2 * np.pi * h / 24).astype('float32')
        q['mes_sin'] = np.sin(2 * np.pi * (q.fecha.dt.month - 1) / 12).astype('float32')
        q['mes_cos'] = np.cos(2 * np.pi * (q.fecha.dt.month - 1) / 12).astype('float32')
        q['dia_semana'] = q.fecha.dt.dayofweek.astype(str)
        for name, lower, upper in [('latitude', -34, 6), ('longitude', -74, -34), ('km', 0, 10000)]:
            v = number(q[name]); bad = ~v.between(lower, upper)
            q[name] = v.mask(bad).astype('float32')
            bitacora.append(dict(ano=year, decision=f'{name}: rango {lower}..{upper}; fuera o no numerico a faltante', filas=int(bad.sum()), fundamento='No imputar coordenadas/posiciones imposibles como cero; conservar victima'))
        for col in CAT:
            mapping = {v: norm(v) for v in q[col].unique()}
            q[col] = q[col].map(mapping)
        q.loc[q['br'].isin(['0', '0.0']), 'br'] = 'DESCONOCIDO'
        for col in ['id', 'pesid', 'id_veiculo']:
            q[col] = pd.to_numeric(q[col], errors='raise').astype('int64')
        for decision, count, reason in [
            ('Excluir desenlaces ilesos/desconocidos del objetivo', len(p) - int(eligible.sum()), 'La pregunta compara lesiones no fatales con fallecimiento, no todos los involucrados'),
            ('Edad fuera de 1..110, incluido cero ambiguo, a faltante sin borrar fila', int(bad_age.sum()), 'Cero puede ser edad real o codigo no informado; no se fuerza edad de lactante'),
            ('Anio de vehiculo fuera de 1900..anio del siniestro a faltante', int(bad_vy.sum()), 'No interpretar codigo cero como vehiculo de mas de dos mil anios'),
        ]:
            bitacora.append(dict(ano=year, decision=decision, filas=count, fundamento=reason))
        frames.append(q[['id', 'pesid', 'id_veiculo', 'fecha', 'ano', 'fallecido'] + FEATURES])
        audits.append(dict(ano=year, filas_originales_personas=len(p), elegibles=len(q), fallecidos=int(q.fallecido.sum()), heridos=int(q.fallecido.eq(0).sum()), accidentes_elegibles=int(q.id.nunique()), sin_union=0, claves_duplicadas=0))
        log(f'Preparado {year}: {len(q):,} victimas')
    d = pd.concat(frames, ignore_index=True)
    assert len(d) == 754098 and d.pesid.is_unique
    for col in CAT:
        d[col] = d[col].astype('category')
    d.sort_values(['fecha', 'id', 'pesid'], inplace=True, ignore_index=True)
    joblib.dump(d, target, compress=3)
    d.to_parquet(DATA / 'victimas_limpias.parquet', index=False, compression='zstd')
    d.to_csv(DATA / 'victimas_limpias.csv.gz', index=False, compression='gzip', encoding='utf8')
    table(pd.DataFrame(audits), 'auditoria_union_y_clases.csv')
    table(pd.DataFrame(bitacora), 'bitacora_limpieza.csv')
    split = d.assign(particion=np.select([d.ano.le(2023), d.fecha.lt('2024-07-01'), d.ano.eq(2024)], ['desarrollo_2017_2023', 'calibracion_2024_H1', 'umbral_2024_H2'], default='prueba_2025'))
    partition = split.groupby('particion').agg(filas=('pesid', 'size'), accidentes=('id', 'nunique'), fallecidos=('fallecido', 'sum'))
    partition['heridos'] = partition.filas - partition.fallecidos
    partition['proporcion_fallecidos'] = partition.fallecidos / partition.filas
    table(partition.reset_index(), 'particiones.csv')
    id_sets = [set(g.id) for _, g in split.groupby('particion')]
    for i in range(len(id_sets)):
        for j in range(i):
            assert not id_sets[i] & id_sets[j]
    descriptions = {
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
    dictionary=[]
    for c in d:
        missing=d[c].isna() | (d[c].astype(str).eq('DESCONOCIDO') if c in CAT else False)
        dictionary.append(dict(variable=c, descripcion=descriptions[c], tipo=str(d[c].dtype), valores_distintos=int(d[c].nunique()), faltantes=int(missing.sum()), porcentaje_faltante=100*float(missing.mean()), predictor=c in FEATURES))
    table(pd.DataFrame(dictionary), 'diccionario_final.csv')
    original = json.loads((ROOT / 'data/perfil_original_prf.json').read_text(encoding='utf8'))
    table(pd.DataFrame([dict(variable=c, columnas_en='personas' if c in original['anios'][0]['columnas_p'] else 'accidentes', faltantes_literales=sum(a['faltantes_literales_personas'].get(c, 0) for a in original['anios']), nota='Perfil original completo y definicion oficial en INVESTIGACION_DATASETS/perfiles y diccionarios PDF') for c in sorted(set(original['anios'][0]['columnas_o']) | set(original['anios'][0]['columnas_p']))]), 'inventario_columnas_originales.csv')
    save_json(dict(filas=len(d), fallecidos=int(d.fallecido.sum()), heridos=int(d.fallecido.eq(0).sum()), predictores=FEATURES, union='many_to_one id validada sin expansion', entre_particiones_accidentes_compartidos=0, imputacion='Ninguna en dataset; se aprende en cada entrenamiento', manifiesto_original='data/manifiesto_origenes.json'), OUT / 'auditoria_preparacion.json')
    return d


def load_existing():
    return joblib.load(DATA / 'victimas_modelado.joblib')


if __name__ == '__main__':
    prepare(force=True)
