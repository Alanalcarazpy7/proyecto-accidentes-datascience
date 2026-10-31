# Clasificación de gravedad de víctimas — PRF Brasil

Abrir **ABRIR_RESULTADOS.html** para ver resultados, PDFs y notebooks. El modelo usa 24 características reales; distingue mejor que sexo/edad, pero sigue produciendo errores importantes. Los informes son material de apoyo con asistencia de IA que el grupo debe verificar y comprender antes de presentar.

## Datos y alcance

754.098 participaciones con desenlace conocido, 2017–2025; 703.273 heridas y 50.825 fallecidas. Las 632.713 ocurrencias originales se vinculan con personas mediante `id`. No se fabrican individuos ni se confunden filas sin `pesid` válido con personas reales. No hay identidad civil longitudinal. Brasil significa carreteras federales cubiertas por PRF, no toda circulación vial ni Paraguay.

El directorio vecino `INVESTIGACION_DATASETS/fuentes_brasil` contiene los originales descargados. Si no existe, se usan `data/raw` y el descargador incluido. Procedencia, URL y SHA-256 en `data/manifiesto_origenes.json`; diccionarios oficiales y perfil completo en las fuentes y `data/perfil_original_prf.json`.

Fuentes oficiales: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf y https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes . Los datos se presentan como abiertos reutilizables por PRF. No se enviaron solicitudes institucionales ni archivos a terceros.

## Reproducir

Python 3.13 recomendado, dependencias declaradas en `requirements.txt`; se usaron semilla 42 y seis hilos para LightGBM. Desde esta carpeta:

```powershell
python -m pip install -r requirements.txt
python src/descargar_fuentes.py
python src/preparar.py
python src/run_all.py
python src/entregables.py
python src/informes_pdf.py
python src/verificar.py
```

No hace falta descargar de nuevo si los originales están presentes. `run_all.py` conserva la selección y los resultados de prueba existentes. Para reproducir desde cero, usar una copia nueva sin salidas/modelos generados, manteniendo el protocolo: eso reproduce un experimento retrospectivo, no convierte 2025 en una nueva prueba ciega. Un cambio de decisión después de ver 2025 exige otra evaluación futura independiente.

Los notebooks están ejecutados y también pueden abrirse por separado. El primero reconstruye desde originales. Los PDF se generan desde tablas congeladas sin reentrenar. La versión de reportlab puede estar en un entorno distinto del de ML; no cambia las métricas. La ejecución local puede tardar varios minutos y requiere varios GB de RAM; solo la descarga necesita internet. Si PRF cambia un archivo, el hash falla deliberadamente y exige documentar otra versión.

## Inferencia

```powershell
python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida output/ejemplo_predicciones.csv
```

La entrada es una tabla con las 24 características YA preparadas según `src/preparar.py`, sin objetivo; no el CSV PRF bruto. Mantener unidades y códigos. El script conserva claves opcionales, aplica codificación, calibración y umbral guardados. No se utiliza para decidir atención médica.

## Estructura y archivos

- `data/processed/victimas_limpias.parquet`: dataset limpio portable; `victimas_limpias.csv.gz` es la versión CSV disponible localmente; el cache joblib acelera lecturas.
- `notebooks/`: tres notebooks; `output/html/`: sus versiones ejecutadas.
- `output/reports/`: comprensión, tres fases e integrador.
- `output/tables/`: auditoría, bitácora, diccionario, contrastes, CV, métricas y errores.
- `models/modelo_seleccionado.joblib`: pipeline final con calibrador y umbral.
- `protocolo.json` y `output/seleccion_congelada_antes_prueba.json`: decisiones anteriores a prueba.
- `contexto/correccion_antes_de_prueba.txt`: corrección técnica; los diagnósticos preliminares no son resultados finales.

El paquete excluye los originales (>25 MB), caches y CSV limpio duplicado; incluye Parquet y los scripts para reconstruirlos. El modelo se seleccionó por AP de CV, no por la mayor métrica de 2025. Los intervalos de prueba remuestrean accidentes completos, manteniendo juntas sus víctimas.

## Pendientes del grupo

Completar legajos; revisar cambio de país y dataset según lo acordado con la profesora; comprender y adoptar decisiones e interpretaciones; declarar el uso de IA; generar sus propias contribuciones e historial Git. No se inventa aprobación docente ni autoría de los integrantes. Esta carpeta no fue publicada ni compartida externamente.
