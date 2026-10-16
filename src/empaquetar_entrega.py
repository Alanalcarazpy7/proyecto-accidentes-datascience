"""Empaqueta una revisión local; no publica ni modifica el historial Git."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def archivos_entrega():
    # Lista explícita de entregables y dependencias; nunca empaqueta output/ entero.
    nombres = ['README.md', 'requirements.txt', 'requirements-lock.txt', '.gitignore', '.gitattributes',
        'notebooks/Fase1_Accidentes_Transito.ipynb', 'notebooks/Fase2_Analisis_Inferencial.ipynb',
        'notebooks/Fase3_Accidentes_AUDITADA.ipynb', 'tests/test_fase3.py',
        'src/preparar_datos.py', 'src/ejecutar_fase3.py', 'src/complementos_fase3.py',
        'src/generar_documentos.py', 'src/inferencia.py', 'src/empaquetar_entrega.py',
        'docs/fase3/Informe_Fase3.docx', 'docs/fase3/Informe_Fase3.pdf',
        'docs/integrador/Informe_Integrador_DataScience.docx', 'docs/integrador/Informe_Integrador_DataScience.pdf',
        'output/fase2/Fase2_Analisis_Inferencial.html', 'docs/fase2/Fase2_Analisis_Inferencial.pdf',
        'output/victimas_individual_limpio.csv', 'output/victimas_vehiculo_limpio.csv',
        'output/siniestros_mensual_2021.csv', 'output/victimas_zona_resumen.csv',
        'output/top10_rutas_siniestros.csv', 'output/fase2/resultados_fase2_consolidados.json',
        'output/fase2/resultados_h1_h2.json', 'output/fase2/tabla_resumen_fase2.csv',
        'output/fase1/bitacora_limpieza_datos.csv', 'output/fase3/mejor_modelo_fase3.joblib',
        'output/fase3/Fase3_Accidentes_AUDITADA.html']
    return [ROOT / n for n in nombres] + sorted((ROOT / 'data').glob('12.2.*.csv'))


def main():
    salida = ROOT / 'entrega'
    salida.mkdir(exist_ok=True)
    paths = archivos_entrega()
    assert all(p.is_file() for p in paths), [str(p) for p in paths if not p.is_file()]
    original_bytes = sum(p.stat().st_size for p in (ROOT / 'data').rglob('*') if p.is_file())
    assert original_bytes < 25 * 1024**2, 'Revisar límite de originales de la consigna.'
    nombre = 'REVISION_Fase3_DataScience_Alcaraz-Ferreira-Rios.zip'
    manifest = {'archivo': nombre, 'estado': 'Revisión técnica; falta confirmación administrativa y revisión personal del grupo.',
                'datos_originales_bytes': original_bytes,
                'archivos': {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)}}
    with zipfile.ZipFile(salida / nombre, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, p.relative_to(ROOT).as_posix())
        z.writestr('MANIFIESTO_REVISION.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(salida / nombre) as z:
        assert z.testzip() is None
        for name, v in manifest['archivos'].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == v['sha256']
    print(nombre, (salida / nombre).stat().st_size, 'bytes; CRC y SHA-256 verificados.')


if __name__ == '__main__':
    main()
