# Comparación de datasets para el Proyecto Integrador

Fecha de verificación: 31 de octubre de 2026. Investigación de descargas públicas; no se contactó a ninguna institución ni se presentó un pedido de acceso. El proyecto mensual anterior se conserva sin cambios. No se entrenaron modelos con esta nueva base.

## Recomendación

Para el objetivo de construir y evaluar un modelo con información individual real, recomiendo **PRF Brasil, 2017–2025, clasificación de víctimas heridas frente a fallecidas**. Hay **754.098 participaciones con esas etiquetas**, claves válidas y accidente vinculado, antes de limpiar características. Es una mejora sustancial respecto de expandir totales agrupados de sexo y edad. No implica que el modelo ya tenga buen rendimiento: eso debe medirse con datos futuros reservados.

Pregunta propuesta: **¿Qué características de las personas, los vehículos y las condiciones del siniestro se asocian con el fallecimiento registrado, frente a lesiones no fatales, en las carreteras federales de Brasil entre 2017 y 2025?** La fase 3 puede estimar esa probabilidad con las características observadas. El alcance es la cobertura de PRF; no todos los accidentes de Brasil ni Paraguay. Es un estudio observacional: asociación no demuestra causalidad.

Si prefieren el pronóstico, PRF también permite estudiar **cantidades diarias de siniestros registrados** y sumar un pronóstico para el año siguiente. Tiene más preparación y evaluación temporal que la clasificación. No aconsejo un modelo cuyo entrenamiento sea una fila por año.

## Lo que se pudo verificar en Paraguay

| Fuente | Qué hay disponible o verificado | Pregunta sobre gravedad individual | Pronóstico de cantidades |
|---|---|---|---|
| Patrulla Caminera e INE | PDFs y tablas estadísticas; nuestra serie anterior tiene 108 meses, 2016–2024 | No se reconstruyen fichas de víctimas con sus vehículos; faltan claves individuales | Viable como serie mensual pequeña, con resultados anteriores limitados |
| Portal Nacional de Datos Abiertos | CSV/JSON del anuario con totales por sexo/edad, mes, causa, ruta, etc. | El formato CSV conserva las agregaciones; no resuelve las uniones individuales | Puede facilitar la lectura, sin crear fechas ni casos nuevos |
| ANTSV / SIAT | Publicaciones del Observatorio y recursos sobre el sistema; no se verificó una exportación pública de fichas | No hay una descarga inmediatamente utilizable confirmada en esta revisión | Los boletines no equivalen a una serie diaria completa descargable |
| Hospital de Trauma | Informes semanales 2023–2024 y publicaciones posteriores; una muestra contiene conteos con fechas diarias | Algunos PDF incluyen listas parciales de niños accidentados en moto y fallecidos de distintas causas; no una cohorte completa de todas las víctimas | Candidato para demanda hospitalaria, con extracción de PDF y cobertura aún por auditar |
| DIGIES / MSPyBS | La página pública de datos abiertos enumera muertes maternas y suicidios; hay otras publicaciones estadísticas | No se verificó allí una base completa de víctimas viales heridas y fallecidas | Los indicadores de otras causas no responden a esta pregunta |

La conclusión es **no encontré una descarga pública paraguaya adecuada y lista para este proyecto individual**. No se afirma que las instituciones carezcan de microdatos: pueden tener registros internos. Con el plazo disponible y sin pedidos institucionales, esos registros no son una opción confirmada.

Fuentes oficiales consultadas:

- [Patrulla Caminera: estadísticas](http://caminera.gov.py/index.php/estadisticas). Auditoría previa local en `../revision_caminera/`.
- [INE: anuarios](https://www.ine.gov.py/tabulado/16/anuario).
- [Datos.gov.py: anuario policial y de accidentes 2021](https://www.datos.gov.py/dataset/anuario-2021-estadisticas-policiales-y-de-accidentes-de-transito). Los títulos describen explícitamente tablas de cantidades agrupadas.
- [ANDA: catálogo](https://anda.ine.gov.py/anda/index.php/catalog). La entrada del Anuario Estadístico 2021 dice «No hay microdatos disponibles»; esto se refiere a esa operación, no a todo el catálogo del INE.
- [ANTSV: Observatorio Vial](https://antsv.gov.py/observatorio-vial/). El enlace del manual de SIAT dirigió a [inicio de sesión](https://nube.antsv.gov.py/index.php/f/65918). Eso por sí solo no prueba el estado de todos los archivos del sistema. Otras descargas ensayadas devolvieron errores o no pudieron inspeccionarse; no se presupone su contenido.
- [Hospital de Trauma: informes semanales](https://htrauma.gov.py/informe-semanal/). [Muestra del 2 al 8 de septiembre de 2024](https://htrauma.gov.py/wp-content/uploads/2025/02/DATOS-ESTADISTICOS-SEMANAL-LUNES-9-DE-SETIEMBRE-DE-2024.pdf): siete cantidades diarias, que suman 224 en la fila denominada accidentes de tránsito. La misma semana reaparece en más de un enlace del índice: habría que deduplicar por contenido y fechas.
- [Hospital de Trauma: estadísticas](https://htrauma.gov.py/112-2/). Informa implementación de HIS en consultorio externo desde 16/12/2024 y urgencias desde 06/01/2025, un posible cambio de registro que habría que examinar.
- [DIGIES: datos abiertos](https://digies.mspbs.gov.py/datos-abiertos/) y [biblioteca](https://digies.mspbs.gov.py/document-library/). Se pudo leer el índice a través del buscador; el acceso directo a algunas páginas falló.

**Cuidado con Trauma:** un conteo hospitalario no es el número de accidentes distintos de todo Paraguay. La fecha de atención puede diferir de la del choque, un accidente puede generar varias atenciones y las listas de fallecidos incluyen causas no viales. Las listas seleccionadas de niños o fallecidos tampoco permiten calcular el riesgo de muerte de todos los accidentados: la selección depende del grupo o del desenlace. No se reproducen datos identificatorios de pacientes en este informe. No se ha reconstruido ni validado una serie diaria completa; no se presenta una cantidad hipotética de días como si ya fueran datos obtenidos.

Los intentos de API CKAN en Datos.gov.py devolvieron 404 (`catalogo_paraguay.json`). Esto es un fallo del endpoint ensayado, **no una prueba de catálogo vacío**; la revisión también utilizó páginas oficiales y búsquedas web.

## Brasil: archivos reales descargados e inspeccionados

Fuente: [portal de datos abiertos de PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf) y [diccionarios oficiales](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes).

Se descargaron 18 ZIP (un CSV de accidentes y uno de personas por año) y 2 diccionarios PDF. Unos 108 MB en total. El manifiesto `descargas_prf.json` conserva URL, tamaño y SHA-256. Los CSV se leyeron completos, con separador `;` y codificación Latin-1. No son conteos convertidos artificialmente en fichas.

| Año | Accidentes con ID único | Filas originales en personas | Participaciones con pesid positivo | Heridas o fallecidas, antes de limpiar variables |
|---|---:|---:|---:|---:|
| 2017 | 89.567 | 224.237 | 204.404 | 90.567 |
| 2018 | 69.333 | 180.061 | 164.889 | 81.969 |
| 2019 | 67.558 | 176.104 | 162.500 | 84.535 |
| 2020 | 63.585 | 162.245 | 147.757 | 76.810 |
| 2021 | 64.567 | 166.287 | 150.974 | 77.270 |
| 2022 | 64.606 | 170.825 | 155.386 | 78.506 |
| 2023 | 67.766 | 183.361 | 166.933 | 84.090 |
| 2024 | 73.202 | 196.448 | 179.247 | 90.758 |
| 2025 | 72.529 | 194.629 | 177.479 | 89.593 |
| **Total** | **632.713** | **1.654.197** | **1.509.569** | **754.098** |

Las 754.098 candidatas se distribuyen así: **535.866 lesiones leves**, **167.407 lesiones graves** y **50.825 fallecimientos (`Óbito`)**. Para la pregunta original se unen lesiones leves y graves: **703.273 heridas frente a 50.825 fallecidas**. Se excluyen ilesos y estados desconocidos del objetivo binario, conservando su recuento en la auditoría.

No llamamos a las 1.654.197 filas «personas únicas»: **144.628 filas tienen `pesid=0` y `estado_fisico=NA`**. Se observan en registros asociados a vehículos sin persona identificada en esa exportación; algunas se repiten dentro de un accidente con distintos vehículos. No representan 144.628 individuos identificados ni sirven como claves de personas. Las 1.509.569 participaciones con `pesid` positivo sí tienen claves únicas en este conjunto, pero tampoco demuestran 1.509.569 personas naturales diferentes a lo largo de nueve años: una misma persona puede participar en accidentes distintos.

Los archivos de accidentes declaran en conjunto 1.603.093 involucrados; tampoco debe confundirse ese total con el número de fichas personales completas. Hay 33.070 accidentes cuyo conteo declarado de personas difiere del número bruto de filas exportadas en personas. Esta es otra razón para no usar la cantidad bruta de filas como población de víctimas.

## Variables y uniones verificadas

La tabla de accidentes tiene **30 columnas** y la de personas **35**. Comparten numerosos campos; son **39 nombres de columna diferentes** al considerar ambas, no 65 variables independientes. Parte de esos campos son identificadores o desenlaces, no predictores.

- Persona: `pesid`, edad, sexo, tipo de involucrado (conductor, pasajero, peatón), estado físico.
- Vehículo: `id_veiculo`, tipo, marca y año de fabricación.
- Accidente: `id`, fecha, día de semana, hora, UF, municipio, carretera BR, kilómetro, coordenadas, causa principal registrada, tipo de accidente, fase del día, sentido de circulación, clima, tipo y trazado de vía, uso de suelo.

**Unión comprobada:** `personas.id → accidentes.id`, de muchas participaciones a un accidente, con `merge(validate='many_to_one')`. El **100 % de las 1.654.197 filas originales encuentra su accidente** en el archivo del mismo año. No hay IDs de accidente duplicados, ni discrepancias de fecha o UF en esa unión. Para las 754.098 víctimas candidatas no hay pares `(id,pesid)` duplicados, y todas tienen `pesid` positivo y accidente encontrado. No hace falta inventar personas ni unir por sexo/edad.

Los atributos del vehículo ya vienen en el CSV de personas. Se pueden organizar en una tabla derivada por `(id,id_veiculo)` cuando el ID de vehículo sea positivo; la auditoría no encontró atributos de vehículo discordantes dentro de esas claves. Hay **1.191.470 IDs positivos de vehículo distintos** en el período. No se descargó una tercera tabla independiente de vehículos. Un peatón puede carecer de vehículo propio: no debe eliminarse automáticamente por ese motivo.

El portal también ofrece una variante con todas las causas y tipos. No se utilizó: su estructura puede multiplicar las filas de una misma participación al representar varios elementos del accidente.

## Calidad y comparabilidad: qué falta limpiar

El portal ofrece años desde 2007; se priorizó **2017–2025**, porque PRF documenta cambio de BR-Brasil a BAT en 2017. 2026 está en curso y no se tomó como un año completo. Los archivos leídos cubren de enero a diciembre de cada año, sin fechas no interpretables, con registros en todos los días del período. Esto confirma cobertura temporal del archivo, no ausencia de subregistro en la realidad.

Los mismos nombres de columna aparecen en los nueve años, pero las categorías varían: por ejemplo, las causas distintas observadas pasan de 24 en 2017 a 71 en 2021. No equivale a una taxonomía idéntica. Hay trazados de vía compuestos con `;`, categorías desconocidas, edad cero ambigua, edades imposibles y años de vehículo cero. La causa principal es una atribución del registro policial y puede conocerse después de investigar el siniestro. Hay que definir en qué momento se pretende hacer la predicción para decidir si corresponde incluirla.

El número final de entrenamiento se decidirá tras esa limpieza; no se asegura que las 754.098 candidatas conserven todas sus características. No corresponde eliminar toda fila con algún faltante ni tratar edad cero automáticamente como recién nacido. Hay que contrastar códigos y tipo de involucrado, marcar faltantes, imputar dentro del entrenamiento y documentar las exclusiones. El desenlace es el registrado por PRF; no se supone seguimiento hospitalario a 30 días.

## Comparación de las dos preguntas

| Aspecto | Gravedad de víctimas con PRF | Pronóstico de cantidades con PRF |
|---|---|---|
| Unidad para modelar | Participación de una víctima herida o fallecida | Día o semana, con cantidad de accidentes distintos |
| Volumen inicial | 754.098 registros elegibles antes de limpiar características | 3.287 días con registros; unos 470 intervalos semanales, según los cortes |
| Si se agrupa por mes/año | No es necesario para la clasificación individual | Solo 108 meses o 9 totales anuales; el gran número de accidentes no aumenta ese N temporal |
| Información útil | Datos de persona, vehículo, lugar y condiciones del evento | Calendario conocido, tendencia, estacionalidad, rezagos y agregaciones históricas |
| Unión | Clave real de accidente; vehículos ya asociados a cada participación | Se cuenta cada ID de accidente una sola vez, sin sumar filas de personas |
| Dificultad principal | Desbalance, faltantes y evitar usar el desenlace como predictor | Cambios de registro/movilidad, dependencia temporal y horizonte largo |
| Evaluación | Separación por fecha y accidente, métricas de ambas clases | Orígenes temporales, comparación con ingenuo estacional y horizonte que coincida con el uso |
| Recomendación para el plazo | Preferida por riqueza individual y relación con el trabajo original | Alternativa válida, preferiblemente diaria o semanal |

También se generaron 2.916 celdas mes–UF (27 × 108). Eso permite un panel regional, pero las celdas comparten tiempo y contexto: no son 2.916 meses independientes ni más años de historia. Para pronosticar un año, se puede estimar una trayectoria diaria/semanal y sumar, con intervalos de incertidumbre. Una evaluación de un paso usando rezagos actualizados no demuestra capacidad de anticipar todo un año desde un único corte. No se puede usar el clima real, las causas o las víctimas del año futuro como si fueran conocidas al pronosticarlo. Los datos 2007–2016 podrían estudiarse en una ampliación con armonización del cambio de sistema; no se incorporaron a los recuentos verificados aquí.

## Cómo evitar un resultado engañoso en la fase 3

En las candidatas actuales, predecir siempre «herida» ya daría **93,26 % de exactitud**, con **cero capacidad de detectar fallecimientos**. Ese es un baseline aritmético, no un modelo entrenado. Por eso una exactitud alta, sola, no demuestra aprendizaje útil. Hay que informar recall y precisión de fallecidos, F1, PR-AUC, balanced accuracy, matriz de confusión y, si se interpretan probabilidades, calibración.

Nunca usar como predictores `estado_fisico`, `mortos`, `feridos_leves`, `feridos_graves`, `ilesos`, `classificacao_acidente` ni agregados de víctimas que revelen el resultado. `id`, `pesid` e `id_veiculo` son claves, no señales para memorizar el desenlace. Definir los campos disponibles en el momento de uso y mantener juntas las personas de un mismo accidente.

Una división defendible a fijar antes de entrenar sería 2017–2023 para desarrollo, 2024 para validación y 2025 reservado para evaluación final. La selección de variables, imputación, codificación, balanceo y ajuste de modelos deben aprenderse sin utilizar el conjunto final. Las pruebas de hipótesis sobre personas deben considerar que víctimas del mismo accidente no son independientes. Los resultados de Brasil no se presentan como representativos de Paraguay ni como mejora de métricas directamente comparable con otro problema y población.

## Archivos y reproducción

- `fuentes_brasil/`: 18 ZIP originales y 2 diccionarios PDF.
- `catalogo_prf.json`: enlaces seleccionados desde la página oficial.
- `descargas_prf.json`: manifiesto con hashes y procedencia de cada descarga.
- `perfiles/resumen_prf_2017_2025.json`: auditoría completa, incluyendo nulos, códigos, clases y controles de unión.
- `perfiles/cantidades_por_anio.csv`: recuentos anuales.
- `perfiles/accidentes_por_dia.csv`: 3.287 filas, una por fecha; suma 632.713 accidentes.
- `perfiles/accidentes_por_mes_uf.csv`: 2.916 celdas regionales observadas.
- `perfiles/dicionario_*.txt`: texto extraído de los diccionarios oficiales.

Desde la carpeta principal, con Python y pandas disponibles:

```powershell
python INVESTIGACION_DATASETS/descargar_prf.py
python INVESTIGACION_DATASETS/perfilar_prf.py
python INVESTIGACION_DATASETS/crear_informe.py
```

La descarga requiere conexión; el perfilado y este informe funcionan con los ZIP ya guardados. Los conteos reflejan esta copia de las descargas: PRF actualiza sus archivos y futuras versiones pueden cambiar. Esta investigación prepara la decisión de dataset/pregunta; todavía no contiene modelos ni resultados de aprendizaje de Brasil.
