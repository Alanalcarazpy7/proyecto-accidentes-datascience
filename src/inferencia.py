"""Inferencia académica independiente. No estima riesgo individual calibrado."""
import argparse
import json
from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def inferir(sexo, grupo_edad, modelo=None):
    ruta = Path(modelo) if modelo else ROOT / 'output' / 'fase3' / 'mejor_modelo_fase3.joblib'
    clf = joblib.load(ruta)
    meta = clf.metadatos_fase3_
    valores = {'sexo': sexo, 'grupo_edad': grupo_edad}
    for k, v in valores.items():
        if v not in meta['categorias'][k]:
            raise ValueError(f'{k} no reconocido: {v!r}. Permitidos: {meta["categorias"][k]}')
    if list(clf.feature_names_in_) != meta['variables']:
        raise ValueError('El modelo y los metadatos no tienen las mismas variables.')
    x = pd.DataFrame([valores], columns=meta['variables'])
    clase = int(clf.predict(x)[0])
    return {'modelo': meta['modelo'], 'clase': clase,
            'etiqueta': 'Fallecido' if clase else 'Herido',
            'puntuacion_no_calibrada': float(clf.predict_proba(x)[0, 1]),
            'alcance': 'Clasificación retrospectiva académica; sin validación externa ni uso clínico.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sexo', required=True)
    p.add_argument('--grupo-edad', required=True)
    p.add_argument('--modelo', type=Path)
    a = p.parse_args()
    try:
        print(json.dumps(inferir(a.sexo, a.grupo_edad, a.modelo), ensure_ascii=False, indent=2))
    except (ValueError, FileNotFoundError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()
