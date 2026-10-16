# Gravedad de víctimas de accidentes de tránsito, Paraguay (2021)

Proyecto integrador de Ciencia de Datos, Ingeniería Informática, FP-UNA.
Integrantes: Alan Alcaraz, Leandro Ferreira y Jorge Rios.

Las Fases 1 y 2 entregadas permanecen intactas. Fase 3 compara regresión logística,
árbol, Random Forest y Naive Bayes categórico con un Dummy, conservando las
explicaciones, tablas, gráficos y conclusiones dentro del notebook ejecutado.

## Organización

```text
data/              11 tablas originales únicas del anuario
notebooks/         Fases 1, 2 y 3; salidas y gráficos embebidos
src/
  preparar_datos.py       reconstrucción y comparación con los conteos originales
  complementos_fase3.py   análisis en memoria y lectura de tablas/figuras del ipynb
  ejecutar_fase3.py       kernel nuevo, HTML y verificaciones opcionales
  inferencia.py          carga independiente del único modelo serializado
  generar_documentos.py  Word/PDF con imágenes en memoria; guía local opcional
  empaquetar_entrega.py   ZIP con lista explícita de archivos y manifiesto interno
output/
  fase1/            bitácora de limpieza
  fase2/            HTML, JSON y tabla resumen históricos
  fase3/
    Fase3_Accidentes_AUDITADA.html
    mejor_modelo_fase3.joblib
  ... cinco CSV compartidos que leen los notebooks originales
docs/
  fase2/Fase2_Analisis_Inferencial.pdf
  fase3/Informe_Fase3.docx / .pdf
  integrador/Informe_Integrador_DataScience.docx / .pdf
tests/test_fase3.py
README.md
requirements.txt
requirements-lock.txt
.gitignore
.gitattributes
```

`.venv/`, `tmp/`, cachés, checkpoints, `entrega/` y `docs/local/` son locales e
ignorados por Git. Solo este README se publica como Markdown; las notas auxiliares
se conservan localmente y tampoco forman parte del ZIP.
Los PNG de cualquier carpeta y las exportaciones `*_excel.csv` también permanecen
locales, fuera de Git y del ZIP. Los gráficos se consultan dentro de los notebooks,
HTML e informes. Se conservan los CSV y JSON históricos que necesita el proyecto.
Los cuatro candidatos se evalúan en memoria; solo se guarda el ganador.
Sus metadatos de variables, categorías y alcance están integrados en el mismo joblib.

Los cinco CSV compartidos permanecen en la raíz de `output/` para conservar las
rutas que leen las Fases 1 y 2 sin editar sus notebooks. Los archivos históricos
reubicados conservan sus bytes. Una reejecución de esos notebooks históricos
puede volver a escribir sus exportaciones en las rutas originales; la reproducción
de Fase 3 utiliza la estructura organizada y no necesita ejecutar Fases 1/2.

## Instalación y ejecución

Entorno comprobado: Python 3.12.1 en Windows. Cumple el mínimo 3.10 de la consigna;
las versiones fijadas se verificaron con 3.12, no se promete compatibilidad con
Python 3.10. `requirements-lock.txt` registra también dependencias transitivas.

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/preparar_datos.py
.\.venv\Scripts\python.exe src/ejecutar_fase3.py --documentos --verificar
```

En Linux/macOS sustituir el ejecutable por `.venv/bin/python`. El último comando
ejecuta todas las celdas en un kernel nuevo, exporta HTML, regenera informes y
ejecuta las pruebas. Usa un directorio temporal del sistema que se limpia al cerrar;
no escribe logs, capturas, tablas intermedias ni PNG en el proyecto.

También se puede abrir el notebook de Fase 3 y ejecutar todas sus celdas. Para
ejecutar únicamente Fase 3 y exportar HTML:

```powershell
.\.venv\Scripts\python.exe src/ejecutar_fase3.py
```

`preparar_datos.py` reconstruye 12.2.1: si falta el CSV demográfico lo crea desde
la tabla original; si existe, compara todas sus filas y columnas. Los CSV/JSON
históricos de contexto ya se incluyen. No es necesario ejecutar o modificar las
Fases 1/2 para reproducir Fase 3.

## Gráficos, tablas e informes sin archivos auxiliares

Los once gráficos de Fase 3 se muestran mediante `plt.show()` y permanecen
embebidos en el `.ipynb` y el HTML, junto con títulos e interpretaciones. No hay
llamadas a `savefig()` en el notebook ni en su análisis complementario.

Las tablas y los metadatos de resultados se conservan en las salidas estructuradas
del notebook. Los informes leen esas salidas y las imágenes embebidas; usan
`BytesIO` para incrustarlas en Word y PDF, sin PNG permanentes ni un nuevo ajuste.

```powershell
.\.venv\Scripts\python.exe src/generar_documentos.py --pdf
```

Este comando solo produce los cuatro informes. La opción adicional `--guia-local`
genera material de estudio opcional en `docs/local/`. Los PDF tienen
15 páginas (Fase 3) y 18 páginas (integrador), incluidos carátula e índice, y las
pruebas comprueban el límite real de 15/30 páginas y la presencia de imágenes.
Ambos formatos son autocontenidos: no enlazan imágenes de `output/`.

El PDF se maqueta con ReportLab desde el mismo contenido que el Word; no es una
conversión del DOCX. La revisión visual de los DOCX sigue pendiente: LibreOffice
no está disponible y Word no completó la exportación en este equipo. Los PDF se
renderizan en memoria para revisar su diseño. En otro sistema se usa Helvetica
si falta Calibri; hay que volver a verificar paginación después de cambiar fuentes
o editar los informes.

## Inferencia independiente

```powershell
.\.venv\Scripts\python.exe src/inferencia.py --sexo Hombre --grupo-edad "De 18 a 29 anos"
.\.venv\Scripts\python.exe src/inferencia.py --sexo Mujer --grupo-edad Ignorado
```

El CLI carga `output/fase3/mejor_modelo_fase3.joblib` y sus metadatos integrados sin abrir
Jupyter. Admite Hombre/Mujer y las ocho etiquetas de edad de la fuente, incluida
Ignorado; rechaza entradas desconocidas. Devuelve clase y puntuación **no calibrada**.

## Metodología y resultados

La tarea es clasificar 0=herido y 1=fallecido mediante sexo y grupo de edad. Se
excluyen identificadores, gravedad y variables redundantes. La tabla 12.2.1
contiene 5.493 filas reconstruidas: 4.513 heridos, 980 fallecidos y **16 perfiles**.
La expansión reproduce frecuencias; no crea microdatos ni información adicional.

Partición 80/20 estratificada, semilla 42: 4.394 filas de train y 1.099 de test.
Los modelos utilizan los mismos cinco pliegues de entrenamiento y pipelines que
ajustan sus codificadores dentro de cada pliegue. Logística, árbol y bosque
conservan OneHotEncoder y `class_weight='balanced'`; NB categórico usa índices
nominales, suavizado y prior 0,5/0,5. No necesitan escalado. Se conservan las grillas
originales y se selecciona por F1 macro CV antes de evaluar test en esta ejecución.
Árbol y bosque pertenecen a una misma familia; Naive Bayes aporta una tercera.

| Modelo | F1 macro CV | F1 macro test | Recall fallecidos | AUC test |
|---|---:|---:|---:|---:|
| Dummy | 0,4510 | 0,4510 | 0,0000 | 0,5000 |
| Logística | 0,5278 | 0,5212 | 0,5153 | 0,5869 |
| **Árbol seleccionado** | **0,5416** | **0,5299** | **0,4541** | **0,5809** |
| Random Forest | 0,5234 | 0,4971 | 0,5204 | 0,5816 |
| Naive Bayes categórico | 0,5347 | 0,5212 | 0,5153 | 0,5989 |

El árbol tiene F1 macro train 0,5490: la brecha train-test es 0,0191. Sus errores
son TN=609, FP=294, FN=107 y TP=89. Omite 33/33 fatalidades entre mujeres y 81/81
en edades de 0–29 años. **Se superponen en 15 filas:** la unión es
33+81−15=99 FN, y los otros 8 son hombres con edad ignorada. Son frecuencias
reconstruidas, no expedientes individuales. Las tablas por sexo, edad y perfil
distinguen las tasas globales de error y las omisiones entre fallecidos.

GroupKFold deja perfiles completos fuera del entrenamiento: F1 macro medio 0,4556
y AUC 0,5248 para el seleccionado. Es sensibilidad interna condicionada a los
hiperparámetros ya elegidos, no validación anidada, temporal ni externa. Categorías
ausentes pueden generar advertencias esperables de OHE; con drop=first quedan
codificadas por ceros, como la referencia. No se silencian advertencias globalmente.

Las importancias Gini del árbol son edad 0,5267 y sexo 0,4733. Se complementan con
permutación y coeficientes/OR regularizados y ponderados, sin significado causal.
Las curvas de calibración y Brier muestran que mejorar F1 no garantiza calibración:
Brier del árbol 0,2457 frente a 0,1783 del Dummy.

El test ya fue inspeccionado en versiones anteriores. La repetición de perfiles,
la falta de fechas individuales y la búsqueda dentro de CV impiden presentar sus
métricas como garantía externa. La pregunta original se responde parcialmente:
edad/sexo ofrecen señal retrospectiva limitada, mientras geografía y siniestros
con motociclistas provienen de universos separados. No se unen artificialmente.
La tabla 12.2.10 no acredita el vehículo de cada víctima; el complemento vehicular
se mantiene descriptivo. Ningún resultado autoriza uso clínico, triaje, seguros,
vigilancia por perfil ni atribución causal.

Las cuatro hipótesis se conectan explícitamente en el notebook y los informes:

| Hipótesis | Evidencia y alcance en Fase 3 |
|---|---|
| H1 — Zona | Tres agregados sin expandir. Asunción: 26/167 (15,57 %); Central: 82/476 (17,23 %); Interior: 187/848 (22,05 %). El contraste histórico Interior/Metropolitana tiene p Bonferroni 0,046565 y V de Cramér 0,0653: efecto pequeño y resultado condicionado a esa agrupación. |
| H2 — Sexo | Asociación histórica y uno de los dos predictores demográficos; no atribución causal ni riesgo individual. |
| H3 — Motocicletas | 12.2.10 documenta 539 víctimas de siniestros con motociclistas, 384 heridas y 155 fallecidas. Se cotejan los doce meses y la construcción del CSV anterior; sus etiquetas y la relación de subconjunto no quedan acreditadas. RR/OR históricos se conservan condicionados, sin segundo predictor. |
| H4 — Edad | Categoría nominal en el modelo. Se separan 4.832 menores de 60 con edad conocida, 308 de 60 o más y 353 desconocidos. El contraste ordinal histórico de Fase 2 conservó -1 y no valida una comparación de mayores/menores de 60. |

`edad_orden = -1` significa edad desconocida, no inferior a la de los niños.
`es_adulto_mayor = 0` en `Ignorado` no acredita edad menor de 60. Ninguna de esas
dos columnas derivadas entra al predictor. Los análisis adicionales separan a los
desconocidos; las nuevas pruebas comprueban categorías y denominadores.

La pregunta original se responde parcialmente: hay señal demográfica retrospectiva
limitada y evidencia territorial separada. No se acredita el efecto conjunto de
los cuatro factores ni un riesgo individual por vehículo. La integración ampliada
queda disponible para la revisión final del grupo.

## Pruebas y trazabilidad de la limpieza

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas recalculan los cuatro modelos en memoria, comprueban sus métricas
anteriores a la limpieza y las salidas embebidas, observan que las búsquedas usan
solo train, verifican pliegues, recarga del modelo, categorías, CLI, errores,
solapamiento, reconstrucción desde originales y hashes de Fases 1/2. También
prohíben guardar figuras durante el análisis de prueba y comprueban Word/PDF.
Son 19 pruebas; incluyen el cotejo de H1/H3 con originales, los desconocidos y la
coincidencia de las cuatro hipótesis y métricas en notebook, Word y PDF.

Se retiraron las 12 copias de `data/raw` después de comprobar igualdad SHA-256 con
los originales conservados; el dataset procesado obsoleto no tenía referencias
en código vigente. Se retiraron scripts de migración/verificación antiguos,
cuatro modelos candidatos serializados, el modelo vehicular obsoleto, gráficos y
tablas/logs auxiliares. Sus análisis permanecen en el notebook; las verificaciones
vigentes están integradas en el runner y las pruebas. Se fusionó la documentación
en este README y los informes; los dos Markdown de estudio quedan en `docs/local/`.

Los archivos retirados conservan un respaldo local en `tmp/`, ignorado por Git,
con rutas y hashes para recuperación. El HTML histórico de Fase 2 está en `output/fase2/` y su PDF en
`docs/fase2/`, sin cambiar sus bytes. Los hashes de ambos notebooks se verifican en
las pruebas; el cambio que Git mostraba en Fase 2 ya existía antes de este trabajo.

`.gitignore` excluye entornos, cachés, temporales, paquetes y resultados auxiliares
de Fase 3, con excepciones para su HTML y único modelo. Las 15 copias/checkpoints
previamente rastreadas se retiran del índice; ignorar un archivo no basta para
dejar de seguirlo.

## Paquete y revisión académica

```powershell
.\.venv\Scripts\python.exe src/empaquetar_entrega.py
```

El ZIP local de revisión usa una lista explícita de originales, código, notebooks,
datos necesarios e informes. No recorre carpetas enteras de resultados ni incluye
el entorno, respaldo, cachés, logs ni Markdown auxiliares. `src/` y `tests/` son
parte del proyecto y del ZIP; no se ignoran. Su manifiesto SHA-256 está dentro del ZIP,
sin archivo JSON adicional en el repositorio; se comprueban hashes y CRC.
`.gitattributes` conserva los bytes de documentos, imágenes, modelos, datos,
notebooks y resultados al guardarlos en Git y al clonar. Así no se alteran los
hashes de procedencia e integridad por conversión automática de saltos de línea.

No hubo devolución docente de Fase 2. El grupo validó el alcance y la interpretación acotada de los
resultados. Faltan legajos, confirmación administrativa de apellidos y fecha del
campus, los Word históricos anunciados y la revisión personal del contenido.

Fuente: [Anuario oficial del INE](https://www.datos.gov.py/dataset/anuario-2021-estadisticas-policiales-y-de-accidentes-de-transito).
12.2.1 procede de Policía Nacional; 12.2.5 y 12.2.10 citan a Patrulla Caminera.
El PDF original de 12.2.6 cita a Patrulla Caminera, MOPC y Policía Nacional.
Referencias técnicas: documentación
oficial de scikit-learn enlazada en el notebook y los informes; consigna local,
apartados 7, 9.3, 9.5, 10, 11 y 12.

Codex asistió en auditoría, implementación, depuración y propuestas de documentación
e interpretación, y en esta simplificación. La validación del alcance no acredita
automáticamente el dominio personal del código: el grupo debe comprender todo el
contenido y revisar su compatibilidad con el apartado 11 de la consigna.
