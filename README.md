# Gravedad de víctimas de accidentes de tránsito, Paraguay (2021)

Proyecto integrador de Ciencia de Datos, Ingeniería Informática, FP-UNA.
Integrantes: Alan Alcaraz, Leandro Ferreira y Jorge Rios.

Las Fases 1 y 2 entregadas permanecen intactas. Fase 3 compara regresión logística,
árbol, Random Forest y Naive Bayes categórico con un Dummy, conservando las
explicaciones, tablas, gráficos y conclusiones dentro del notebook ejecutado.

## Organización

```text
data/              11 tablas originales únicas del anuario y referencia agregada DINATRAN para H3
notebooks/         Fases 1, 2 y 3; salidas y gráficos embebidos
src/
  preparar_datos.py       reconstrucción demográfica y resúmenes de contexto
  auditoria_fase3.py      contrastes de edad y evaluación territorial agregada
  complementos_fase3.py   análisis en memoria y lectura de tablas/figuras del ipynb
  inferencia.py          carga independiente del único modelo serializado
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
tests/
  test_fase3.py
  test_auditoria.py
README.md
requirements.txt
requirements-lock.txt
.gitignore
.gitattributes
```

`.venv/`, `tmp/`, cachés, checkpoints, `entrega/` y `docs/local/` son locales e
ignorados por Git. Solo este README se publica como Markdown; las notas auxiliares
se conservan localmente. Al preparar el ZIP manualmente, revisar qué archivos se incluyen.
Los PNG de cualquier carpeta y las exportaciones `*_excel.csv` también permanecen
locales y fuera de Git; excluirlos del ZIP si no son necesarios. Los gráficos se consultan dentro de los notebooks,
HTML e informes. Se conservan los CSV y JSON históricos que necesita el proyecto.
Los cuatro candidatos se evalúan en memoria; solo se guarda el ganador.
Sus metadatos de variables, categorías y alcance están integrados en el mismo joblib.

Los cinco CSV compartidos permanecen en la raíz de `output/` para conservar las
rutas que leen las Fases 1 y 2 sin editar sus notebooks. Los archivos históricos
reubicados conservan sus bytes. Una reejecución de esos notebooks históricos
puede volver a escribir sus exportaciones en las rutas originales; la reproducción
de Fase 3 utiliza la estructura organizada y no necesita ejecutar Fases 1/2.

## Instalación y ejecución

Auditoría comprobada con Python 3.13.14 en Windows, en un entorno virtual limpio.
Cumple el mínimo 3.10 de la consigna; no se verificó este conjunto de versiones
con Python 3.10. `requirements-lock.txt` fija también dependencias transitivas.

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe src/preparar_datos.py
```

En Linux/macOS sustituir el ejecutable por `.venv/bin/python`.
El último comando prepara o coteja el dataset demográfico y los tres resúmenes;
no entrena modelos ni exporta HTML.

Para ejecutar Fase 3 manualmente:

1. Abrir `notebooks/Fase3_Accidentes_AUDITADA.ipynb` en VS Code o Jupyter.
2. Seleccionar como kernel el entorno `.venv` con las dependencias instaladas.
3. Elegir **Reiniciar kernel y ejecutar todas las celdas** y esperar a que termine.
4. Comprobar que no haya errores y guardar el notebook con sus salidas.
5. Revisar las interpretaciones metodológicas Markdown si se cambia el experimento.
   Los resúmenes numéricos generados por Python se actualizan al ejecutar sus celdas.

El notebook prepara/coteja los datos, entrena y evalúa los candidatos y guarda
`output/fase3/mejor_modelo_fase3.joblib`. La exportación a HTML es un paso separado.
Después de guardar el notebook ejecutado, exportarlo desde el editor o utilizar:

```powershell
.\.venv\Scripts\python.exe -m nbconvert --to html notebooks/Fase3_Accidentes_AUDITADA.ipynb --output Fase3_Accidentes_AUDITADA --output-dir output/fase3
```

Este comando exporta las salidas guardadas; no vuelve a ejecutar las celdas.
La ejecución del notebook, los tests, la preparación de informes y el armado del
ZIP se realizan por separado.

`preparar_datos.py` reúne la reconstrucción de 12.2.1 y la regeneración de resúmenes
territorial, mensual y de rutas. Verifica las frecuencias y el orden demográficos;
los indicadores de edad desconocida son NA. `reconstruir()` y
`regenerar_resumenes()` son funciones separadas del mismo módulo; ejecutar el
script llama a ambas. El anterior `regenerar_contexto.py` fue fusionado en él.
El CSV vehicular conserva las etiquetas históricas como antecedente y no es
necesario para entrenar. La revisión DINATRAN precisa los grupos de H3 a partir
de conteos agregados, sin reescribir ese CSV. No se deben ejecutar Fases 1/2 sobre
el proyecto actualizado: sus versiones históricas pueden reintroducir -1 y 0.
Se ejecutaron en copias aisladas para comprobar su reproducibilidad histórica.

El diagnóstico técnico previo a esta simplificación está en
[AUDITORIA_TECNICA_FASE3.md](AUDITORIA_TECNICA_FASE3.md); sus referencias a scripts
anteriores describen esa revisión histórica. La organización vigente es la de este README.
Ese archivo es local porque la configuración existente ignora Markdown adicionales;
no se modificó la configuración de Git. `docs/fase3/` incorpora la revisión H3;
el integrador conserva su versión anterior y requiere consolidar esta revisión
antes de una nueva entrega conjunta. Las Fases 1 y 2 no se reescriben.

## Recorrido de estudio, gráficos e informes manuales

El notebook sigue este orden: datos y preparación → modelos → validación cruzada
→ evaluación → errores → interpretación y sensibilidad → hipótesis H1–H4 →
modelo guardado e inferencia → conclusiones. El anexo conserva las grillas completas
y tablas detalladas; train/CV, H4 y los diagnósticos ya no dependen de leer un bloque
técnico oculto para comprender sus resultados.

`calcular_diagnosticos()` calcula una vez errores, calibración, importancia y
sensibilidad por perfiles. `mostrar_complementos()` presenta las figuras elegidas
con esos resultados. Las funciones reciben argumentos explícitos y devuelven sus
resultados; no leen ni modifican `globals()` del notebook. La sensibilidad del
ganador se extrae de la evaluación por grupos de todos los candidatos, sin volver
a entrenarlo sobre los mismos cuatro pliegues.

Los once gráficos de Fase 3 se muestran mediante `plt.show()` y permanecen
embebidos en el `.ipynb` y el HTML, junto con títulos e interpretaciones. No hay
llamadas a `savefig()` en el notebook ni en su análisis complementario.

Las tablas y los metadatos de resultados se conservan en las salidas estructuradas
del notebook. Los Word se editan manualmente y los PDF se exportan desde el editor
de documentos. Ejecutar el notebook o exportar su HTML no actualiza los informes.

Utilizar el notebook ejecutado como evidencia para incorporar tablas, figuras e
interpretaciones. El informe de Fase 3 incorpora H4 corregida y la revisión H3 de
DINATRAN/INE. El integrador histórico debe incorporar la misma precisión de H3
cuando se prepare su próxima edición.

Antes de entregar, comprobar carátula, legajos, índice, numeración, legibilidad e
imágenes incrustadas. Verificar los límites de **15 páginas para Fase 3** y
**30 páginas para el integrador** sobre los PDF finales, después de cada edición.

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
DINATRAN identifica los roles de motocicleta/motocarro y respalda una asociación
vehicular agregada en el registro de Caminera; eso no crea vínculos con la tabla
nacional ni incorpora vehículo al Modelo A. Ningún resultado autoriza uso clínico, triaje, seguros,
vigilancia por perfil ni atribución causal.

Las cuatro hipótesis se conectan explícitamente en el notebook y los informes:

| Hipótesis | Evidencia y alcance en Fase 3 |
|---|---|
| H1 — Zona | Tres tasas anuales y 36 celdas mes/zona sin expandir. Se evaluó GLM binomial por zona con tres bloques cronológicos: no supera consistentemente la tasa global de entrenamiento en log-loss/Brier. Se conserva como experimento, sin recomendar su uso predictivo. El contraste histórico Interior/Metropolitana tiene p Bonferroni 0,046565 y V de Cramér 0,0653, condicionado a esa agrupación. |
| H2 — Sexo | Asociación histórica y uno de los dos predictores demográficos; no atribución causal ni riesgo individual. |
| H3 — Motocicletas | DINATRAN pp.130/132/133/135/136 documenta 534 conductores/acompañantes de motocicleta + 5 pasajeros de motocarro dentro de 1.324 víctimas. Coinciden los doce meses del INE. 539 frente a 785 demás usuarios: RR=1,9802; OR=2,3758. Sin motocarro: 534 frente a los mismos 785 (N=1.319), RR=1,9472; OR=2,3206. Ambos Fisher mantienen evidencia con Bonferroni de seis. El resto incluye peatones y ciclistas; asociación registrada, sin causalidad ni predictor vehicular nacional. |
| H4 — Edad | Mann-Whitney corregida sobre 5.140 edades conocidas: U=2.299.236; p≈1,657×10⁻²⁰; r biserial=0,1854, IC bootstrap [0,1455; 0,2266]. Comparación separada de 60 años o más: RR=2,0455, IC 95 % [1,7319; 2,4158]. Los ajustes previos de cuatro pruebas se conservan para cotejo; la familia ampliada de seis mantiene H4. |

La [revisión verificable de H3](docs/fase3/Revision_H3_fuentes.html) reúne páginas,
URL, hashes, definiciones, conteos y fórmulas. La transcripción agregada está en
`data/referencia_h3_dinatran_2021.json`; no contiene personas reconstruidas.
`auditar_h3()` coteja mes y rol frente al INE y calcula los contrastes directamente
con tablas 2×2. El subgrupo está respaldado documentalmente por estructura,
fuente y compatibilidad de las tablas; no existe enlace de IDs individuales.

Se añade un Bonferroni conjunto de seis preguntas: H1, H2, H3 histórica, H4
ordinal corregida, ≥60 y sensibilidad H3 sin motocarro. La tabla
`multiplicidad_actual` muestra todos los p sin seleccionar resultados favorables.
H1 queda en p=0,069847 para esta familia ampliada; su p histórico con cuatro
(0,046565) sigue documentado como antecedente, no se sustituye silenciosamente.

En el dataset corregido, `edad_orden` y `es_adulto_mayor` son NA para los 353
registros `Ignorado`. Se mantienen las 5.493 filas; solo los contrastes etarios
excluyen desconocidos. Ninguna de esas dos columnas derivadas entra al predictor.
Los IC y valores p suponen muestreo independiente condicionado a los conteos;
no se dispone de identificadores de siniestro para comprobar esa independencia.

La pregunta original se responde parcialmente: hay señal demográfica retrospectiva
limitada y asociaciones territorial y vehicular separadas. No se acredita el efecto conjunto de
los cuatro factores ni un riesgo poblacional por exposición. La integración ampliada
queda disponible para la revisión final del grupo.

## Pruebas y trazabilidad de la limpieza

La batería contiene 37 pruebas: 20 de Fase 3, diez de auditoría y siete de H3. La verificación
del paquete se adaptó a la existencia de los entregables del flujo manual; ya no
importa el empaquetador eliminado. Una prueba adicional comprueba las interfaces
explícitas y que la sensibilidad por grupos se calcule una sola vez.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas recalculan los cuatro modelos en memoria, comprueban sus métricas
anteriores a la limpieza y las salidas embebidas, observan que las búsquedas usan
solo train, verifican pliegues, recarga del modelo, categorías, CLI, errores,
solapamiento, reconstrucción desde originales y hashes de Fases 1/2. También
prohíben guardar figuras durante el análisis de prueba y comprueban Word/PDF.
Las pruebas de Word/PDF verifican estructura y referencias
históricas; no acreditan que esos informes incluyan las correcciones nuevas.

Se retiraron las 12 copias de `data/raw` después de comprobar igualdad SHA-256 con
los originales conservados; el dataset procesado obsoleto no tenía referencias
en código vigente. Se retiraron scripts de migración/verificación antiguos,
cuatro modelos candidatos serializados, el modelo vehicular obsoleto, gráficos y
tablas/logs auxiliares. Sus análisis permanecen en el notebook; las verificaciones
de resultados están en los módulos de análisis y las pruebas. Se fusionó la documentación
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

El ZIP se prepara manualmente. Incluir `data/`, `notebooks/`, `src/`, los resultados
necesarios de `output/`, los informes finales de `docs/`, `tests/`, README y los
archivos de dependencias. Conservar los antecedentes JSON/CSV de Fase 2 que leen
los análisis y los cuatro módulos vigentes de `src/`.

Excluir `.venv/`, `.git/`, `__pycache__/`, temporales, logs y copias locales.
Si los originales superan 25 MB, aplicar la alternativa de fuente y descarga
indicada por la consigna. Usar la nomenclatura final
`Fase3_DataScience_Alcaraz-Ferreira-Rios.zip`, previa confirmación de los apellidos.

Abrir el ZIP y comprobar que contiene el notebook ejecutado, su HTML, el modelo,
`src/inferencia.py` y ambos PDF finales. El manifiesto interno y las comprobaciones
automáticas de CRC/SHA-256 del antiguo empaquetador ya no se generan.
`.gitattributes` conserva los bytes de documentos, imágenes, modelos, datos,
notebooks y resultados al guardarlos en Git y al clonar. Así no se alteran los
hashes de procedencia e integridad por conversión automática de saltos de línea.

No se dispone de devolución docente de Fase 2. La interpretación actual y las
decisiones quedan pendientes de revisión y defensa por el grupo. Faltan legajos,
confirmación administrativa y revisión de los informes; los entregables originales
de Fases 1/2 se localizaron en Descargas y se consultaron sin modificarlos.

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
