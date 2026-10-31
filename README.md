# Proyecto Integrador - Gravedad de víctimas en Brasil

La entrega conserva una sola opción: **LightGBM final de 31 características**, con AUC 0,845 en las 67.591 víctimas del corte enero-septiembre de 2026. El estudio principal usa 2017-2025; 2026 es validación posterior. Persisten omisiones y falsas alarmas: no es un modelo clínico validado.

## Orden recomendado de lectura

1. [Comprensión del problema](output/reports/Comprension_del_problema.pdf) - contexto, pregunta, objetivos y alcance.
2. [Fase 1: preparación y exploración](output/reports/Fase_1_Preparacion_y_EDA.pdf).
3. [Fase 2: inferencia](output/reports/Fase_2_Inferencia.pdf).
4. [Fase 3: modelo final y evaluación](output/reports/Fase_3_Modelado_y_Evaluacion.pdf).
5. [Informe integrador](output/reports/Informe_Integrador.pdf).

Los notebooks ejecutados están en `notebooks/` y sus exportaciones en `output/html/`. No hay otra carpeta de proyecto ni un complemento separado para elegir.

## Archivos necesarios

| Carpeta/archivo | Propósito |
|---|---|
| `data/raw/` | Fuentes seleccionadas de PRF y diccionarios oficiales. Se conservan localmente; no se suben a Git ni al ZIP por su volumen. |
| `data/fuentes.json` | URL, tamaño y SHA-256 de cada fuente del corte registrado. |
| `data/processed/victimas_limpias.parquet` | único dataset limpio: 821.689 participaciones, incluidas las 67.591 de validación posterior. La exploración e inferencia se restringen a 2017-2023. |
| `data/metodologia/` | Protocolos y congelamientos originales: evidencia del proceso de selección anterior a la prueba posterior. |
| `data/ejemplo_inferencia.csv` | Ejemplo de las 31 entradas preparadas, sin objetivo. |
| `notebooks/` | Tres notebooks explicados y ejecutados. |
| `src/` | Descarga, preparación, análisis, comparación, modelo final, inferencia y generación de entregables. |
| `output/reports/` | Cinco PDF exigidos por las tres fases. |
| `output/html/` | Tres exportaciones HTML de los notebooks. |
| `output/tables/`, `output/figures/` | Diccionarios original/final, bitácora, contrastes y evidencias usadas en los informes. |
| `output/modelado/` | Tablas y registros necesarios para demostrar comparación de familias, ajuste temporal y evaluación. No son otros proyectos para elegir. |
| `output/modelo/modelo_final.joblib` | único modelo serializado conservado, con codificador, calibrador y umbrales. |
| `requirements.txt`, `protocolo.json` | Dependencias y decisiones generales. |
| `dist/` | ZIP acumulativo para entrega; se genera localmente y no se versiona. |

## Reproducción

Python 3.13 recomendado; semilla 42. Desde la raíz:

```powershell
python -m pip install -r requirements.txt
python src/descargar_fuentes.py
python src/reproducir.py
python src/notebooks.py
python src/informes.py
python src/verificar.py
python src/empaquetar.py
```

La descarga solo se necesita cuando faltan originales. Las fuentes se validan por hash: si PRF cambió el archivo, el proceso lo señala en vez de sustituir silenciosamente el corte. Solo se consultan descargas públicas; no se envían pedidos institucionales.

`reproducir.py` reconstruye preparación y análisis y conserva los resultados de entrenamiento registrados. Para reconstruir también todos los ajustes:

```powershell
python src/reproducir.py --reentrenar
```

Ese cálculo puede tardar varios minutos y requiere varios GB de RAM. Reproducir un experimento cuyo resultado ya se conoce no crea una prueba ciega nueva. La selección histórica inicial y final está documentada; no se ajustaron variables o umbrales usando 2026.

Los notebooks se ejecutan por separado y descargan las fuentes si faltan. `informes.py` requiere reportlab y genera PDF desde resultados calculados, sin reentrenar. Para renderizar páginas para inspección visual puede utilizarse Poppler o pypdfium2; estas herramientas de revisión no forman parte del análisis estadístico.

## Aplicar el único modelo final

```powershell
python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida tmp/ejemplo_predicciones.csv
```

Crear la carpeta de salida si no existe. La entrada debe tener las características YA preparadas según `src/preparar.py`. El contexto vehicular requiere todos los vehículos identificados del siniestro; no se inventa desde una sola víctima aislada. El script no acepta el CSV original como si ya tuviera esas columnas transformadas.

## Qué exige conservar la cátedra

Las comparaciones con logística, árbol, Bayes y referencias siguen en tablas y código porque la fase 3 exige al menos tres familias. Se eliminaron sus modelos serializados descartados y las versiones de proyecto separadas. Los informes respetan los límites: comprensión 3 páginas, fase 1 hasta 20, fase 2 hasta 15, fase 3 hasta 15 e integrador hasta 30.

La carpeta `dist` contiene una sola entrega acumulativa `Fase3_DataScience_Alcaraz-Ferreira-Rios.zip`, sin fuentes originales voluminosas. El historial Git anterior se conserva; esta limpieza no lo reescribe.

## Integrantes, alcance e integridad

Alan Alcaraz, Leandro Ferreira y Jorge Rios. **Faltan los legajos:** deben completarlos los integrantes. No se inventa aprobación docente ni contribuciones individuales. Se declara asistencia de IA en programación, análisis y redacción; el grupo debe revisar, comprender y asumir las decisiones e interpretaciones antes de entregar. La exposición oral y sus diapositivas son una instancia de cierre que debe preparar y defender el grupo.

La población es la de víctimas lesionadas registradas por PRF en carreteras federales, no todos los viajes o accidentes de Brasil ni Paraguay. Faltan exposición, velocidad de impacto, seguridad y seguimiento clínico completo. No se deduce causalidad ni se aplica el modelo a decisiones médicas.

Fuentes oficiales: [Datos abiertos de PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf) y [diccionarios](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes).
