# Qué mantuvimos y qué cambió entre Paraguay y Brasil

Revisión del 2 de noviembre de 2026. Se consultó el proyecto anterior de `C:\Users\Leandro\Desktop\DATAAAAA FASE 2\proyecto-accidentes-datascience` y los archivos del proyecto actual. No se modificó el repositorio anterior, no se entrenó otro modelo y no se subieron cambios a GitHub.

## La respuesta principal

**Continuamos el tema y el resultado que queríamos estudiar: la gravedad de las víctimas, heridas frente a fallecidas. Sin embargo, no conservamos exactamente la misma investigación.** El país, la población, los años, algunos grupos de comparación y las hipótesis formales cambiaron. Por eso Brasil no permite responder directamente por Paraguay en 2021 ni confirmar todas sus hipótesis.

La pregunta original incluía usuario de moto frente a otros, sexo, grupos de edad y Asunción/Central/Interior en Paraguay 2021. La pregunta nueva estudia características personales, vehiculares y del accidente en carreteras federales de Brasil durante 2017-2025, con evaluación posterior en enero-septiembre de 2026.

No elegimos como objetivo final pronosticar la cantidad de accidentes del próximo año. Esa fue una alternativa conversada y descartada; ambos clasificadores comparados aquí distinguen heridos y fallecidos.

## Fase 1: datos, fuentes y preparación

| Aspecto | Proyecto anterior | Trabajo de Brasil | Qué se mantuvo o por qué cambió |
|---|---|---|---|
| Fuente | Ocho CSV del anuario oficial 2021 de Paraguay, más una referencia posterior de DINATRAN para precisar H3. | PRF: tablas de ocurrencias y personas con vehículo asociado; 20 ZIP anuales y dos diccionarios oficiales en el corte conservado. | Se mantiene el uso de fuentes oficiales; cambia su nivel de detalle y cobertura. |
| País y cobertura | Tablas nacionales y tablas de Caminera con coberturas diferentes. No toda la información correspondía a las mismas víctimas. | Víctimas registradas por PRF en carreteras federales de Brasil. | Cambia la población. PRF tampoco representa todos los accidentes o viajes de Brasil. |
| Años | El objetivo demográfico era Paraguay 2021. Algunos archivos de contexto incluían otros años. | Período principal 2017-2025; prueba posterior enero-septiembre de 2026. | Incorporamos historia comparable desde el sistema BAT y una evaluación cronológica. |
| Filas y unidad | 5.493 filas reconstruidas a partir de frecuencias; 4.513 heridos y 980 fallecidos, pero solo 16 perfiles sexo por edad. | 754.098 participaciones reales en 2017-2025 y 67.591 en 2026: 821.689 filas limpias. | No buscamos simplemente más filas: buscamos varias características observadas para una misma participación. |
| Tablas de contexto | Tres filas territoriales que resumen 1.491 víctimas; 1.324 filas vehiculares reconstruidas; 12 meses que resumen 1.942 accidentes. | Las personas se relacionan con su accidente real. Los vehículos propios y otros vehículos aportan contexto. | Los conteos del proyecto anterior no podían convertirse en características individuales conjuntas. |
| Identificadores | `id_victima` e `id_caso` eran consecutivos creados al expandir cantidades. No vinculaban a la misma persona entre anuarios. | `id` identifica el accidente y `pesid` una participación; se conserva `id_veiculo` para formar el contexto. | Los identificadores de la fuente permiten comprobar uniones, no inventarlas. No son identidad civil longitudinal. |
| Variables disponibles para predecir | Sexo y grupo de edad. Zona, vehículo, fecha y causas no se podían unir correctamente al clasificador nacional. | 31 entradas: persona, vehículo, otros vehículos, tiempo, ubicación y condiciones del accidente. | Ampliamos la información conjunta que recibe el modelo. El Parquet tiene además seis campos de identificación/fecha/objetivo: 37 columnas no significa 37 predictores. |
| Edad | Ocho categorías, incluida Ignorado. La Fase 1 histórica usaba -1 para edad desconocida; la Fase 3 anterior auditada ya corrigió los indicadores desconocidos a NA. | Edad en años; cero ambiguo o valores fuera de 1-110 pasan a faltante, sin borrar la víctima. | Cambia la precisión de la medición. La corrección de desconocidos no comenzó recién en Brasil. |
| Limpieza y formatos | Limpieza de tablas agregadas, expansión de frecuencias y creación de resúmenes separados. | Conversión de fechas/números, normalización de categorías, verificación de fuentes, claves y uniones, revisión de faltantes y valores imposibles. | Se mantiene la preparación reproducible por código; cambian las comprobaciones posibles. |
| Selección del objetivo | Heridos y fallecidos. | Heridos leves/graves frente a fallecimiento registrado. Se excluyen ilesos y estado desconocido del objetivo binario. | Se mantiene el resultado general. Las definiciones institucionales y el seguimiento de muerte no son necesariamente idénticos. |
| Contexto vehicular | No podía agregarse al modelo nacional por persona. | Se cuentan vehículos identificados una vez por accidente, incluso cuando sus ocupantes están ilesos. Se resta el propio cuando corresponde. | Agregamos siete características de contexto sin usar cantidades de muertos o heridos. |
| Gráficos y descripción | Sexo, grupos etarios y resúmenes territoriales, mensuales y vehiculares de universos separados. | Diez gráficos sobre datos de desarrollo, con edad, vehículos, tiempo, relaciones, faltantes y contexto. | Se mantiene la exploración y se amplía la información. En Brasil la exploración usa 573.747 víctimas de 2017-2023, no toda la prueba futura. |

Los conteos anteriores eran oficiales; la limitación no era que fueran datos falsos, sino que **expandir totales no crea nuevas observaciones individuales independientes**. El README anterior menciona once tablas, pero en el directorio `data` consultado se verificaron ocho CSV y una referencia JSON. No se asumieron tres archivos adicionales que no se encontraron.

## Fase 2: correspondencia real de las hipótesis

Los números de hipótesis cambiaron. H1 anterior no es H1 nueva.

| Hipótesis original | Qué se hizo en el trabajo nuevo | Continuidad y límite |
|---|---|---|
| H1: Interior frente a Asunción/Central. | No se repitió ese contraste. La ubicación entra en exploración y predicción mediante UF, municipio, ruta y coordenadas. | **No se conserva la hipótesis territorial original.** No corresponde llamar Asunción/Central/Interior a regiones brasileñas ni afirmar que fue confirmada. |
| H2: sexo y gravedad. | Nueva H1: asociación entre sexo y herido/fallecido, con chi cuadrado. | Se mantiene el tema, con otra población y una víctima aleatoria por accidente. El contraste de independencia detecta asociación, no es por sí solo una prueba direccional de mayor riesgo masculino. |
| H3: motociclistas con mayor proporción fatal. | Nueva H3: diferencia bilateral entre usuarios de moto y otros vehículos conocidos, entre conductores/pasajeros. | Se mantiene la comparación vehicular como idea; **cambian los grupos, el universo y la alternativa estadística**. No es una repetición exacta. |
| H4: vulnerabilidad por edad; interés inicial en 60 años o más, prueba ordinal en Fase 2. | Nueva H2: comparación bilateral de la distribución de edad exacta entre heridos y fallecidos, con Mann-Whitney. | Se mantiene estudiar edad y gravedad. **No se ejecutó en Brasil un contraste específico de 60 años o más igual al anterior.** |
| Horario: parte del contexto descriptivo original. | Nueva H4: relación de la noche con la gravedad considerando edad, sexo, rol, ruralidad y tendencia anual. | Se agregó una hipótesis formal que no era una de las cuatro originales. Se usó regresión logística con incertidumbre ajustada por accidente. |

### Pruebas y resultados documentados

| Aspecto | Anterior | Brasil |
|---|---|---|
| Fuentes de los contrastes | Demografía nacional, territorio y vehículos en tablas separadas. | Base individual de desarrollo; H1-H3 seleccionan una víctima al azar por accidente. H4 usa todas las víctimas con las variables necesarias. |
| Independencia | No había ID de accidente para comprobar si varias víctimas compartían siniestro. | Selección por accidente en H1-H3 y errores agrupados por accidente en H4. Accidentes diferentes todavía pueden compartir condiciones temporales o geográficas. |
| Comparaciones múltiples | La salida histórica de Fase 2 usa Bonferroni y FDR-BH sobre cuatro pruebas. La revisión posterior de Fase 3 amplía algunos contrastes. | Holm sobre las cuatro hipótesis actuales. Se mantiene controlar resultados encontrados por repetir pruebas, pero no el procedimiento exacto. |
| Sexo | Fase 2 histórica: OR 2,0370; V de Cramér 0,0971; p Bonferroni 2,44e-12. | Nueva H1: V de Cramér 0,0730; evidencia de asociación pequeña. Los efectos no son una comparación causal entre países. |
| Edad | Fase 2 histórica: rangos de edad, U=2.576.490. La Fase 3 anterior auditada excluye desconocidos del contraste: U=2.299.236 sobre 5.140 edades conocidas; además estudia por separado 60 años o más. | Nueva H2: 370.413 casos con edad válida en la selección por accidente; efecto biserial 0,1606. Es edad en años y contraste bilateral. |
| Motocicletas | Resultado histórico RR 1,9802. La revisión DINATRAN precisa 539 víctimas de motocicleta/motocarro frente a 785 demás usuarios, que incluyen peatones y ciclistas. Sin motocarro: 534 frente a los mismos 785. | Nueva H3: proporciones 5,32 % y 5,68 %, diferencia de -0,362 puntos porcentuales, p Holm≈1,93e-6. Solo conductores/pasajeros con vehículo conocido. |
| Noche | No era una de las cuatro hipótesis formales originales. | Nueva H4: OR ajustado 1,8495, IC 95 % [1,7989; 1,9016], con 494.806 víctimas de 334.129 accidentes. OR no es un multiplicador directo de la probabilidad. |
| Bootstrap | La fase original lo aplicó, por ejemplo, a sexo y edad. La revisión anterior de edad utiliza 2.000 remuestras. | Se usa para incertidumbre de efectos; la comparación de proporciones moto/otros lleva 5.000 remuestras. Se mantienen remuestreo e intervalos, pero cambian efectos y unidades. |

**La diferencia vehicular de Brasil no confirma la dirección de la H3 original.** Tampoco demuestra que viajar en moto sea más seguro: ambas fuentes condicionan a víctimas registradas, no a viajes realizados, y usan comparadores distintos. La revisión posterior de DINATRAN del repositorio anterior ya precisaba esos grupos; no es un hallazgo nuevo de Brasil.

La Fase 2 histórica rechazaba las cuatro H0 con su corrección. En la Fase 3 anterior auditada, ampliar la familia a seis contrastes cambia el resultado territorial al 5 %. En Brasil se rechazan las cuatro H0 actuales con Holm, pero son preguntas parcialmente distintas. Por eso no corresponde decir simplemente «se volvieron a confirmar las mismas cuatro hipótesis».

## Fase 3: aprendizaje, evaluación y conclusiones

| Aspecto | Modelo anterior | Modelo nuevo | Motivo o lectura |
|---|---|---|---|
| Resultado a clasificar | Herido=0, fallecido=1. | Herido leve/grave=0, fallecido registrado=1. | Se mantiene la tarea central, con límites institucionales distintos. |
| Información de entrada | Sexo y grupo de edad; 16 perfiles. | 31 características individuales y del accidente/vehículos. | Agregamos información conjunta real, no solo filas. |
| Familias probadas | Regresión logística, árbol, Random Forest, Naive Bayes categórico y Dummy. | Regresión logística, árbol, Naive Bayes categórico, LightGBM y Dummy. | Se mantienen varias familias y la referencia mínima. Random Forest del anterior se reemplaza en la comparación nueva por LightGBM. No son el mismo algoritmo. |
| Ganador | Árbol de decisión: profundidad 6 y mínimo 50 filas por hoja. | LightGBM: 400 árboles, 15 hojas, tasa 0,04, mínimo 300 casos por hoja, L2=25. | Cambia el modelo y su configuración. No se prueba que solo cambiar el algoritmo explique la diferencia. |
| Separación de datos | 80/20 estratificado: 4.394 filas de entrenamiento y 1.099 de prueba. Sin fechas por persona. | 2017-2023 para aprender; 2024 H1 para calibrar; 2024 H2 para el punto de decisión; 2025 retrospectivo y 2026 posterior. | La nueva separación respeta el tiempo y mantiene juntas a las víctimas del mismo accidente. |
| Validación | Cinco pliegues estratificados. Sensibilidad con GroupKFold por perfil sexo-edad. | Tres cortes temporales: validar 2021/2022/2023 con años anteriores. | Se mantiene validación, cambia su diseño porque ahora hay fechas y accidentes identificables. |
| Selección | F1 macro de validación cruzada. | AP media temporal; punto de decisión por F1 de fallecidos en 2024 H2. | Cambia el criterio de selección; no se debe afirmar que se usó el mismo en ambos proyectos. |
| Desbalance | 82,16 % heridos y 17,84 % fallecidos. Pesos balanceados y prior balanceado en Bayes. | Aproximadamente 93 % heridos y 7 % fallecidos. Se compararon pesos en las configuraciones; el ganador usa proporción natural. | El problema no desaparece. Se mantienen F1 macro, precisión y detección como controles. No se usaron SMOTE ni duplicaciones en el modelo final. |
| Calibración | Se diagnosticaban las probabilidades; el artefacto devuelve puntuación no calibrada. | Ajuste sigmoide en 2024 H1, separado de la elección del punto de decisión. | Se agregó un ajuste explícito de los porcentajes de riesgo, sin garantía individual. |
| Interpretación | Importancia de sexo y edad, permutación y análisis de errores por perfil. | Importancia por permutación en 10.000 casos de validación; errores por grupos y contexto. | Se mantiene estudiar qué usa el modelo. Las variables importantes no se interpretan como causas. |
| Producto | Notebook, HTML, único modelo guardado y script de inferencia. | Los mismos tipos de entregables, datos limpios, resultados registrados y reproducción por código. | Se mantiene la entrega reproducible y un único modelo principal. |

### Cifras documentadas: pruebas diferentes

| Métrica | Paraguay: árbol, prueba interna de 1.099 filas | Brasil: LightGBM, 67.591 víctimas de 2026 |
|---|---:|---:|
| AUC | 0,5809 | 0,8449 |
| F1 macro | 0,5299 | 0,6748 |
| Precisión de fallecidos | 23,24 % | 37,34 % |
| Detección de fallecidos | 45,41 % | 42,36 % |

El resultado nuevo tiene mayor AUC y F1 macro, pero **no mejora todas las métricas**. Además, los grupos, proporciones de fallecidos, períodos y fuentes son diferentes: esta tabla no es una prueba controlada de que Brasil o LightGBM sean por sí solos la causa de la mejora. La reproducción del artefacto anterior con la partición documentada recuperó TN=609, FP=294, FN=107, TP=89 y las métricas publicadas.

Una comparación más justa dentro de Brasil enfrenta la referencia de 24 variables con la versión final de 31, sobre las mismas víctimas de 2026 y los mismos períodos de ajuste. La referencia obtiene AUC 0,7994 y F1 macro 0,6475; el final, 0,8449 y 0,6748. Cambiaron tanto las variables de contexto como la configuración/regularización. El final identifica 132 fallecidos más y produce 717 falsas alarmas menos.

El modelo final detecta 1.953 de 4.610 fallecidos, omite 2.657 y produce 3.277 falsas alarmas. No es suficiente para uso médico. El test anterior había sido inspeccionado históricamente; el modelo Brasil se fijó antes de abrir originalmente 2026. Hoy ambos resultados ya son conocidos: volver a ejecutarlos no crea una prueba ciega nueva.

## Qué no podemos afirmar que se mantuvo

1. No se conserva la población Paraguay 2021 ni la comparación Asunción/Central/Interior.
2. No se estima la misma H3 con la misma definición de usuarios, ni se confirma su dirección original.
3. No se repite en Brasil el contraste específico de adultos de 60 años o más.
4. La nueva hipótesis de noche ajustada es una incorporación, no una renumeración de la hipótesis territorial.
5. No se demuestra un efecto causal de sexo, edad, vehículo, ubicación o país.
6. No se dispone de velocidad de impacto, casco/cinturón o tiempos individuales de atención. La prueba con `causa_acidente` se descartó y no integra estos resultados.
7. No se predice el número de accidentes del próximo año, ni el riesgo de accidentarse de una persona cualquiera.

**Forma honesta de presentarlo:** «Quisimos continuar el estudio de gravedad de las víctimas. Las tablas originales no permitían reunir suficiente información individual, así que usamos registros oficiales de Brasil. Mantuvimos el tema y la clasificación herido/fallecido, pero adaptamos país, años, algunas hipótesis y la evaluación. Los resultados corresponden a la nueva población; no sustituyen conclusiones sobre Paraguay».

## Fuentes y versiones utilizadas

- Fases 1 y 2 anteriores: notebooks históricos y sus salidas; `output/fase2/resultados_fase2_consolidados.json` y tabla resumen.
- Fase 3 anterior: `notebooks/Fase3_Accidentes_AUDITADA.ipynb`, `docs/fase3/Informe_Fase3.pdf`, modelo guardado y `docs/fase3/Verificacion_H3.json`. Se prioriza la revisión posterior de H3 documentada en estos archivos frente a notas técnicas anteriores que quedaron desactualizadas.
- Evidencia documental de H3 anterior: `data/referencia_h3_dinatran_2021.json`; distingue conteos agregados de personas individualmente vinculadas.
- Nuevo proyecto: `data/fuentes.json`, `protocolo.json`, `output/tables/particiones.csv`, `contrastes_fase2.csv`, `importancia_modelo_final.csv` y los resultados en `output/modelado/`.
- `evidencia.json`, en esta carpeta, conserva cifras verificadas y huellas SHA-256 de las fuentes consultadas. El resumen gráfico usa esos datos; no estima ni inventa nuevas métricas.
