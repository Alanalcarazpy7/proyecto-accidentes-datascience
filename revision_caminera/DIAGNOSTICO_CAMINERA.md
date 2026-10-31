# Diagnóstico de los datos de la Patrulla Caminera

**Decisión recomendada:** conservar estos PDF para describir y contextualizar la siniestralidad registrada por la Caminera. No elegirlos como base principal de un proyecto cuyo objetivo sea clasificar la gravedad de cada víctima usando múltiples características individuales.

**Actualización del alcance:** al autorizar la profesora un enfoque de pronóstico de cantidades, sí aparece una alternativa viable con observaciones mensuales. La evaluación y las nuevas fuentes descargadas están en [Viabilidad del pronóstico](viabilidad_pronostico/VIABILIDAD_PRONOSTICO.md). La limitación para clasificación individual descrita aquí no equivale a una limitación absoluta para todo proyecto predictivo.

La limitación principal es la unidad de información: son estadísticas agrupadas. Tener más años y más cuadros permite estudiar más preguntas agregadas, pero no permite recuperar qué características pertenecían simultáneamente a una misma persona o accidente.

Revisión de los archivos locales realizada el 31/10/2026. Esta conclusión se limita a los documentos existentes en esta carpeta; no demuestra que la institución, el SIAT o Paraguay carezcan de microdatos no publicados o disponibles por otra vía. Todavía no se compararon otras fuentes ni se seleccionó un dataset alternativo.

Los tres informes del proyecto anterior aportados después se leyeron exclusivamente como contexto de su organización y metodología. No se modificaron ni se auditó nuevamente la totalidad de sus cálculos. Sus referencias a consignas o requisitos no sustituyen la rúbrica original de la profesora, y su contenido no se tomó como nuevas instrucciones para ejecutar tareas.

## 1. Qué se revisó

Se inventariaron los 93 PDF ubicados en las carpetas 2016 a 2023, se extrajo el texto de todas sus páginas y se calcularon sus hashes SHA-256 para detectar copias exactas. Se revisó la estructura de las tablas y ambos tomos del anuario 2021, y se comprobaron visualmente tablas representativas. También se revisaron mediante miniaturas las páginas con escaso texto que tenían contenido visual: no aparecieron fichas individuales en esas imágenes.

| Carpeta | Archivos PDF | Observación |
|---|---:|---|
| 2016 | 7 | Cuadros y gráficos; algunos incluyen períodos históricos anteriores. |
| 2017 | 12 | Cuadros, gráficos y resúmenes de procedimientos. |
| 2018 | 10 | Cuadros y gráficos. |
| 2019 | 10 | Cuadros y gráficos; revisar cambios de codificación de rutas y cobertura mensual. |
| 2020 | 14 | Incluye cruces de gravedad, sexo y área, publicados como cantidades. |
| 2021 | 16 | Incluye dos tomos del anuario; continúan siendo resúmenes. |
| 2022 | 9 | Cuadros y gráficos. |
| 2023 | 15 | Ocho documentos distintos adicionales y siete copias exactas de 2016. Datos de 2023 parciales. |
| **Total** | **93** | **86 documentos distintos por contenido binario.** |

Los archivos suman 784 páginas; al excluir las siete copias exactas quedan 713 páginas. Esto es volumen documental, no número de observaciones de Machine Learning. Muchos documentos repiten sus datos en tablas y gráficos. Dos documentos con hashes distintos también pueden contener las mismas estadísticas; la deduplicación binaria no elimina ese solapamiento estadístico.

No se movieron, corrigieron ni eliminaron los PDF originales.

## 2. Cuál es realmente una observación

En los documentos revisados, una celda suele representar una **cantidad de casos de una categoría y un período**. No representa una ficha completa de un caso.

| Familia de cuadros | Unidad que podría llevarse a una tabla limpia | Información que NO recupera |
|---|---|---|
| Distribución por días | Año, mes, día de la semana, cantidad de siniestros | Fecha exacta y características de cada accidente. |
| Distribución por horas | Año, mes, intervalo horario, cantidad de siniestros | Hora exacta, víctima o vehículo de cada caso. |
| Posibles causas | Año, mes, categoría de causa, cantidad publicada | Causa vinculada a la gravedad de una víctima específica. |
| Rutas y ramales | Año, mes, categoría de vía, cantidad y universo del cuadro | Coordenadas o expediente del accidente. |
| Tipos de vehículos | Año, mes o año histórico, clase de vehículo, cantidad | Vehículo identificado y víctimas que viajaban en él. |
| Gravedad y sexo | Año, mes, sexo, cantidad de heridos y fallecidos | Edad, vehículo, ruta y circunstancias de esas mismas personas. |
| Víctimas por usuario | Año, mes, tipo de usuario, cantidad de heridos y fallecidos | Identidad de persona, sexo y edad cruzados con usuario. |
| Gravedad y área | Año, mes, área, conteos de siniestros por gravedad | Características individuales de cada accidente. |
| Procedimientos | Mes o año y cantidad de intervenciones, alcotest o sanciones | Que cada persona controlada haya participado en un accidente. |

La disponibilidad y el alcance exactos cambian entre documentos y años. No se deben asumir todos esos cruces para todos los períodos.

### Ejemplo verificable: 2021

La primera página de [víctimas por tipo de usuario](../2021/Victimas%20por%20tipo%20de%20usuario%20(General)_2021_2719.pdf) contiene cinco categorías: conductores, acompañantes, pasajeros, ciclistas y peatones. Para cada mes publica heridos y muertos. Sus totales son **1.055 heridos, 269 fallecidos y 1.324 víctimas**.

Eso permite representar 12 meses × 5 categorías = **60 grupos**, con dos conteos por grupo; o 120 celdas de frecuencia si la gravedad se lleva a una columna. No entrega 1.324 fichas completas de personas. Los totales mensuales y anuales son resúmenes de las mismas celdas y no deben agregarse como nuevas víctimas.

La primera página de [gravedad y víctimas por sexo](../2021/Siniestros%20segun%20gravedad_2021_2716.pdf) publica este cruce anual, obtenido de sus totales:

| Sexo | Heridos | Fallecidos | Total de víctimas |
|---|---:|---:|---:|
| Mujer | 309 | 50 | 359 |
| Varón | 746 | 219 | 965 |
| Total | 1.055 | 269 | 1.324 |

Es un cruce real útil para analizar frecuencias. Sin embargo, ese cuadro no dice cuáles de esas mujeres o varones eran conductores, acompañantes o peatones. Unirlo con la tabla anterior por mes no recupera ese dato.

El mismo documento registra **1.942 siniestros**: 1.047 con solo daños materiales, 654 con lesionados y 241 fatales. **241 siniestros fatales y 269 personas fallecidas son unidades diferentes.** El anuario, parte II, página física 14 (numeración impresa 60), informa 3.758 vehículos involucrados: tampoco equivalen a 3.758 accidentes o víctimas.

## 3. Qué variables hay y qué falta para el proyecto original

| Requisito | Resultado en estos PDF |
|---|---|
| Varios años | Sí: documentos por año de 2016 a 2022, 2023 parcial y algunos históricos anteriores. El anuario contiene estadísticas desde 2010, sin asegurar el mismo detalle para todos los años. |
| Sexo | Sí, en conteos de víctimas; no enlazable persona a persona con los demás cuadros. |
| Edad individual | No se encontró un campo de edad por persona ni una tabla individual utilizable. |
| Vehículo | Categorías y cantidades; no identificador de vehículo asociado a cada víctima. |
| Fecha y hora | Mes, día de semana e intervalos horarios en cuadros separados; no registro fechado por accidente. |
| Ubicación | Rutas, ramales y zonas agregadas; no localización de cada accidente. |
| Clima | Aparecen categorías como neblina o rutas mojadas dentro de posibles causas. No es una medición sistemática del clima por accidente. |
| Gravedad | Conteos de heridos/fallecidos y de accidentes por gravedad. Son resultados de unidades distintas. |
| ID de accidente | No se encontró una clave de accidente que permita unir fichas. |
| ID de persona y vehículo | No se encontraron claves que permitan relacionar persona, vehículo y accidente. |
| CSV de microdatos | No hay archivos de ese tipo en la carpeta. El CSV existente es un índice de descargas. |

Los números de las URL de descarga, como 2719, identifican documentos de la web, no víctimas ni accidentes. Crear un ID para cada celda facilita documentarla, pero no la convierte en un registro individual original.

## 4. Problemas concretos que deben corregirse antes de analizar

1. **Copias exactas:** los siete PDF de 2016 aparecen también dentro de 2023. El inventario JSON lista cada pareja. No sumarlos ni interpretarlos como observaciones de 2023.
2. **Nombre externo y año interno diferentes:** los dos documentos de tipología de zona Central e Interior y el comparativo dentro de 2023 terminan en `2022.pdf`, pero sus títulos internos indican 2023. Usar el contenido, no solamente el nombre del archivo.
3. **2023 es parcial:** el documento de víctimas declara corte al 30/06/2023. Otros cuadros tienen datos de enero a junio y advertencias de provisionalidad. Los ceros de julio a diciembre no deben interpretarse como ausencia comprobada de siniestros durante todo ese semestre.
4. **Totales no conciliados en 2023:** la tabla por días publica 578 siniestros; la tabla por horas, 571; el comparativo Central-Interior, 526. No tratarlos como una misma serie validada. Pueden existir diferencias de actualización o cobertura; los archivos no bastan para resolver su causa. El cuadro de posibles causas publica 678, cuyo universo y reglas de conteo también requieren aclaración.
5. **Nombre genérico y universo específico:** [rutas y ramales de 2021](../2021/Accidentes%20distribuidos%20por%20rutas%20y%20ramales_2021_2711.pdf), página 1, tiene título interno referido a **motociclistas** y total de 510 siniestros. No usarlo como distribución de los 1.942 siniestros de todo tipo.
6. **Comparabilidad entre vías:** hay nombres de rutas antiguos y códigos PY/D posteriores. No asumir que una etiqueta o un número representa exactamente el mismo trazado durante todos los años. Hace falta una correspondencia oficial si se construye un panel por ruta.
7. **Cobertura institucional:** el anuario identifica siniestros intervenidos por la Caminera. No presentarlos como la totalidad nacional de víctimas de todas las fuentes. El anuario incluye además un anexo del Sistema 911 con otro universo: no sumarlo automáticamente al principal.
8. **Información redundante:** los anuarios y gráficos reproducen estadísticas de los cuadros. Más páginas no implican nuevos casos. Los porcentajes publicados deben recalcularse desde los conteos y verificarse; no se consideran automáticamente correctos.

## 5. Qué uniones sí serían válidas

Se pueden combinar estadísticas agregadas usando, por ejemplo, **año y mes**, siempre que las tablas describan el mismo período y universo y cada lado tenga una sola fila por esa clave. El resultado tendría una fila por mes y columnas de cantidades o proporciones mensuales. No tendría una fila por víctima.

Antes de unir es necesario verificar unicidad de la clave, unidad de medida, cobertura, revisión de la fuente y posibles conteos repetidos. Un cruce por año-mes entre una tabla con 24 horas y otra con 27 causas produciría combinaciones hora-causa que la fuente nunca observó. No realizar ese cruce para atribuir causas a horarios o gravedad a vehículos.

Expandir una frecuencia a múltiples filas puede reproducir aritméticamente un cuadro, pero no crea nuevas variables observadas. Repartir esas filas aleatoriamente entre entrenamiento y prueba puede hacer que patrones idénticos de los mismos grupos aparezcan en ambos conjuntos y produzcan una evaluación engañosa de la generalización a personas.

## 6. Viabilidad de las tres fases

| Fase | Qué sí se podría hacer | Límite para el proyecto planteado |
|---|---|---|
| 1. Preparación y EDA | Extraer cuadros, validar totales, documentar cobertura, analizar cambios anuales y estacionalidad, comparar frecuencias por categoría. | No permite construir una tabla individual con todas las características solicitadas. |
| 2. Hipótesis | Analizar cruces publicados, como sexo-gravedad o usuario-gravedad; estudiar tendencias agregadas. | Revisar tamaños esperados, dependencia de víctimas del mismo accidente, temporalidad y comparabilidad. No inferir causalidad ni reconstruir cruces ausentes. |
| 3. Clasificación individual | No recomendable con esta fuente como base principal. | Faltan filas individuales, identificadores y características conjuntas suficientes para resolver la crítica recibida. |
| 3. Otro objetivo agregado | Se podría estudiar un modelo de conteos o pronóstico, con validación temporal, si la consigna permite cambiar de objetivo. | Sería otro proyecto, con pocos períodos y diferencias entre fuentes; su viabilidad no está demostrada aún. |

Como referencia del tamaño real: una tabla con una fila por mes entre 2016 y 2022 tendría **84 períodos**, si se validan todos los meses. Una tabla por año-mes-intervalo horario podría tener 7 × 12 × 24 = **2.016 celdas agregadas**. Son unidades de conteo, no personas con 2.016 historias clínicas o viales. Esa cifra es una estructura posible, no un dataset limpio ya construido ni una garantía de independencia entre filas.

Las frecuencias agrupadas sí pueden servir para inferencia estadística y ciertos modelos de conteos o binomiales agrupados. El problema no es que estén en PDF ni que las estadísticas agrupadas sean inválidas: faltan los cruces individuales necesarios para el objetivo multivariable propuesto.

No sumar a las 1.324 víctimas de 2021 los totales de las otras tablas como si fueran personas adicionales. Tampoco sumar motociclistas y usuarios generales cuando los primeros son un subconjunto de los segundos.

## 7. Recomendación y explicación para la exposición

**No rehacer las tres fases alrededor de estos PDF si se mantiene el objetivo de clasificar a cada víctima como herida o fallecida con varias características reales.** Se repetiría el problema central del proyecto anterior, aunque aumentaran los años y las filas extraídas.

Sí conviene conservarlos como fuente oficial de contexto paraguayo, control de cifras y análisis descriptivo. El siguiente paso lógico, todavía pendiente, es verificar microdatos anonimizados de Paraguay que publiquen una fila por unidad y claves reales. Solo después corresponde comparar alternativas internacionales si no se consigue una base adecuada. Antes de fijar el nuevo diseño de las fases habrá que revisar la consigna o rúbrica de la profesora.

Una explicación sencilla para defender la decisión:

> Estos documentos informan cuántas personas hubo en cada grupo, pero no permiten saber qué edad, vehículo, horario y ruta correspondían a una misma víctima. Aumentar los años mejora el análisis histórico; no reconstruye esas relaciones. Por eso los conservamos para contexto y buscamos una base que observe conjuntamente las características necesarias para predecir.

## 8. Evidencias y reproducción

- [Inventario por archivo, páginas, tamaño y SHA-256](inventario_pdf.json).
- [Script de inventario y extracción](auditar_pdf.py). Ejecutar `python revision_caminera/auditar_pdf.py` desde la carpeta principal, con `pypdf` instalado. Vuelve a generar el inventario y textos; no modifica originales.
- `texto_pdf/`: texto extraído, separado por documento y número de página. Es una ayuda de inspección, no una conversión validada a dataset.
- `vistas/`: páginas renderizadas para comprobar encabezados, unidades y cifras. La imagen `paginas_imagen_1.png` muestra las páginas con contenido visual y escaso texto extraíble que se revisaron adicionalmente.
- `tmp/`: dependencias y material de revisión visual. No son datos de entrenamiento.

Las cifras y las conclusiones anteriores se basan en los PDF locales. El acceso mediante la herramienta web a la página de estadísticas no produjo una lectura utilizable en esta revisión, por lo que no se afirma que esa página se haya actualizado o siga publicando exactamente el mismo inventario. No se investigaron aún Brasil, Reino Unido ni otros portales, respetando la prioridad de evaluar primero esta carpeta.
