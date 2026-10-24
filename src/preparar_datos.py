"""Reconstrucción determinista de las frecuencias demográficas de 12.2.1.

No ejecuta ni altera las Fases 1 y 2. Verifica conteos y orden contra el CSV
existente, y regenera los indicadores de edad desconocida como NA.
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


if __name__ == '__main__':
    print(reconstruir()[1])
