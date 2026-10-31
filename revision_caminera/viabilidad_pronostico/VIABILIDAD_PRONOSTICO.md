# Viabilidad de un proyecto de pronóstico de siniestros de tránsito

**Recomendación: mantener Paraguay y reformular el proyecto para pronosticar cantidades mensuales, ampliando los PDF con los cuadros oficiales del INE.** Se verificó una serie candidata de enero de 2016 a diciembre de 2024, con 108 meses consecutivos. Es suficiente para plantear una comparación académica de modelos parsimoniosos; todavía no demuestra que alguno vaya a pronosticar bien.

La recomendación anterior de no usar estos PDF para clasificación individual sigue siendo válida. Cambiar la variable objetivo cambia la unidad de análisis: para pronosticar cantidades mensuales, una fila por mes es una observación real del fenómeno agregado. No hace falta inventar personas ni reconstruir accidentes individuales.

Revisión: 31/10/2026. Los informes anteriores del grupo se usaron solamente como contexto; no sustituyen la consigna original de la profesora. No se entrenaron modelos ni se emitieron predicciones durante esta evaluación de fuentes.

## 1. Pregunta de investigación propuesta

**¿Con qué precisión se puede pronosticar la cantidad mensual de siniestros registrados por la Patrulla Caminera en zona Central e Interior durante los siguientes doce meses, utilizando su historial y variables de calendario, y qué modelo mejora un pronóstico estacional sencillo?**

Producto final: doce pronósticos mensuales, un total anual obtenido sumándolos y una medida de incertidumbre. El alcance se refiere a los registros de la institución; no equivale a todos los accidentes ocurridos en Paraguay, incluidos los no registrados o atendidos exclusivamente por otras instituciones.

Un título posible es: **Pronóstico mensual de siniestros de tránsito registrados por la Patrulla Caminera en Paraguay: comparación de modelos con datos de 2016–2024**.

## 2. Qué se verificó realmente

Se descargaron diez archivos XLSX del INE y un ZIP de muestra de la PRF de Brasil. Son originales publicados por sus organismos; no se modificaron sus hojas. Las URL, tamaños y hashes se conservan en [fuentes_descargadas.json](fuentes_descargadas.json).

El [catálogo oficial del INE](https://www.ine.gov.py/tabulado/16/anuario) permite descargar los cuadros por año. Se leyeron las hojas de tipología de accidentes de las ediciones 2017, 2018, 2019, 2021, 2022, 2023 y 2024. Cubren conjuntamente 2016–2024 y citan a la Patrulla Caminera del MOPC como fuente. La columna C contiene el total de accidentes de cada mes y D:J siete tipos de accidente.

| Año | Meses disponibles en la serie candidata | Siniestros publicados, suma mensual |
|---|---:|---:|
| 2016 | 12 | 2.085 |
| 2017 | 12 | 1.933 |
| 2018 | 12 | 1.518 |
| 2019 | 12 | 1.570 |
| 2020 | 12 | 1.269 |
| 2021 | 12 | 1.942 |
| 2022 | 12 | 1.605 |
| 2023 | 12 | 1.366 |
| 2024 | 12 | 1.709 |
| **Total** | **108** | **14.997** |

Los 14.997 son la suma de siniestros representados en los cuadros, no 14.997 fichas descargadas. El tamaño de la serie para modelar el total mensual es 108 observaciones.

Comprobaciones realizadas:

- Se encontraron exactamente los 108 períodos esperados, sin meses faltantes ni repetidos en la tabla seleccionada.
- Los 84 totales mensuales de 2016–2022 extraídos de los PDF por horas coinciden con los totales de los cuadros INE.
- Los conteos mensuales de las ediciones INE que se solapan coinciden, incluidos sus siete tipos de accidente.
- La suma de los doce meses coincide con cada total anual publicado revisado.
- La suma de los siete tipos coincide con el total de cada mes.
- Los doce totales mensuales del cuadro INE de tipología de 2024 también coinciden con el cuadro por horas de 2024.

Esto verifica coherencia aritmética y coincidencia entre estas publicaciones. No prueba por sí mismo que la cobertura, el esfuerzo de registro o las definiciones institucionales se hayan mantenido idénticos durante nueve años. Ese punto debe documentarse en la Fase 1 y reflejarse en las limitaciones.

La serie está en [serie_mensual_candidata_2016_2024.json](serie_mensual_candidata_2016_2024.json). Cada observación conserva el archivo, hoja y celda de origen y las ediciones alternativas coincidentes. [preparar_serie_candidata.py](preparar_serie_candidata.py) reproduce la extracción desde los XLSX originales usando Python y openpyxl, sin escribir en ellos.

## 3. Qué aportan los archivos que ya tenías

Los PDF permiten reunir 84 meses de 2016–2022. Para el nuevo objetivo, esa estructura sí tiene sentido: fecha mensual y cantidad de siniestros. No conviene reducirlos a siete totales anuales, porque quedarían muy pocas observaciones para comparar modelos y estudiar patrones dentro del año.

Los cuadros históricos que comienzan en 2010 no garantizan disponibilidad mensual desde 2010 para todos los siniestros: varios contienen totales anuales por día u horario. Tampoco debe confundirse el histórico de accidentes de motociclistas con el de víctimas de motociclistas. El cuadro INE 12.2.11 de 2024 descargado mide víctimas, un objetivo distinto al número de accidentes.

Los PDF de 2023 que tenías eran parciales y no concordaban entre sí. Se recomienda utilizar los cuadros anuales posteriores del INE para la serie candidata y conservar los PDF parciales como versiones documentadas. El valor 1.605 de 2022 aparece también en dos ediciones posteriores del INE, aunque el PDF local por horas advertía provisionalidad. Esto respalda usar ese valor publicado en la serie, sin prometer que nunca pueda revisarse.

## 4. Comparación de fuentes para este objetivo

| Opción | Datos verificados | Aporte para pronóstico | Límites y decisión |
|---|---|---|---|
| Solo los PDF locales | 84 totales mensuales de todos los siniestros, 2016–2022; 2023 local parcial. | Permiten un primer diseño temporal. | Serie más corta y desactualizada; no es la primera opción si podemos ampliarla. |
| **Caminera + INE, Paraguay** | **108 meses, 2016–2024**, con totales y siete tipos. Descargas XLSX verificadas. | Mantiene el país y aporta nueve ciclos anuales para modelos sencillos y validación temporal. | Pocas observaciones para modelos complejos. Comparabilidad institucional aún requiere documentación. **Opción recomendada por prioridad geográfica.** |
| **PRF, Brasil** | Portal histórico desde 2007. Se descargó el ZIP 2025 por ocurrencia: **72.529 filas, 72.529 ID únicos y 30 columnas**, del 01/01/2025 al 31/12/2025. | Permite construir series diarias, semanales o mensuales y estudiar estado o carretera. Más flexible para un proyecto con mayor detalle. | Solamente se perfiló 2025; no se contaron todavía todos los años. El diccionario oficial distingue BR-Brasil 2007–2016 y BAT desde 2017; conviene empezar evaluando 2017–2025 y revisar cambios de cobertura. **Mejor alternativa si se prioriza granularidad sobre Paraguay.** |
| STATS19, Gran Bretaña | Portal oficial con histórico 1979–2025. Se verificó descarga de 8.192 bytes de la tabla de colisiones 2025: cabecera con 44 campos, incluido collision_index, fecha y hora. | Posibilita series por fecha y área; también dispone de tablas de vehículos y víctimas. | Solo se verificó una muestra de la tabla de colisiones, no el total de filas ni sus uniones. Se refiere a colisiones con lesiones en vías públicas notificadas a la policía; su definición difiere de un total con daños materiales. |
| ANTSV / SIAT | El observatorio enlaza informe anual 2025 y primer semestre 2026. | Podrían actualizar Paraguay y ayudar a documentar cobertura. | Los enlaces de descarga devolvieron HTTP 403 en esta revisión; no se verificaron sus tablas. No se supone que incluyan microdatos ni que continúen automáticamente la serie Caminera. |

Fuentes oficiales: [INE](https://www.ine.gov.py/tabulado/16/anuario), [PRF: descargas](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf), [PRF: diccionario y cambio de sistemas](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes), [STATS19](https://www.gov.uk/government/statistical-data-sets/road-safety-open-data), [Observatorio ANTSV](https://antsv.gov.py/observatorio-vial/).

En PRF, el término portugués «agrupados por ocorrência» corresponde en la muestra a una fila por accidente identificado; no es un cuadro de totales por edad o sexo. Para contar accidentes se debe usar el identificador de ocurrencia y comprobar su unicidad. Contar filas de una tabla por personas o por todas las causas podría contar varias veces el mismo accidente.

Aunque PRF y STATS19 tengan variables como clima, causa o estado de la calzada de cada accidente, sus valores observados en un mes futuro no se conocen al emitir un pronóstico. No deben usarse como predictores contemporáneos de ese mes en una evaluación supuestamente anticipada. Sirven para describir el historial o para construir variables rezagadas y escenarios justificados.

## 5. Diseño propuesto para las tres fases

### Fase 1: construir y entender una serie mensual

Preparar una fila por año-mes, con cantidad de siniestros, fuente y alcance. Conservar los originales. Documentar duplicados, versiones, definiciones y meses sin cobertura. Revisar la evolución temporal, los cambios de nivel, los patrones mensuales y el episodio de 2020. Un cambio observado no demuestra una causa específica.

Se pueden añadir variables derivadas útiles: mes del año, días del mes, cantidades previas de accidentes y medias de meses anteriores. Para un modelo con rezago de doce meses quedarían como máximo 96 filas utilizables de la serie de 108, antes de separar entrenamiento y evaluación.

No sumar columnas que son partes del total para intentar predecir ese mismo total del mismo mes: eso filtraría la respuesta. Las siete clases de accidente son resultados registrados, no siete causas externas independientes conocidas de antemano.

### Fase 2: hipótesis coherentes con el tiempo

Preguntas posibles: si hay diferencias sistemáticas entre meses del calendario, si existen cambios de nivel entre períodos y si las cantidades de meses previos aportan información. Los métodos concretos deben elegirse después de revisar distribución, tendencia y autocorrelación; no aplicar pruebas de independencia automáticamente a meses consecutivos. El tamaño de un conteo tampoco mide riesgo por viaje sin un denominador de exposición.

Es posible tener un proyecto universitario sólido sin encontrar significación en todas las hipótesis ni lograr que un modelo complejo supere al sencillo. El valor está en una pregunta bien delimitada, la evaluación y la explicación de los resultados.

### Fase 3: comparar pronósticos para doce meses

Comparación inicial propuesta:

1. **Referencia estacional:** para cada mes pronosticar la cantidad del mismo mes del año anterior. Es una referencia que los demás modelos deben intentar mejorar.
2. **Suavizado exponencial o SARIMA:** modelos clásicos de series temporales, con complejidad limitada por el número de períodos.
3. **Modelo de regresión o Machine Learning sencillo:** por ejemplo, regresión regularizada o un bosque de poca complejidad, utilizando calendario e historia disponible. Su rendimiento debe demostrarse, no asumirse.

Un diseño posible reserva 2024 para la evaluación final y usa cortes cronológicos anteriores para comparar y ajustar modelos: por ejemplo, entrenar hasta diciembre de 2021 para pronosticar 2022 y entrenar hasta diciembre de 2022 para pronosticar 2023. Se pueden incorporar más cortes anteriores si hay suficiente historial, sin confundirlos con experimentos independientes.

La evaluación debe simular el objetivo real: pronosticar los doce meses desde un mismo origen, sin ir suministrando los resultados reales de los meses intermedios. Si se necesitan rezagos de meses que todavía no ocurrieron, se usan predicciones recursivas o un diseño directo por horizonte. Otra evaluación con actualización mensual es válida, pero responde una pregunta operativa diferente.

Usar MAE, RMSE y una medida relativa a la referencia, además del error del total anual. No usar accuracy, F1 o matriz de confusión para una cantidad numérica. Informar incertidumbre: para el total anual debe considerarse la dependencia entre los errores de los doce meses, no sumar desviaciones estándar como si fueran independientes.

Referencia metodológica: [Forecasting: Principles and Practice, capítulo 5](https://otexts.com/fpp3/toolbox.html), métodos de referencia, evaluación y validación temporal. Este diseño es una propuesta, no una selección definitiva de algoritmos ni un resultado experimental.

## 6. Qué significa «el próximo año»

A fecha de esta revisión, el próximo año calendario es 2027. La serie verificada termina en diciembre de 2024: un pronóstico de enero–diciembre de 2027 desde ese corte tiene horizontes de 25 a 36 meses, no de uno a doce. No conviene presentarlo como si utilizara datos cerrados de 2026.

Hay dos caminos defendibles:

- **Ejercicio académico histórico:** evaluar pronósticos a doce meses en años observados; por ejemplo, usar 2024 como evaluación final después de escoger el modelo con años anteriores. Después se puede mostrar un pronóstico para los doce meses posteriores al último dato, etiquetando claramente su fecha de origen.
- **Pronóstico operativo de 2027:** conseguir primero una continuación comparable de 2025 y los meses disponibles de 2026; completar 2026 o especificar explícitamente cómo se pronostican sus meses pendientes. La disponibilidad de un informe reciente no basta si su universo es distinto.

## 7. Decisión y próximos pasos

Recomiendo usar la serie mensual ampliada de Paraguay para reformular la investigación, siempre que la consigna permita regresión/pronóstico y que se documenten sus límites. Con 108 meses se puede hacer una comparación modesta y bien evaluada; no se justifica prometer redes neuronales profundas ni muchos predictores sin información adicional.

Si se decide que hacen falta series diarias o semanales, análisis por territorio o carretera y una base más rica para extender el proyecto, la alternativa preferida es PRF. Antes de adoptarla habría que descargar y perfilar los demás años, verificar cambios de registro y delimitar el territorio. No se deben unir los conteos de Brasil con los de Paraguay para fabricar una sola serie.

El trabajo inmediato para la siguiente etapa es fijar la pregunta y horizonte, revisar la rúbrica de la profesora, exportar la serie elegida a un formato de trabajo y documentar las variables utilizables en la fecha de cada pronóstico. Luego corresponde desarrollar las fases, con los modelos y métricas adecuados al nuevo objetivo.

## Archivos de esta revisión

- `fuentes/`: diez XLSX originales del INE y ZIP de muestra de PRF 2025.
- [Serie mensual candidata y procedencia por celda](serie_mensual_candidata_2016_2024.json).
- [Gráfico de datos observados](serie_mensual_2016_2024.png).
- [Contraste de 84 meses entre los PDF y el INE](contraste_pdf_ine.json).
- [Perfil de la muestra completa de PRF 2025](perfil_prf2025.json).
- [Cabecera de la muestra de STATS19](muestra_stats19_2025.json).

Los archivos son evidencia de selección y preparación inicial. No constituyen las tres fases terminadas ni una evaluación de rendimiento predictivo.
