"""Preparación reproducible de demografía y resúmenes de contexto.

reconstruir() conserva frecuencias/orden de 12.2.1 y edades desconocidas como NA.
regenerar_resumenes() coteja o crea los tres resúmenes desde sus tablas originales.
El CLI ejecuta ambas funciones sin ejecutar ni alterar las Fases 1 y 2.
"""
from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EDADES = ['De 0 a 13 anos', 'De 14 a 17 anos', 'De 18 a 29 anos',
          'De 30 a 39 anos', 'De 40 a 49 anos', 'De 50 a 59 anos',
          'De 60 anos y mas', 'Ignorado']


def reconstruir(root=ROOT):
    fuente = next((root / 'data').glob('12.2.1.*.csv'))
    raw = pd.read_csv(fuente, sep=';', dtype=str, encoding='utf-8-sig')
    filas = []
    for _, row in raw.iterrows():
        edad = row.iloc[0].strip()
        if edad == 'TOTAL':
            continue
        for gravedad, sexo, col in [
            ('Herido', 'Hombre', 'LESION CORPORAL - HOMBRES'),
            ('Herido', 'Mujer', 'LESION CORPORAL - MUJERES'),
            ('Fallecido', 'Hombre', 'HOMICIDIO - HOMBRES'),
            ('Fallecido', 'Mujer', 'HOMICIDIO - MUJERES')]:
            n = int(row[col].replace('.', '').strip())
            filas.extend([{'grupo_edad': edad, 'sexo': sexo, 'gravedad': gravedad}] * n)
    df = pd.DataFrame(filas)
    df.insert(0, 'id_victima', range(1, len(df) + 1))
    df['es_fallecido'] = (df.gravedad == 'Fallecido').astype(int)
    df['es_hombre'] = (df.sexo == 'Hombre').astype(int)
    df['es_adulto_mayor'] = df.grupo_edad.eq('De 60 anos y mas').astype('Int64')
    df.loc[df.grupo_edad.eq('Ignorado'), 'es_adulto_mayor'] = pd.NA
    df['edad_orden'] = df.grupo_edad.map({e: i for i, e in enumerate(EDADES[:7])}).astype('Int64')
    assert len(df) == 5493 and df.es_fallecido.sum() == 980
    assert len(df[['sexo', 'grupo_edad']].drop_duplicates()) == 16
    dest = root / 'output' / 'victimas_individual_limpio.csv'
    dest.parent.mkdir(exist_ok=True)
    if dest.exists():
        previo = pd.read_csv(dest)
        # Única migración admitida: corregir los dos indicadores derivados de edad.
        columnas = df.columns.difference(['edad_orden', 'es_adulto_mayor'])
        pd.testing.assert_frame_equal(df[columnas], previo[columnas], check_dtype=False)
    contenido = df.to_csv(index=False).encode('utf-8-sig')
    if not dest.exists() or dest.read_bytes() != contenido:
        dest.write_bytes(contenido)
    return df, {'fuente': fuente.name, 'sha256_fuente': hashlib.sha256(fuente.read_bytes()).hexdigest(),
                'filas': len(df), 'fallecidos': int(df.es_fallecido.sum()), 'perfiles': 16,
                'comparacion_csv_historico': 'frecuencias y orden preservados; indicadores desconocidos corregidos a NA'}




MESES=['ENE.','FEB.','MAR.','ABR.','MAY.','JUN.','JUL.','AGO.','SET.','OCT.','NOV.','DIC.']


def regenerar_resumenes(root=ROOT):
    def leer(prefijo):
        return pd.read_csv(next((root/'data').glob(prefijo+'*.csv')),sep=';',dtype=str)
    def numero(s):
        s=str(s).strip()
        return 0 if s=='-' else int(s.replace('.',''))
    z=leer('12.2.6.').iloc[0]
    zonas=pd.DataFrame([dict(zona=nombre,heridos=numero(z['HERIDOS - '+col]),
                              fallecidos=numero(z['MUERTOS - '+col]))
                        for nombre,col in [('Asunción','ASUNCION'),('Central','ZONA CENTRAL'),('Interior','INTERIOR')]])
    zonas['total_victimas']=zonas.heridos+zonas.fallecidos
    zonas['letalidad_pct']=100*zonas.fallecidos/zonas.total_victimas
    rutas=leer('12.2.9.')
    ruta_py02=rutas.loc[rutas['RUTA Y RAMAL'].str.contains('PY02')].iloc[0]
    excluir=rutas['RUTA Y RAMAL'].str.strip().eq('TOTAL')|rutas['RUTA Y RAMAL'].str.contains('Nacionales y Departamentales',case=False)
    top=rutas.loc[~excluir,['RUTA Y RAMAL']].copy()
    top['siniestros']=rutas.loc[~excluir,'TOTAL'].map(numero)
    top=top.sort_values('siniestros',ascending=False).head(10).reset_index(drop=True)
    horas=leer('12.2.4.').iloc[1:].reset_index(drop=True)
    dias=leer('12.2.7.').iloc[1:].reset_index(drop=True)
    causas=leer('12.2.3.')
    causa=causas.loc[causas['POSIBLES CAUSAS'].str.contains('No conservar distancia')].iloc[0]
    if len(horas)!=12 or len(dias)!=12 or horas.MES.str.strip().tolist()!=dias.MES.str.strip().tolist():
        raise ValueError('Meses de contexto incompatibles')
    mensual=pd.DataFrame({'mes_id':range(1,13),'mes_nombre':horas.MES})
    mensual['fecha']=pd.date_range('2021-01-01',periods=12,freq='MS')
    mensual['trimestre']=mensual.fecha.dt.to_period('Q').astype(str)
    mensual['accidentes_totales']=horas.TOTAL.map(numero)
    mensual['accidentes_py02']=[numero(ruta_py02[m]) for m in MESES]
    mensual['accidentes_tarde_noche']=sum(horas[c].map(numero) for c in ['DE 15:00 a 17:59 HORAS','DE 18:00 a 20:59 HORAS','DE 21:00 a 23:59 HORAS'])
    mensual['accidentes_fin_de_semana']=sum(dias[c].map(numero) for c in ['DIA VIERNES','DIA SABADO','DIA DOMINGO'])
    mensual['causa_no_guardar_distancia']=[numero(causa['ANO 2021 - '+m]) for m in MESES]
    if mensual.accidentes_totales.sum()!=1942:
        raise ValueError('Total mensual inesperado')
    tablas={'victimas_zona_resumen.csv':zonas,'siniestros_mensual_2021.csv':mensual,'top10_rutas_siniestros.csv':top}
    (root/'output').mkdir(exist_ok=True)
    for nombre,tabla in tablas.items():
        path=root/'output'/nombre
        contenido=tabla.to_csv(index=False,encoding='utf-8-sig')
        # Validar antes de escribir; no reemplazar un resultado diferente silenciosamente.
        if path.exists():
            previo=pd.read_csv(path)
            esperado=tabla.copy()
            if 'fecha' in esperado: esperado['fecha']=esperado.fecha.dt.strftime('%Y-%m-%d')
            pd.testing.assert_frame_equal(esperado,previo,check_dtype=False,rtol=1e-12)
        if not path.exists(): path.write_text(contenido,encoding='utf-8-sig')
    return tablas


if __name__ == '__main__':
    print(reconstruir()[1])
    print({nombre: len(tabla) for nombre, tabla in regenerar_resumenes().items()})
    print('El CSV vehicular conserva sus etiquetas históricas; H3 se coteja con DINATRAN mediante conteos agregados, sin crear registros individuales.')
