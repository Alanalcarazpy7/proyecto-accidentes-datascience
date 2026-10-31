# Pronóstico mensual de siniestros de tránsito en Paraguay

Las tres fases están calculadas sobre 108 meses publicados por el INE con fuente Patrulla Caminera (Central e Interior, 2016–2024). Es un estudio de conteos mensuales; no reconstruye víctimas individuales.

## Qué leer primero

1. `output/reports/Fase_3_Modelado_y_Evaluacion.pdf`: comparación de entrenamiento, validación y prueba, con errores y límites.
2. `output/reports/Fase_1_Preparacion_y_EDA.pdf`: calidad, limpieza, diccionarios y diez gráficos interpretados.
3. `output/reports/Fase_2_Inferencia.pdf`: cuatro contrastes y su cautela temporal.
4. `output/reports/Informe_Integrador.pdf`: relato completo de las tres fases.
5. `output/reports/Comprension_del_problema.pdf`: pregunta, objetivos y alcance en tres páginas.

Los notebooks ejecutados están en `notebooks/`, y sus versiones legibles sin Jupyter en `output/html/`. Cada fase ejecuta funciones de `src/`; el código de extracción, inferencia y modelado se entrega completo.

## Resultado predictivo principal

La selección se fijó por validación temporal 2019–2022: SVR con `C=1`, `epsilon=15`, `gamma=scale`. En prueba 2024 obtuvo MAE **10,87**, RMSE **15,32**, MAPE **7,13%** y R² **−0,477**. La referencia estacional obtuvo MAE 36,58 y la media de los doce últimos meses, 28,58.

Mejorar referencias no equivale a explicar bien la variación mensual: el SVR predice aproximadamente 132–135 siniestros por mes, frente a 126–174 reales. El R² negativo se conserva y explica. Random Forest ajusta mucho más el entrenamiento pero generaliza peor. Ridge consigue un MAE de prueba ligeramente menor; no se cambia a ese modelo porque sería elegir después de mirar prueba.

## Diseño y límites

- Desarrollo: 2016–2022, 84 meses. Exploración, inferencia y cuatro cortes de validación a doce pasos.
- Calibración: 2023, doce meses. Banda empírica posterior a fijar la selección; no se usa para elegir hiperparámetros.
- Prueba: 2024, doce meses emitidos desde diciembre de 2023. No se alimenta la recursión con sus resultados reales.
- Reajuste final: 2016–2024, para una **proyección retrospectiva de 2025 con corte 2024**. No es un pronóstico actualizado de 2027 ni está evaluado con 2025 real.

La banda de incertidumbre es orientativa y no tiene cobertura temporal garantizada. No se publica un intervalo anual formal con un único año de calibración. La estabilidad de cobertura institucional debe documentarse mejor; no se representan todos los accidentes de Paraguay ni el riesgo por viaje.

## Reproducción

Se probó el análisis con Python 3.13. Las versiones exactas están en `requirements.txt` y `output/entorno.json`. Usar un entorno virtual evita alterar otras instalaciones.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/run_all.py
```

Los siete XLSX originales están incluidos y ocupan menos de 25 MB; no se necesita red para repetir el análisis. `src/download_data.py` permite restaurarlos desde sus URL oficiales y exige que coincida el hash de la versión estudiada. Si el organismo revisa un archivo, el script detiene el reemplazo y exige documentar la nueva versión.

Para ejecutar solo las etapas analíticas:

```powershell
python src/data_prep.py
python src/phase1.py
python src/phase2.py
python src/phase3.py
```

`phase3.py` reutiliza el resultado si los datos y el protocolo coinciden, evitando repetir la selección durante la lectura de notebooks. Al eliminar los resultados y ejecutar en una copia limpia, reconstruye el experimento completo con la misma grilla. Una repetición no convierte 2024 en una nueva prueba no consultada.

Para generar solo PDF con otro intérprete que tenga reportlab, usar `--pdf-python RUTA_PYTHON` en `run_all.py`. Para omitir formatos opcionalmente al comprobar el cálculo, se admiten `--sin-notebooks` y `--sin-pdf`.

## Modelo guardado e inferencia

`output/models/modelo_evaluado_2024.joblib` conserva el ajuste evaluado. `modelo_pronostico.joblib` conserva la misma especificación reajustada con todo el historial.

```powershell
python src/inference.py --meses 12
python src/inference.py --historial nuevo_historial.csv --meses 12 --salida output/tables/nuevo_pronostico.csv
```

El CSV nuevo debe incluir `fecha` (primer día de cada mes) y `accidentes`, con al menos 36 meses consecutivos, conteos enteros no negativos y sin meses duplicados. Se reajusta la especificación ya elegida, sin volver a seleccionar hiperparámetros. Debe comprobarse que el nuevo historial represente el mismo universo.

## Organización

| Carpeta | Contenido |
|---|---|
| `data/raw` | Siete originales XLSX, catálogo de URL y hashes |
| `data/processed` | CSV mensual limpio y desarrollo separado |
| `src` | Extracción, tres fases, informes, notebooks, inferencia y verificación |
| `notebooks` | Tres notebooks ejecutados y explicados |
| `output/tables` | Auditorías, diccionarios, contrastes, búsquedas y predicciones |
| `output/figures` | Diez figuras F1, cuatro F2 y siete F3 |
| `output/reports` | Cinco informes PDF |
| `output/models` | Modelo evaluado y reajuste de producción |
| `output/html` | Tres exportaciones HTML de los notebooks |

## Consigna e integridad académica

Se siguió la estructura del documento `Proyecto_DataScience_Tres_Fases (1).pdf`: fases acumulativas, cuatro contrastes y varias familias, modelos lineales y de árboles, referencias, validación temporal, métricas de regresión, interpretación y reproducibilidad. El cambio al pronóstico se basa en la autorización comunicada por el usuario; no se afirma una aprobación docente adicional que no se recibió.

El material fue preparado con asistencia de IA para proponer metodología, escribir y ejecutar código, calcular resultados, generar gráficos y redactar borradores. **La consigna reserva al grupo las decisiones metodológicas y la interpretación.** Sus integrantes deben revisar y comprender este trabajo y asumir o ajustar sus decisiones antes de entregarlo. El historial local del repositorio registra la preparación asistida; no simula contribuciones de los integrantes.

Nombres confirmados: Alan Alcaraz, Leandro Ferreira y Jorge Rios. **Faltan los legajos**, que no se inventaron. La publicación, el envío a la cátedra y la defensa oral corresponden al grupo.

## Fuentes

- INE: https://www.ine.gov.py/tabulado/16/anuario
- URL y SHA-256 de cada original: `data/raw/catalogo_fuentes.json` y `output/tables/inventario_fuentes.csv`.
- Hyndman y Athanasopoulos, *Forecasting: Principles and Practice*, capítulo 5: https://otexts.com/fpp3/toolbox.html
- statsmodels: https://www.statsmodels.org/stable/
- scikit-learn: https://scikit-learn.org/stable/

No se copió una licencia específica que no figure en los originales. Se conserva la atribución de las publicaciones institucionales.
