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

## Archivos de la entrega

| Carpeta o archivo | Para qué sirve |
|---|---|
| `notebooks/` | Los tres notebooks ejecutados, uno por fase. |
| `output/html/` | Los mismos notebooks en un formato que se puede abrir en el navegador. |
| `src/fase1.py`, `src/preparar.py` | Limpieza, unión y análisis de los datos. |
| `src/fase2.py` | Las cuatro pruebas estadísticas. |
| `src/comparacion.py`, `src/modelado.py`, `src/graficos.py` | Comparación de familias, entrenamiento final y evaluación. |
| `src/inferencia.py` | Aplicación del modelo a nuevas filas con las características ya preparadas. |
| Otros módulos de `src/` | Descarga, reproducción, textos, informes, verificación y creación del ZIP. |
| `data/processed/victimas_limpias.parquet` | El único dataset limpio: 821.689 participaciones reales, con los períodos identificados. |
| `data/raw/`, `data/fuentes.json` | Originales locales y sus enlaces/huellas de verificación. Los originales pesados no se incluyen en el ZIP. |
| `data/metodologia/`, `protocolo.json` | Decisiones y registros originales de la selección del modelo. |
| `output/reports/` | Los informes PDF. |
| `output/tables/`, `output/figures/` | Diccionarios original/final, bitácora, tablas y gráficos que respaldan las tres fases. |
| `output/modelado/` | Resultados de comparación y validación que permiten justificar la elección. |
| `output/modelo/modelo_final.joblib` | El único modelo principal guardado. |
| `requirements.txt` | Versiones de las bibliotecas utilizadas. |
| `dist/` | Un ZIP acumulativo listo para la entrega de las tres fases. |

Las comparaciones iniciales se conservan porque la cátedra exige varias familias de modelos. No son otras opciones de proyecto para estudiar o entregar.

## Cómo reproducirlo

Usamos Python 3.13 y semilla 42. Desde esta carpeta:

```powershell
python -m pip install -r requirements.txt
python src/descargar_fuentes.py
python src/reproducir.py
python src/notebooks.py
python src/informes.py
python src/verificar.py
python src/empaquetar.py
```

La descarga solo es necesaria si faltan los originales. El programa comprueba sus huellas SHA-256 para detectar cambios de la fuente. `reproducir.py` reconstruye datos y análisis y reutiliza los resultados de entrenamiento registrados. Para volver a entrenar todas las comparaciones, usar `python src/reproducir.py --reentrenar`; puede tardar varios minutos y requiere varios GB de memoria. Repetir resultados ya conocidos no crea una prueba independiente nueva.

Para aplicar el modelo al ejemplo de entradas preparadas:

```powershell
python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida tmp/predicciones.csv
```

Crear la carpeta de salida si hace falta. No se debe pasar un CSV original sin preparar: el ejemplo contiene las 31 características que espera el modelo.

## Integrantes y revisión final

Alan Alcaraz, Leandro Ferreira y Jorge Rios. **Falta completar los legajos en las carátulas.** El grupo debe revisar y comprender los resultados antes de presentar y preparar la exposición oral y sus diapositivas. No se inventan contribuciones individuales ni aprobación docente.

Se utilizaron herramientas de IA como apoyo en programación, análisis y redacción. Los resultados corresponden a registros PRF; no prueban causas ni validan una herramienta médica o su aplicación automática a Paraguay.

Fuente: [datos abiertos oficiales de PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf).
