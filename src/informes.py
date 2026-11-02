"""Informes desde los resultados congelados. No ajusta ni reevalua modelos.

Las funciones de maquetacion reutilizables se incluyen en pdf_layout.py.
"""
import csv
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
import pdf_layout as L
from textos import F1_TITULOS, F1_TEXTOS, F3_TEXTOS
L.OUT=OUT
W=L.WIDTH


def p(s,small=False):
    return L.p(str(s).replace('–','-').replace('—','-').replace('≥','>='),small)


def readj(name):return json.loads((OUT/name).read_text(encoding='utf8'))
def readc(name):
    with (OUT/'tables'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def read_csv_path(path):
    with path.open(encoding='utf-8-sig',newline='') as file:return list(csv.DictReader(file))

def f(v,n=3):return L.fmt(v,n)
def pct(v):return f(float(v)*100,2)+' %'
def pv(v):return '< 1e-300' if float(v)==0 else f'{float(v):.3g}'


def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Vera',7)
    canvas.drawString(1.6*cm,.8*cm,'Ciencia de Datos | Accidentes de tránsito en Brasil | 02/11/2026')
    canvas.drawRightString(A4[0]-1.6*cm,.8*cm,f'Página {doc.page}');canvas.restoreState()


def cover(label):
    return [Spacer(1,1.3*cm),p('CIENCIA DE DATOS - PROYECTO INTEGRADOR',True),Spacer(1,.5*cm),
            Paragraph(label,L.STYLES['TitleProject']),
            L.heading('Factores asociados a la gravedad de las víctimas en siniestros de tránsito'),
            p('Carreteras federales de Brasil - PRF - Estudio 2017-2025; validación enero-septiembre 2026'),Spacer(1,.7*cm),
            L.sub('Integrantes'),p('Alan Alcaraz · Leandro Ferreira · Jorge Rios'),
            p('Legajos pendientes de completar por el grupo.',True),L.sub('Alcance del trabajo'),
            p('Analizamos registros individuales de PRF para estudiar la gravedad y comparar modelos predictivos. Usamos herramientas de IA como apoyo en programación, análisis y redacción. El equipo debe revisar y comprender el contenido antes de presentarlo.'),
            p('El modelo distingue entre víctimas heridas y fallecidas registradas por PRF. Parte de un accidente que ya ocurrió: no predice quién tendrá un accidente ni cuántos accidentes habrá el próximo año. Su evaluación es académica, no médica.'),
            p('Fecha: 2 de noviembre de 2026.',True)]


def build(name,label,sections,index=True):
    story=cover(label)
    if index:
        story += [PageBreak(),L.heading('Índice de secciones')]
        story += [p(f'{i+1}. {title}') for i,(title,_) in enumerate(sections)]
    for title,content in sections:story += [PageBreak(),L.heading(title),*content]
    target=OUT/'reports'/name
    SimpleDocTemplate(str(target),pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=1.5*cm,bottomMargin=1.6*cm,title=label,author='Alan Alcaraz, Leandro Ferreira y Jorge Rios').build(story,onFirstPage=footer,onLaterPages=footer)
    print(target)


def main():
    a=readj('auditoria_preparacion.json');f1=readj('fase1_resultados.json');f2=readj('fase2_resultados.json');f3=readj('fase3_resultados.json');g3=readj('interpretaciones_fase3.json')
    f1['interpretaciones']=F1_TEXTOS
    g3=F3_TEXTOS
    proto=json.loads((ROOT/'protocolo.json').read_text(encoding='utf8'))
    chosen=f3['prueba'];results=[]
    def graph(name,texts):return [L.image(name,width=W*.92),p(texts[name])]
    objectives=['Unir los registros de víctimas, vehículos y accidentes mediante sus identificadores reales, sin inventar ni duplicar personas.',
                'Revisar la calidad de los datos y describir diferencias por edad, sexo, vehículo, lugar y horario.',
                'Comprobar cuatro hipótesis con pruebas estadísticas, considerando que varias víctimas pueden pertenecer al mismo accidente.',
                'Comparar distintas familias de modelos y evaluar cómo trabajan con muchos más heridos que fallecidos.',
                'Medir el resultado en datos posteriores al entrenamiento, explicar los errores y responder la pregunta de investigación.']
    problem=[L.sub('Contexto y relevancia'),p('La Policía Rodoviaria Federal de Brasil (PRF) publica datos de accidentes ocurridos en carreteras federales. Elegimos esta fuente porque permite relacionar a cada persona con su vehículo y accidente. En el trabajo anterior de Paraguay teníamos cantidades agrupadas: repetir esas cantidades como filas no creaba información individual nueva.'),
             L.sub('Pregunta principal'),p(proto['pregunta']),L.sub('Objetivo general'),p('Analizar qué características se relacionan con la gravedad y evaluar qué tan bien permiten distinguir entre víctimas heridas y fallecidas en un período posterior.'),L.sub('Objetivos específicos'),*L.bullets(objectives)]
    sources=[p('Usamos 20 ZIP con tablas CSV y dos diccionarios oficiales, descargados el 31/10/2026. Los archivos 2017-2025 tienen 632.713 accidentes y 1.654.197 filas en personas. El corte 2026 añade 54.895 accidentes y 148.868 filas en personas. No todas esas filas sirven para nuestro objetivo: hay ilesos, estados desconocidos y registros sin identificador de persona. En 2017-2025 hay 144.628 filas con pesid=0 que no contamos como personas identificadas.'),
             p('Después de seleccionar heridos y fallecidos, 2017-2025 tiene 754.098 víctimas: 703.273 heridas y 50.825 fallecidas. El corte de 2026 agrega 67.591 víctimas, con 4.610 fallecidos. El archivo limpio reúne 821.689 participaciones reales. Usamos id para unir cada persona con un solo accidente. Verificamos que la unión no añadiera filas ni dejara víctimas sin pareja. Los datos del vehículo ya vienen en personas: no inventamos una tercera fuente.'),
             L.table(['Partición','Víctimas','Fallecidos','Accidentes'],[[r['particion'],f(r['filas'],0),f(r['fallecidos'],0),f(r['accidentes'],0)] for r in readc('particiones.csv')],[W*.46,W*.18,W*.18,W*.18]),
             p('Cada accidente queda en un solo grupo de evaluación. Una fila representa a una persona en un accidente; pesid no permite seguir su identidad a lo largo de toda su vida. Comenzamos en 2017 por el cambio al sistema BAT. La exploración y las pruebas estadísticas usan 2017-2023. Los datos de 2026 cubren enero-septiembre y se reservan para la evaluación posterior.'),
             p('PRF presenta estos archivos como datos abiertos y reutilizables. Conservamos la atribución a la fuente. En data/fuentes.json guardamos sus enlaces, tamaños y huellas SHA-256, que permiten comprobar que seguimos usando los mismos archivos.'),
             p('https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf',True),p('https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes',True)]
    quality=[p('Los archivos originales usan punto y coma y codificación Latin-1; las salidas usan UTF-8. Unificamos mayúsculas, espacios y categorías con el mismo significado. Convertimos fechas y números a sus tipos correctos. También comprobamos identificadores y cantidad de filas antes y después de la unión. La bitácora registra cada decisión y cuántos casos afecta.'),
             p('Una edad cero no permite saber si se trata de un bebé o de un dato sin completar. Por eso la marcamos como faltante, igual que edades negativas o mayores de 110, sin borrar a la víctima. Revisamos años de fabricación imposibles y coordenadas fuera de límites razonables. No usamos cero como reemplazo automático de la información ausente.'),
             p('Conservamos las categorías desconocidas. LightGBM admite números faltantes; los modelos que necesitan completarlos aprenden ese reemplazo solo con entrenamiento. Que falte información puede depender de la víctima o de cómo se registró el accidente, por lo que no suponemos que esas ausencias ocurran totalmente al azar.'),
             p('El modelo final usa 31 características: edad, sexo, rol de la persona, vehículo, antigüedad, horario, ubicación y condiciones del accidente, entre otras. Las siete características añadidas describen los otros vehículos presentes. Para construirlas usamos todos los vehículos identificados antes de seleccionar las víctimas y contamos una sola vez a un vehículo con varios ocupantes. No usamos identificadores, cantidades de muertos o heridos ni la causa atribuida después de investigar el accidente como entradas del modelo principal.'),
             p('Revisamos los cambios de categorías entre años y no borramos un valor extremo solo por estar alejado de los demás si sigue siendo posible. No tenemos velocidad de impacto, casco, cinturón ni seguimiento clínico completo. Tampoco conocemos todos los viajes realizados. Por eso este estudio no estima la probabilidad de que una persona cualquiera tenga un accidente.')]
    describe=L.table(['Variable','Media','Mediana','SD','P5 / P95','Asimetría'],[[r['variable'],f(r['media'],2),f(r['mediana'],2),f(r['sd'],2),f(r['p5'],2)+' / '+f(r['p95'],2),f(r['asimetria'],2)] for r in readc('descriptivos_desarrollo.csv')],[W*.23,W*.13,W*.13,W*.13,W*.24,W*.14])
    phase1=[('Problema, pregunta y objetivos',problem),('Fuentes, claves y unidad de análisis',sources),('Preparación y calidad',quality),('Estadística descriptiva en desarrollo',[describe,p('La media es el promedio; la mediana es el valor central; el desvío estándar indica cuánto se dispersan los valores. P5 y P95 dejan entre ambos al 90 % central de los casos. Cuando hay valores extremos, la mediana ayuda a no depender solo del promedio. Los CSV incluyen además moda, percentiles, asimetría, curtosis, frecuencias y correlaciones de Pearson y Spearman.')])]
    phase1 += [(f'Gráfico {i+1}: '+F1_TITULOS[name],graph(name,f1['interpretaciones'])) for i,name in enumerate(f1['interpretaciones'])]
    conclusion1=[p('Ahora podemos estudiar conjuntamente información real de personas, vehículos y accidentes. Hay diferencias entre grupos, pero también mucha superposición de edades. Estos patrones no demuestran causas ni garantizan que una característica aislada alcance para predecir la gravedad.'),p('Exploramos 573.747 víctimas de 2017-2023. En los años posteriores revisamos cobertura y calidad, pero no los usamos para buscar los patrones de esta fase. La fase 1 muestra qué información tenemos y cómo se comporta; la capacidad predictiva se comprueba en la fase 3.'),p('Llevamos cuatro preguntas a la fase 2: si sexo y gravedad están relacionados, si las edades difieren, si cambia la proporción de fallecidos entre motos y otros vehículos, y si la noche se relaciona con la gravedad al considerar otras características. No elegimos variables únicamente porque una prueba dé un valor p pequeño.'),p('Los resultados corresponden a las víctimas registradas por PRF. Faltan casos que no se registraron, información de seguridad y seguimiento completo de fallecimientos posteriores. Las víctimas de un mismo accidente comparten condiciones. No podemos trasladar automáticamente los resultados a todo Brasil o a Paraguay.')]
    phase1 += [('Conclusión y puente a inferencia',conclusion1)]
    dictionary=readc('diccionario_final.csv')
    for i in range(0,len(dictionary),15):
        phase1 += [(f'Diccionario final: campos {i+1}-{min(i+15,len(dictionary))}',[L.table(['Campo','Significado / unidad','Tipo','Faltante %'],[[r['variable'],r['descripcion'],r['tipo'],f(r['porcentaje_faltante'],2)] for r in dictionary[i:i+15]],[W*.23,W*.48,W*.14,W*.15]),p('Los nombres de campos permiten ubicar las columnas en el código. Los diccionarios original y final completos están en output/tables/. Un id_veiculo igual a cero indica información ausente o no aplicable, no un vehículo real.',True)])]
    h=f2['contrastes']
    hypothesis=[p('H0 plantea igualdad o ausencia de asociación; H1 plantea una diferencia. Fijamos un nivel de significancia de 0,05 y usamos pruebas bilaterales, que permiten diferencias en ambas direcciones. Como hacemos cuatro contrastes, aplicamos Holm, una variante de Bonferroni, para reducir las diferencias encontradas solo por repetir pruebas. Cada intervalo del 95 % corresponde a su efecto por separado.')]
    for r in h:hypothesis += [L.sub(r['id']),p('H0: '+r['H0']+'. H1: '+r['H1']+'.'),p('Unidad / cobertura: '+r['alcance']+'.',True)]
    summarytests=[L.table(['Hip. / prueba','Efecto','IC 95 %','p Holm','Decisión'],[[r['id']+' / '+r['prueba'],r['efecto']+': '+f(r['valor_efecto']),f(r['IC95_bajo'])+' a '+f(r['IC95_alto']),pv(r['p_Holm']),r['decision']] for r in h],[W*.25,W*.28,W*.19,W*.12,W*.16]),p('El efecto describe la magnitud de la relación; el intervalo muestra su incertidumbre. Los estadísticos, grados de libertad y cantidades de casos están en contrastes_fase2.csv. Un valor p pequeño no mide el tamaño de la diferencia. Cuando el programa guarda p como cero por su límite numérico, lo presentamos como extremadamente pequeño, no como una probabilidad exactamente cero.',True)]
    summarytests += [L.table(['Prueba','Estadistico','Grados de libertad','Casos'],[[r['id'],f(r['estadistico']),'-' if r['gl'] is None else f(r['gl'],0),f(r['n'],0)] for r in h],[W*.18,W*.30,W*.30,W*.22])]
    inferdesign=[p('Mantenemos las reglas de limpieza y las uniones de la fase 1. La mejora frente al proyecto anterior es que usamos registros individuales reales. Conservamos las edades ausentes sin inventarlas y tenemos en cuenta que varias víctimas comparten un accidente. No inventamos una nueva devolución de la profesora.'),p('Para las tres primeras pruebas elegimos una víctima al azar por accidente, con semilla 42. Así evitamos contar a varios pasajeros como si fueran casos totalmente independientes. Esta selección da el mismo peso a cada accidente; no representa a todas las víctimas con el mismo peso.'),p(f"La muestra contiene {f(f2['n_muestra_una_victima_por_accidente'],0)} accidentes. H4 utiliza {f(f2['GLM']['n'],0)} víctimas con todas las variables necesarias. Ajustamos el cálculo de incertidumbre para los {f(f2['GLM']['accidentes'],0)} accidentes. Suponemos que accidentes distintos son aproximadamente independientes, aunque pueden compartir condiciones de tiempo y lugar."),p('Usamos cuatro tipos de pruebas: chi cuadrado para sexo, Mann-Whitney para edad, comparación de proporciones para vehículos y regresión logística para estudiar la noche considerando otras características. Las pruebas se eligen según el tipo de variable y sus supuestos; no aplicamos una prueba de normalidad al resultado binario herido/fallecido.')]
    b=f2['bootstrap']
    phase2=[('Correcciones y diseño inferencial',inferdesign),('Hipótesis nulas y alternativas',hypothesis),('Resultados y tamaños de efecto',summarytests),
            ('Verificación de supuestos',[L.image('f2_01_normalidad.png',width=W),p('Revisamos las edades con gráficos Q-Q y Shapiro-Wilk, usando hasta 5.000 casos por grupo. No encontramos normalidad, por eso usamos Mann-Whitney para comparar las distribuciones. Esa prueba no mide únicamente diferencias de medianas. Levene revisa la dispersión, aunque su igualdad no es un requisito de Mann-Whitney.'),p('Para chi cuadrado comprobamos que hubiera suficientes casos esperados. En la comparación de proporciones revisamos los recuentos de ambos resultados. La regresión terminó correctamente y ajustamos sus errores por accidente. Estos controles no eliminan todos los posibles sesgos del registro policial.')]),
            ('Bootstrap frente al intervalo clásico',[L.image('f2_02_bootstrap.png',width=W),p(f"Para la diferencia de letalidad moto menos otros, IC bootstrap: {pct(b['IC95_bootstrap'][0])} a {pct(b['IC95_bootstrap'][1])} puntos porcentuales; IC clásico: {pct(b['IC95_clasico'][0])} a {pct(b['IC95_clasico'][1])}. Bootstrap consiste en volver a tomar muestras con reemplazo de los resultados observados. Lo repetimos 5.000 veces por grupo, después de elegir una víctima por accidente. No añadimos personas al dataset ni entrenamos el modelo con esas remuestras."),p('La diferencia entre motos y otros vehículos es pequeña. Entre las víctimas seleccionadas hay alrededor de 5,32 % de fallecidos en motos y 5,68 % en otros vehículos. Esto no significa que viajar en moto sea más seguro: no tenemos la cantidad de viajes ni todos los accidentes, y los grupos pueden diferir en otros aspectos.')]),
            ('Asociación ajustada y límites',[L.table(['Variable','OR','IC 95 %','p'],[[r['variable'],f(r['OR']),f(r['OR_IC95_bajo'])+' a '+f(r['OR_IC95_alto']),pv(r['p'])] for r in readc('regresion_logistica_inferencial.csv')],[W*.4,W*.15,W*.3,W*.15]),p('La noche presenta un OR ajustado de aproximadamente 1,85 frente al pleno día. Consideramos edad, edad al cuadrado, sexo, moto, peatón, zona rural y año. OR compara la relación entre fallecidos y heridos: no significa que la probabilidad individual se multiplique directamente por 1,85. Pueden faltar otras variables importantes. Esta regresión estudia asociaciones; no es el modelo predictivo final.')]),
            ('Conclusión de la fase 2',[p('Las cuatro pruebas permiten rechazar H0 después de la corrección. Esto respalda la existencia de asociaciones bajo los supuestos usados, pero sus magnitudes son distintas. Sexo tiene una asociación pequeña; las edades se superponen; la diferencia por moto es pequeña; y la noche conserva una asociación al considerar otras variables.'),p('Los registros no son una muestra aleatoria de todos los usuarios del tránsito. Los intervalos y valores p no corrigen casos sin registrar ni garantizan que el resultado se repita en cualquier población. Con muchos casos, una diferencia pequeña puede ser estadísticamente detectable. Eso no implica que sirva mucho para predecir.'),p('En la fase 3 combinamos edad, sexo, vehículo, rol, ubicación, tiempo y condiciones del accidente. Excluimos las columnas que revelan el resultado y los identificadores. La selección se basa en su disponibilidad y sentido para el problema, además de los resultados estadísticos.')])]
    initial=readj('modelado/inicial/fase3_resultados.json')
    final=readj('modelado/final/resultados.json');selected=final['seleccionado']
    initial_rows=[r for r in read_csv_path(OUT/'modelado/inicial/metricas_prueba_2025.csv') if r['regla']=='F1_validacion' and r['familia'] in ['Logistica','Arbol','Bayes','LightGBM','Dummy']]
    final_rows=[r for r in final['metricas'] if r['regla']=='F1_validacion']
    design=[p('Nuestra tarea es una clasificación: estimamos fallecimiento registrado (1) frente a lesión leve o grave (0). Una fila corresponde a una persona en un accidente. El modelo parte de un accidente que ya ocurrió: no estima quién tendrá un accidente en su vida cotidiana. No recibe identificadores ni cantidades de muertos o heridos que le darían parte de la respuesta.'),
        p('Primero comparamos regresión logística, árbol, Naive Bayes y LightGBM, además de Dummy, con 24 características. Probamos 13 configuraciones en cortes temporales de 2021, 2022 y 2023. Después añadimos contexto de los vehículos y probamos ocho configuraciones de LightGBM, también con esos cortes. En cada caso entrenamos solo con años anteriores.'),
        p('Entrenamos con 2017-2023. Usamos enero-junio de 2024 para calibrar los porcentajes de riesgo y julio-diciembre para elegir desde qué porcentaje clasificar un caso como fallecido. Ese punto de decisión busca el mejor F1 de fallecidos en validación. Para elegir el modelo usamos AP media, que evalúa cómo se priorizan los fallecidos considerando las falsas alarmas. La elección quedó fijada antes de abrir 2026.'),
        p('Los resultados de 2025 ya eran conocidos cuando mejoramos el modelo, así que su comparación final es retrospectiva. La prueba posterior original fue enero-septiembre de 2026. Guardamos los protocolos y las decisiones de ese momento. Volver a ejecutar hoy los resultados conocidos no crea una nueva prueba independiente.'),
        p('Elegimos LightGBM con 31 características, 400 árboles, tasa de aprendizaje 0,04, máximo de 15 hojas, mínimo de 300 casos por hoja, regularización L2=25 y semilla 42. Estas restricciones ayudan a evitar reglas demasiado específicas del entrenamiento. Solo conservamos este modelo entrenado como opción final; las tablas y el código de comparación permiten justificar y repetir la elección.')]
    initial_comparison=[L.table(['Familia inicial','AP','AUC','Precisión','Recall','F1 macro'],[[r['familia'],f(r['AP']),f(r['ROC_AUC']),pct(r['precision']),pct(r['recall']),f(r['F1_macro'])] for r in initial_rows],[W*.25,W*.12,W*.13,W*.17,W*.16,W*.17]),
        p('Esta tabla es la comparación INICIAL con 24 características y las mismas 89.593 víctimas de 2025; no es el resultado final. La regresión logística combina características, el árbol aprende reglas, Naive Bayes usa probabilidades y LightGBM combina muchos árboles. Dummy responde siempre herido y sirve como referencia mínima.'),
        p('Consideramos distintos pesos para los fallecidos y distintas complejidades. El modelo final conservó la proporción natural, sin duplicar personas ni crear víctimas sintéticas. La validación y la prueba mantienen la proporción real. Dar más peso a una clase no garantiza que el modelo mejore.')]
    rank=read_csv_path(OUT/'modelado/final/ranking_CV.csv')
    search=[L.table(['Configuración','AP CV','AUC CV','Cortes mejores'],[[r['modelo'],f(r['AP_media']),f(r['AUC_media']),r['cortes_supera_referencia']+' / 3'] for r in rank],[W*.52,W*.16,W*.16,W*.16]),
        p('La configuración elegida fue Contexto_regularizado_natural. Mejoró a la referencia en los tres cortes de validación. Los nombres de esta tabla identifican configuraciones probadas, no proyectos diferentes para entregar. Las pruebas con marca y más detalle del trazado no quedaron en el ganador. Sus resultados completos siguen en CSV.'),*graph('01_busqueda_CV.png',g3)]
    metrics_final=[L.table(['Evaluación / modelo','AUC','AP','F1 macro','Precisión','Recall'],[[('2025 retrospectivo' if r['particion'].startswith('2025') else '2026 posterior')+' / '+('Final' if r['modelo']==selected else 'Referencia'),f(r['ROC_AUC']),f(r['AP']),f(r['F1_macro']),pct(r['precision']),pct(r['recall'])] for r in final_rows],[W*.35,W*.12,W*.12,W*.13,W*.14,W*.14]),
        p(f"La exactitud, o porcentaje total de aciertos, es {pct(chosen['accuracy'])}. La exactitud balanceada es {pct(chosen['balanced_accuracy'])} y el F1 de fallecidos es {f(chosen['F1_fallecido'])}. También calculamos Brier ({f(chosen['Brier'],4)}) y log loss ({f(chosen['log_loss'],4)}), que evalúan los porcentajes de riesgo: un valor menor es mejor."),
        p('La prueba final tiene 67.591 víctimas y 4.610 fallecidos. AUC evalúa si el modelo suele asignar mayor riesgo a fallecidos que a heridos. F1 macro evalúa la clasificación de ambos grupos con igual peso. Precisión indica cuántas alertas acierta; recall o detección indica cuántos fallecidos encuentra. AUC 0,845 no significa 84,5 % de aciertos. El punto de decisión elegido es 0,214245, alrededor del 21,4 % de riesgo estimado.'),*graph('02_comparacion_2026.png',g3)]
    errors=readc('errores_mayor_confianza_modelo_final.csv')
    error_section=[L.table(['Error','Edad','Rol','Vehículo','P(fallecido)'],[[r['tipo_error'],r['idade'],r['tipo_envolvido'],r['tipo_veiculo'],f(r[selected])] for r in errors[:6]],[W*.12,W*.12,W*.23,W*.30,W*.23]),
        p('Son errores cometidos aunque el modelo asignaba un riesgo alto o bajo con mucha confianza. Los revisamos para reconocer sus límites, no para explicar qué causó el resultado. Las tablas completas incluyen veinte casos y evaluaciones por sexo, edad, rol, vehículo y ubicación. No cambiamos decisiones por grupo mirando la prueba.'),
        L.table(['Cambio final - referencia','IC 95% inferior','IC 95% superior'],[[r['metrica'],f(r['IC95_bajo'],4),f(r['IC95_alto'],4)] for r in final['intervalos_delta']],[W*.5,W*.25,W*.25]),
        p('Los intervalos se obtuvieron repitiendo 300 veces la selección de accidentes completos con reemplazo. Comparamos ambos modelos sobre las mismas víctimas. Los cinco cambios son positivos en esos intervalos, pero eso no elimina posibles problemas del registro o diferencias entre lugares y años.')]
    limits=[p('La respuesta final es que combinar información de la persona, el vehículo y el accidente permite distinguir heridos y fallecidos mejor que referencias sencillas. El mejor modelo fue LightGBM con 31 características: AUC 0,845 y F1 macro 0,675 en 2026. Sobre las mismas víctimas, la referencia obtuvo 0,799 y 0,647. Detectamos 132 fallecidos más y generamos 717 falsas alarmas menos.'),
        p('El modelo todavía clasifica como heridos a 2.657 de los 4.610 fallecidos y genera 3.277 falsas alarmas. Con la decisión principal detecta cerca de 42 de cada 100 fallecidos. Si bajamos la exigencia podemos detectar más, pero aumentan mucho las falsas alarmas. No hay una decisión perfecta para todos los usos.'),
        p('El rendimiento es mejor en entrenamiento que en datos posteriores: AP es 0,456, frente a 0,358 en validación y 0,352 en 2026. Parte de lo aprendido no se mantiene fuera del entrenamiento. También faltan velocidad de impacto, casco, cinturón y seguimiento clínico completo. El modelo no está validado para decisiones médicas ni para aplicarlo automáticamente a Paraguay.'),
        p('Usamos IA como apoyo en programación, análisis y redacción. El grupo debe revisar y comprender el trabajo y asumir sus decisiones antes de presentarlo. Los legajos y las contribuciones de cada integrante deben completarse por el grupo; no inventamos aprobaciones docentes ni participación individual.')]
    phase3=[('Qué predecimos y cómo dividimos los datos',design),('Comparación inicial de familias: 24 variables',initial_comparison),('Cómo elegimos LightGBM',search),('Resultado final: modelo de 31 variables',metrics_final)]
    phase3 += [(title,graph(name,g3)) for title,name in [('Curvas ROC y precisión-recall','03_curvas_2026.png'),('Aciertos y errores del modelo final','04_confusion_2026.png'),('¿Aprendió o memorizó los datos?','f3_05_generalizacion.png'),('Calibración: ajustar los porcentajes de riesgo','f3_06_calibracion.png'),('Interpretación y relación con inferencia','f3_07_importancia.png'),('Heridos, fallecidos y punto de decisión','f3_08_umbrales.png')]]
    phase3 += [('Casos mal predichos e incertidumbre',error_section),('Conclusión general y límites',limits)]
    build('Comprension_del_problema.pdf','Comprensión del problema',[('Pregunta y objetivos',problem),('Alcance y método previsto',[*sources[:2],*quality[-2:],p('El objetivo es distinguir heridos y fallecidos registrados en Brasil, no pronosticar la cantidad de accidentes del próximo año. Las tres fases trabajan con la misma base individual y sus decisiones deben poder explicarse durante la exposición.')])],index=False)
    build('Fase_1_Preparacion_y_EDA.pdf','Fase 1 - Preparación y exploración',phase1)
    build('Fase_2_Inferencia.pdf','Fase 2 - Inferencia estadística',phase2)
    build('Fase_3_Modelado_y_Evaluacion.pdf','Fase 3 - Modelado y evaluación',phase3)
    integrated=[('Problema y objetivos',problem),('Fuentes y construcción',sources),('Calidad de los datos',quality),('Desbalance y edad',graph('f1_01_clases.png',f1['interpretaciones'])+graph('f1_02_histograma_edad.png',f1['interpretaciones'])),('Cambios temporales',graph('f1_04_serie_temporal.png',f1['interpretaciones'])),('Inferencia: diseño',inferdesign),('Inferencia: hipótesis',hypothesis),('Inferencia: resultados',summarytests),('Inferencia: conclusión',phase2[-1][1]),*phase3]
    build('Informe_Integrador.pdf','Informe integrador - Tres fases',integrated)


if __name__=='__main__':main()
