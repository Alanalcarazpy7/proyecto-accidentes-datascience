# Gravedad de las víctimas de accidentes de tránsito en Brasil

Proyecto Integrador de **Data Science (Electiva), curso TQ**. Integrantes: **Leandro Ferreira, Jorge Rios y Alan Alcaraz**.


## Problema y objetivos

¿Qué características se asocian con el fallecimiento frente a lesiones no fatales en víctimas de PRF Brasil de 2017-2025, y qué desempeño alcanza su clasificación en enero-septiembre de 2026?

**Objetivos:** preparar datos verificables, explorar patrones, contrastar hipótesis y comparar modelos. Continuamos el tema de Paraguay usando registros individuales, porque las tablas agrupadas anteriores no permitían reunir suficientes características por víctima.

## Datos y desarrollo de las tres fases

Fuente: **Polícia Rodoviária Federal (PRF), carreteras federales de Brasil**. [Descargas oficiales](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf) y [diccionario](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes). Usamos personas y accidentes desde 2017, inicio del sistema BAT.

Base limpia: **821.689 participaciones reales** (754.098 de 2017-2025 y 67.591 de 2026), con **31 predictoras** entre 37 columnas. Las claves reales unen personas, accidentes y contexto vehicular sin expandir totales. No identifican personas únicas entre años.

| Fase y código | Qué se realiza |
|---|---|
| [1. Preparación y exploración](notebooks/Fase_1_Preparacion_EDA.ipynb) | Unión, limpieza, faltantes, estadísticas y gráficos. |
| [2. Inferencia](notebooks/Fase_2_Inferencia.ipynb) | Sexo, edad, motocicletas y noche: cuatro hipótesis, pruebas, intervalos y corrección de Holm. |
| [3. Modelado y evaluación](notebooks/Fase_3_Modelado.ipynb) | Comparación de familias, selección de LightGBM, calibración y análisis de errores. |

**Períodos:** 2017-2023, desarrollo; 2024 H1, calibración; 2024 H2, punto de decisión; 2025, comparación retrospectiva; enero-septiembre de 2026, evaluación posterior. Seleccionamos por AP de validación temporal. Excluimos IDs, gravedad, conteos de heridos/muertos y `causa_acidente` como predictores.

## Ejecución

Usar **Python 3.13**, desde la carpeta de este README. Semilla: **42**. Bibliotecas: Pandas, NumPy, SciPy, statsmodels, scikit-learn, LightGBM, Matplotlib, Seaborn y Jupyter; versiones en [requirements.txt](requirements.txt).

Ejecutar en orden y esperar que termine cada comando:

```powershell
# Dependencias: instalar la primera vez
python -m pip install -r requirements.txt

# Fases 1, 2 y 3: ejecutar y guardar sus resultados en los notebooks
python -m nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/Fase_1_Preparacion_EDA.ipynb
python -m nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/Fase_2_Inferencia.ipynb
python -m nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/Fase_3_Modelado.ipynb

# Aplicar el modelo guardado a 30 casos de ejemplo
python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida tmp/predicciones.csv
```

**Datos:** están incluidos el [dataset limpio](data/processed/victimas_limpias.parquet), el [modelo](output/modelo/modelo_final.joblib) y `output/modelado/`. La Fase 1 descarga los ZIP que falten en `data/raw/` y verifica sus SHA-256 según [data/fuentes.json](data/fuentes.json). Requiere internet; si PRF cambió un archivo, se necesita el ZIP del corte registrado. Las Fases 2 y 3 usan la base limpia incluida.

**Salida:** cada fase termina con `Writing ... .ipynb`. El último comando muestra 30 predicciones y guarda `tmp/predicciones.csv`; es una demostración, no la evaluación completa. La Fase 3 verifica el modelo guardado con **`REENTRENAR = False`**. Activarlo repite la búsqueda y reemplaza el modelo; no crea una nueva prueba independiente.

## Resultados y alcance

El ganador es **LightGBM con 31 entradas**. En las 67.591 víctimas de 2026 obtuvo:

| AUC | AP | F1 macro | Precisión de fallecidos | Recall de fallecidos |
|---:|---:|---:|---:|---:|
| 0,845 | 0,352 | 0,675 | 37,34 % | 42,36 % |

Detectó 1.953 fallecidos, omitió 2.657 y generó 3.277 falsas alarmas. Superó a la referencia de 24 entradas. Conserva las proporciones naturales, sin SMOTE ni duplicaciones; el desbalance exige evaluar más que exactitud.

Las cuatro hipótesis rechazan H0 tras Holm, con efectos de distinta magnitud. Son asociaciones, no causas. Clasificamos víctimas de accidentes registrados: **no predecimos quién se accidentará ni cuántos accidentes ocurrirán**. No está validado para uso clínico o para Paraguay.

Respaldo: `output/tables/`, `output/figures/` y `output/modelado/`. Para consultar sin ejecutar: notebooks con resultados y `output/html/`.
