# Proyecto Integrador de Ciencia de Datos

**Tema:** gravedad de las víctimas de accidentes registrados por PRF en carreteras federales de Brasil.

Estudiamos qué características de la persona, el vehículo y el accidente se relacionan con la gravedad. Después comparamos modelos para distinguir entre víctimas heridas y fallecidas. No pronosticamos la cantidad de accidentes del próximo año.

El estudio usa 2017-2025 y una evaluación posterior de enero-septiembre de 2026. La opción final es **LightGBM con 31 características: AUC 0,845 y F1 macro 0,675**. No usamos `causa_acidente` en ese modelo.

## Qué leer

Para una lectura rápida de la Fase 3, usar el [resumen visual de seis páginas](output/resumen_fase3/Resumen_Fase_3_Continuidad_Paraguay_Brasil.pdf), que también incluye los principales resultados de las Fases 1 y 2. La [comparación completa con el proyecto de Paraguay](output/resumen_fase3/COMPARACION_PROYECTOS.md) explica qué se mantuvo y qué cambió en cada fase.

1. [Fase 1: datos, limpieza y gráficos](output/reports/Fase_1_Preparacion_y_EDA.pdf).
2. [Fase 2: hipótesis y pruebas estadísticas](output/reports/Fase_2_Inferencia.pdf).
3. [Fase 3: modelos, resultados y errores](output/reports/Fase_3_Modelado_y_Evaluacion.pdf).

La consigna también pide un [documento de comprensión del problema](output/reports/Comprension_del_problema.pdf) y un [informe integrador](output/reports/Informe_Integrador.pdf); por eso se conservan esos dos PDF.

## Código para estudiar y ejecutar por fase

Los pasos del análisis están escritos directamente en los tres notebooks, con explicaciones y resultados junto al código:

1. [Fase 1: preparación, uniones, limpieza y gráficos](notebooks/Fase_1_Preparacion_EDA.ipynb).
2. [Fase 2: muestra, cuatro hipótesis, pruebas e interpretación](notebooks/Fase_2_Inferencia.ipynb).
3. [Fase 3: modelos, entrenamiento, calibración, evaluación y errores](notebooks/Fase_3_Modelado.ipynb).

Abrirlos desde esta carpeta o desde `notebooks/` y ejecutar las celdas en orden. Primero ejecutar la Fase 1 si falta el dataset limpio. La Fase 3 usa por defecto el modelo guardado: comprueba sus predicciones y recalcula sus métricas sin volver a entrenarlo. El entrenamiento está visible en sus celdas y se puede repetir con `REENTRENAR = True`; esto reemplaza el modelo guardado y puede tardar bastante. La preparación necesaria para esa repetición también está incluida en el notebook.

Los tres notebooks son el código principal y se editan directamente: ya no dependen de los módulos de preparación, pruebas o entrenamiento de `src/`. Solo conservamos `src/inferencia.py` para aplicar el modelo por comando. Los PDF, el PPT y la guía Word se conservan como materiales finales.

La exposición actual está en [Presentacion_Tres_Fases_Brasil_Actualizada.pptx](output/presentacion_tres_fases/Presentacion_Tres_Fases_Brasil_Actualizada.pptx), acompañada por [la guía de estudio en Word](output/presentacion_tres_fases/Guia_Estudio_Tres_Fases_Brasil_Actualizada.docx).

## Archivos de la entrega

| Carpeta o archivo | Para qué sirve |
|---|---|
| `notebooks/` | Los tres notebooks ejecutados, con las operaciones visibles por fase. |
| `output/html/` | Los mismos notebooks en un formato que se puede abrir en el navegador. |
| `src/inferencia.py` | Aplicación del modelo a nuevas filas con las características ya preparadas. |
| `data/processed/victimas_limpias.parquet` | El único dataset limpio: 821.689 participaciones reales, con los períodos identificados. |
| `data/raw/`, `data/fuentes.json` | Originales locales y sus enlaces/huellas de verificación. Los originales pesados no se incluyen en el ZIP. |
| `data/metodologia/`, `protocolo.json` | Decisiones y registros originales de la selección del modelo. |
| `output/reports/` | Los informes PDF. |
| `output/tables/`, `output/figures/` | Diccionarios original/final, bitácora, tablas y gráficos que respaldan las tres fases. |
| `output/modelado/` | Resultados de comparación y validación que permiten justificar la elección. |
| `output/modelo/modelo_final.joblib` | El único modelo principal guardado. |
| `output/presentacion_tres_fases/` | PPT y guía Word actualizados de la exposición. |
| `requirements.txt` | Versiones de las bibliotecas utilizadas. |
| `dist/` | Un ZIP acumulativo listo para la entrega de las tres fases. |

Las comparaciones iniciales se conservan porque la cátedra exige varias familias de modelos. No son otras opciones de proyecto para estudiar o entregar.

## Cómo reproducirlo

Usamos Python 3.13 y semilla 42. Desde esta carpeta:

```powershell
python -m pip install -r requirements.txt
python -m nbconvert --execute --to notebook --inplace notebooks/Fase_1_Preparacion_EDA.ipynb
python -m nbconvert --execute --to notebook --inplace notebooks/Fase_2_Inferencia.ipynb
python -m nbconvert --execute --to notebook --inplace notebooks/Fase_3_Modelado.ipynb
```

También se pueden ejecutar las celdas desde un editor de notebooks. La Fase 1 descarga los originales que falten y comprueba sus huellas SHA-256. La Fase 2 recalcula las pruebas estadísticas. La Fase 3 reutiliza el modelo y los resultados registrados; para repetir la búsqueda completa, cambiar `REENTRENAR` a `True` en ese notebook. Puede tardar varios minutos y requiere varios GB de memoria. Repetir resultados ya conocidos no crea una prueba independiente nueva.

Para actualizar las versiones HTML después de editar los notebooks:

```powershell
python -m nbconvert --to html --output-dir output/html notebooks/*.ipynb
```

Para aplicar el modelo al ejemplo de entradas preparadas:

```powershell
python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida tmp/predicciones.csv
```

La carpeta de salida se crea automáticamente. No se debe pasar un CSV original sin preparar: el ejemplo contiene las 31 características que espera el modelo.

## Integrantes

Alan Alcaraz, Leandro Ferreira y Jorge Rios. **Falta completar los legajos en las carátulas.**

Los resultados corresponden a registros PRF; no prueban causas ni demuestran que el modelo funcionaría igual en Paraguay.

Fuente: [datos abiertos oficiales de PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf).
