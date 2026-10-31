"""Auditoria reproducible de los CSV originales PRF; no entrena modelos.

Ejecutar: python INVESTIGACION_DATASETS/perfilar_prf.py
No modifica ni descomprime permanentemente los ZIP de origen.
"""
from pathlib import Path
from collections import Counter
import json
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'perfiles'
OUT.mkdir(exist_ok=True)


def read_csv(kind, year):
    with zipfile.ZipFile(ROOT / 'fuentes_brasil' / f'{kind}_{year}.zip') as z:
        member = next(n for n in z.namelist() if n.lower().endswith('.csv'))
        with z.open(member) as f:
            df = pd.read_csv(f, sep=';', encoding='latin1', dtype=str,
                             keep_default_na=False)
    df.columns = df.columns.str.strip().str.lstrip('\ufeff')
    for col in ('id', 'pesid', 'id_veiculo'):
        if col in df:
            df[col] = df[col].str.strip().str.replace(r'\.0$', '', regex=True)
    return df


def counts(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).items()}


profiles, daily, monthly_uf = [], [], []
all_crashes, all_people, all_vehicles = set(), set(), set()
all_labels = Counter()
schema_o, schema_p = None, None
for year in range(2017, 2026):
    o, p = read_csv('ocorrencias', year), read_csv('pessoas', year)
    oid = set(o['id'])
    pid_valid = p['pesid'].str.fullmatch(r'\d+') & pd.to_numeric(p['pesid'], errors='coerce').gt(0)
    vid_valid = p['id_veiculo'].str.fullmatch(r'\d+') & pd.to_numeric(p['id_veiculo'], errors='coerce').gt(0)
    pids = set(p.loc[pid_valid, 'pesid'])
    vids = set(p.loc[vid_valid, 'id_veiculo'])
    crash_dups = int(o.duplicated('id').sum())
    if crash_dups:
        raise ValueError(f'{year}: id de accidente duplicado; revisar antes de unir')
    joined = p[['id', 'pesid', 'data_inversa', 'uf']].merge(
        o[['id', 'data_inversa', 'uf']], on='id', how='left',
        validate='many_to_one', indicator=True, suffixes=('_persona', '_accidente'))
    matched = joined['_merge'].eq('both')
    label = p['estado_fisico'].str.strip()
    eligible = label.isin(['Lesões Leves', 'Lesões Graves', 'Óbito', 'Morto'])
    age = pd.to_numeric(p['idade'], errors='coerce')
    ve_year = pd.to_numeric(p['ano_fabricacao_veiculo'], errors='coerce')
    dates = pd.to_datetime(o['data_inversa'], errors='coerce', format='mixed', dayfirst=False)
    expected_days = pd.date_range(f'{year}-01-01', f'{year}-12-31')
    observed_days = pd.DatetimeIndex(dates.dropna().unique())
    person_rows_by_crash = p.groupby('id').size()
    declared_people = pd.to_numeric(o.set_index('id')['pessoas'], errors='coerce')
    reconciled = declared_people.to_frame('declaradas').join(person_rows_by_crash.rename('filas_personas'))
    vehicle_conflicts = p.loc[vid_valid].groupby(['id', 'id_veiculo'])[
        ['tipo_veiculo', 'marca', 'ano_fabricacao_veiculo']].nunique().gt(1).any(axis=1)
    this_labels = counts(label)
    all_labels.update(this_labels)
    info = {
        'anio': year, 'filas_accidentes': len(o), 'accidentes_id_unicos': len(oid),
        'columnas_accidentes': len(o.columns), 'filas_personas': len(p),
        'columnas_personas': len(p.columns), 'personas_pesid_unicos_validos': len(pids),
        'filas_sin_pesid_positivo': int((~pid_valid).sum()),
        'filas_pesid_cero': int(p['pesid'].eq('0').sum()),
        'filas_pesid_cero_y_estado_na': int((p['pesid'].eq('0') & label.eq('NA')).sum()),
        'pesid_duplicados_validos': int(p.loc[pid_valid].duplicated('pesid').sum()),
        'pares_accidente_persona_duplicados': int(p.duplicated(['id', 'pesid']).sum()),
        'pares_accidente_persona_duplicados_pesid_positivo': int(p.loc[pid_valid].duplicated(['id', 'pesid']).sum()),
        'filas_exactas_duplicadas_personas': int(p.duplicated().sum()),
        'accidentes_repetidos_anios_anteriores': len(oid & all_crashes),
        'pesid_repetidos_anios_anteriores': len(pids & all_people),
        'vehiculos_id_unicos_validos': len(vids),
        'vehiculos_repetidos_anios_anteriores': len(vids & all_vehicles),
        'vehiculos_con_atributos_discordantes': int(vehicle_conflicts.sum()),
        'filas_sin_id_vehiculo_valido': int((~vid_valid).sum()),
        'personas_con_accidente_encontrado': int(matched.sum()),
        'personas_sin_accidente_encontrado': int((~matched).sum()),
        'ids_accidente_solo_tabla_personas': len(set(p['id']) - oid),
        'accidentes_sin_filas_personas': len(oid - set(p['id'])),
        'fechas_discordantes_en_join': int((matched & joined['data_inversa_persona'].ne(joined['data_inversa_accidente'])).sum()),
        'uf_discordantes_en_join': int((matched & joined['uf_persona'].ne(joined['uf_accidente'])).sum()),
        'accidentes_con_conteo_personas_discordante': int(reconciled['declaradas'].ne(reconciled['filas_personas']).sum()),
        'personas_declaradas_tabla_accidentes': int(declared_people.sum()),
        'fecha_min': str(dates.min().date()), 'fecha_max': str(dates.max().date()),
        'fechas_no_interpretables': int(dates.isna().sum()),
        'fechas_fuera_del_anio': int(dates.dt.year.ne(year).sum()),
        'dias_con_registros': len(observed_days),
        'dias_calendario_sin_registros': [str(d.date()) for d in expected_days.difference(observed_days)],
        'estados_fisicos': this_labels,
        'sexo': counts(p['sexo']),
        'candidatas_heridas_o_fallecidas_sin_limpiar': int(eligible.sum()),
        'candidatas_clave_duplicada': int(p.loc[eligible].duplicated(['id', 'pesid']).sum()),
        'candidatas_con_pesid_valido_y_join': int((eligible & pid_valid & matched.to_numpy()).sum()),
        'candidatas_edad_0_110_y_sexo_informado': int((eligible & age.between(0, 110) & p['sexo'].isin(['Masculino', 'Feminino'])).sum()),
        'edad_no_numerica': int(age.isna().sum()),
        'edad_negativa': int(age.lt(0).sum()), 'edad_cero': int(age.eq(0).sum()),
        'edad_mayor_110': int(age.gt(110).sum()),
        'anio_vehiculo_cero': int(ve_year.eq(0).sum()),
        'anio_vehiculo_no_plausible_1900_al_anio': int((~ve_year.between(1900, year)).sum()),
        'causas_distintas': int(o['causa_acidente'].nunique()),
        'tipos_accidente_distintos': int(o['tipo_acidente'].nunique()),
        'trazados_distintos': int(o['tracado_via'].nunique()),
        'uf_distintas': int(o['uf'].nunique()),
        'columnas_o': list(o.columns), 'columnas_p': list(p.columns),
        'faltantes_literales_personas': {
            c: int(p[c].str.strip().str.casefold().isin(['', 'na', 'nan', 'null', 'não informado', 'ignorado', 'inválido']).sum())
            for c in p.columns},
    }
    if schema_o is None:
        schema_o, schema_p = list(o.columns), list(p.columns)
    info['mismas_columnas_que_2017'] = list(o.columns) == schema_o and list(p.columns) == schema_p
    profiles.append(info)
    all_crashes.update(oid)
    all_people.update(pids)
    all_vehicles.update(vids)
    daily.append(pd.DataFrame({'fecha': dates}).value_counts().rename('accidentes').reset_index())
    monthly_uf.append(pd.DataFrame({'mes': dates.dt.to_period('M').astype(str), 'uf': o['uf']}).value_counts().rename('accidentes').reset_index())
    (OUT / f'prf_{year}.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({k: info[k] for k in ['anio', 'filas_accidentes', 'filas_personas', 'personas_sin_accidente_encontrado', 'candidatas_heridas_o_fallecidas_sin_limpiar', 'pares_accidente_persona_duplicados']}, ensure_ascii=False), flush=True)

summary = {
    'periodo': '2017-2025', 'accidentes_filas': sum(p['filas_accidentes'] for p in profiles),
    'accidentes_ids_unicos': len(all_crashes),
    'personas_filas': sum(p['filas_personas'] for p in profiles),
    'personas_pesid_unicos_validos': len(all_people),
    'vehiculos_ids_unicos_validos': len(all_vehicles),
    'estados_fisicos': dict(all_labels),
    'candidatas_heridas_o_fallecidas_sin_limpiar': sum(p['candidatas_heridas_o_fallecidas_sin_limpiar'] for p in profiles),
    'dias_con_registros': sum(p['dias_con_registros'] for p in profiles),
    'anios': profiles,
    'advertencia': 'pesid identifica una participacion registrada; no demuestra personas naturales unicas entre distintos accidentes. Candidatas antes de limpieza; no es N final para modelar.',
}
(OUT / 'resumen_prf_2017_2025.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
cols = ['anio', 'filas_accidentes', 'filas_personas', 'personas_pesid_unicos_validos',
        'vehiculos_id_unicos_validos', 'candidatas_heridas_o_fallecidas_sin_limpiar',
        'personas_sin_accidente_encontrado', 'pares_accidente_persona_duplicados',
        'dias_con_registros']
pd.DataFrame(profiles)[cols].to_csv(OUT / 'cantidades_por_anio.csv', index=False, encoding='utf-8-sig')
pd.concat(daily).sort_values('fecha').to_csv(OUT / 'accidentes_por_dia.csv', index=False)
pd.concat(monthly_uf).sort_values(['mes', 'uf']).to_csv(OUT / 'accidentes_por_mes_uf.csv', index=False)
print(json.dumps({k: v for k, v in summary.items() if k != 'anios'}, ensure_ascii=False, indent=2), flush=True)
