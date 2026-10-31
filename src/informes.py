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
    canvas.drawString(1.6*cm,.8*cm,'PRF Brasil | Gravedad de víctimas | 31/10/2026')
    canvas.drawRightString(A4[0]-1.6*cm,.8*cm,f'Página {doc.page}');canvas.restoreState()


def cover(label):
    return [Spacer(1,1.3*cm),p('CIENCIA DE DATOS - PROYECTO INTEGRADOR',True),Spacer(1,.5*cm),
            Paragraph(label,L.STYLES['TitleProject']),
            L.heading('Factores asociados a la gravedad de las víctimas en siniestros de tránsito'),
            p('Carreteras federales de Brasil - PRF - Estudio 2017-2025; validación enero-septiembre 2026'),Spacer(1,.7*cm),
            L.sub('Integrantes'),p('Alan Alcaraz · Leandro Ferreira · Jorge Rios'),
            p('Legajos pendientes de completar por el grupo.',True),L.sub('Qué contiene este material'),
            p('Resultados calculados con registros individuales y evaluación temporal. Borrador de apoyo académico con asistencia de IA: el equipo debe revisar, comprender y asumir las decisiones metodológicas y las interpretaciones antes de presentar.'),
            p('El modelo estima un desenlace registrado entre víctimas lesionadas atendidas por PRF. No predice quién sufrirá un accidente, no establece causas y no está validado para uso médico ni para Paraguay.'),
            p('Fecha: 31 de octubre de 2026.',True)]


def build(name,label,sections,index=True):
    story=cover(label)
    if index:
        story += [PageBreak(),L.heading('Índice de secciones')]
        story += [p(f'{i+1}. {title}') for i,(title,_) in enumerate(sections)]
    for title,content in sections:story += [PageBreak(),L.heading(title),*content]
    target=OUT/'reports'/name
    SimpleDocTemplate(str(target),pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=1.5*cm,bottomMargin=1.6*cm,title=label,author='Material de apoyo con asistencia de IA').build(story,onFirstPage=footer,onLaterPages=footer)
    print(target)


def main():
    a=readj('auditoria_preparacion.json');f1=readj('fase1_resultados.json');f2=readj('fase2_resultados.json');f3=readj('fase3_resultados.json');g3=readj('interpretaciones_fase3.json')
    proto=json.loads((ROOT/'protocolo.json').read_text(encoding='utf8'))
    chosen=f3['prueba'];results=[]
    def graph(name,texts):return [L.image(name,width=W*.92),p(texts[name],True)]
    objectives=['Construir una tabla individual de víctimas con sus características personales, vehiculares y del siniestro mediante claves reales y controles de unión.',
                'Evaluar la calidad, las ausencias y los patrones de edad, sexo, vehículo, lugar y tiempo en 2017-2023.',
                'Contrastar cuatro hipótesis con tamaños de efecto, intervalos y corrección de multiplicidad, considerando víctimas del mismo accidente.',
                'Comparar modelos de varias familias con validación temporal, calibración y tratamiento explícito del desbalance.',
                'Medir en 2025 el aporte de las nuevas variables frente a sexo/edad y referencias triviales, comunicando errores y límites.']
    problem=[L.sub('Contexto y relevancia'),p('PRF publica registros administrativos de siniestros en carreteras federales y sus involucrados. Comprender qué características distinguen lesiones no fatales y fallecimientos registrados permite formular hipótesis y evaluar predicción académica. El trabajo anterior de Paraguay solo disponía de totales agrupados: expandirlos no creaba información individual.'),
             L.sub('Pregunta principal'),p(proto['pregunta']),L.sub('Objetivo general'),p('Analizar asociaciones entre características individuales y del siniestro con el desenlace y evaluar la capacidad de modelos para clasificar víctimas heridas o fallecidas registradas, mediante un procedimiento reproducible y sin filtraciones del resultado.'),L.sub('Objetivos específicos'),*L.bullets(objectives)]
    sources=[p('Se conservan 20 ZIP CSV y 2 diccionarios PDF oficiales del corte descargado el 31/10/2026. En 2017-2025 hay 632.713 accidentes distintos y 1.654.197 filas en personas; el corte 2026 agrega 54.895 ocurrencias y 148.868 filas en personas. Se descartaron del objetivo ilesos y desenlaces desconocidos; 144.628 filas con pesid=0 de 2017-2025 no se cuentan como individuos identificados.'),
             p('La base principal 2017-2025 tiene 754.098 víctimas con desenlace válido: 703.273 heridas y 50.825 fallecidas. El corte posterior 2026 agrega 67.591 víctimas (4.610 fallecidas). El dataset limpio consolidado contiene 821.689 participaciones. La unión personas.id a accidentes.id es muchos a uno, sin expansión ni víctimas sin pareja. Las claves de víctimas son únicas; los datos de vehículo ya están asociados en personas. No se inventó una tercera fuente independiente.'),
             L.table(['Partición','Víctimas','Fallecidos','Accidentes'],[[r['particion'],f(r['filas'],0),f(r['fallecidos'],0),f(r['accidentes'],0)] for r in readc('particiones.csv')],[W*.46,W*.18,W*.18,W*.18]),
             p('No hay accidentes compartidos entre particiones. pesid identifica una participación, no identidad civil longitudinal. Se inicia en 2017 por el cambio al sistema BAT. El corte 2026 se utiliza exclusivamente como validación posterior: no es un año completo y no integra la exploración o inferencia.'),
             p('Fuente y licencia de datos: PRF los presenta como datos abiertos reutilizables. Se conserva atribución; la licencia del sitio web no se confunde con una licencia adicional de cada CSV. URLs exactas, tamaños y SHA-256 están en data/fuentes.json.'),
             p('https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf',True),p('https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes',True)]
    quality=[p('El CSV original usa Latin-1 y punto y coma; las salidas usan UTF-8. Se normalizan mayúsculas, espacios y acentos de categorías, conservando la semántica. Se verifican hashes, claves, fechas y cardinalidad de la unión. La bitácora registra afectados por regla y por año.'),
             p('Edad cero se considera ambigua y se trata como faltante sin eliminar la víctima, al igual que edades negativas o mayores de 110. Se invalida año de vehículo cero o posterior al siniestro y se calcula antigüedad. Coordenadas fuera de límites geográficos amplios y posiciones imposibles se conservan como ausencia, no se imputan como cero.'),
             p('Las categorías desconocidas se conservan. Medianas, escalado, categorías y discretización se aprenden dentro de cada entrenamiento. Los faltantes pueden depender de gravedad, rol y calidad de registro; no se presume mecanismo completamente aleatorio.'),
             p('El modelo final usa 31 predictores. Los 24 iniciales incluyen edad, antigüedad de vehículo, hora y ciclos, ubicación, sexo, rol, tipo de vehículo, UF, BR, municipio, tipo de evento, fase del día, sentido, clima, calzada, trazado, suelo y día semanal. Se agregan seis cantidades de contexto vehicular y la familia del único otro vehículo identificado. El contexto se obtiene de TODOS los vehículos antes de seleccionar víctimas, incluidos ilesos y filas sin persona, deduplicando claves positivas. Se excluyen IDs, desenlace, conteos de víctimas y atribución posterior de causa.'),
             p('Columnas iguales entre años no garantizan categorías idénticas: las causas y trazados cambian. No se borra un extremo plausible solo por exceder un umbral IQR. Falta exposición por viaje, velocidad previa, casco/cinturón y atención posterior; no se estima riesgo de accidente por usuario.')]
    describe=L.table(['Variable','Media','Mediana','SD','P5 / P95','Asimetría'],[[r['variable'],f(r['media'],2),f(r['mediana'],2),f(r['sd'],2),f(r['p5'],2)+' / '+f(r['p95'],2),f(r['asimetria'],2)] for r in readc('descriptivos_desarrollo.csv')],[W*.23,W*.13,W*.13,W*.13,W*.24,W*.14])
    phase1=[('Problema, pregunta y objetivos',problem),('Fuentes, claves y unidad de análisis',sources),('Preparación y calidad',quality),('Estadística descriptiva en desarrollo',[describe,p('El anexo CSV añade moda, CV, IQR, mínimo, máximo, percentiles y curtosis. Las distribuciones asimétricas requieren acompañar medias con medianas y dispersión. Los IDs no son medidas sustantivas. Las matrices Pearson/Spearman y las contingencias absolutas y por fila/columna se conservan como CSV.')])]
    phase1 += [(f'Exploración {i+1}: '+name.split('_',2)[-1].replace('.png','').replace('_',' '),graph(name,f1['interpretaciones'])) for i,name in enumerate(f1['interpretaciones'])]
    conclusion1=[p('La información ya permite analizar conjuntamente características de personas, vehículos y siniestros; las tablas comparten claves reales. Se observan desbalance marcado, superposición de edades y diferencias entre tipos de evento y vehículo. Estas asociaciones descriptivas no prueban causas ni aseguran capacidad predictiva.'),p('La exploración utiliza únicamente 573.747 víctimas de 2017-2023. El perfilado previo de los años posteriores se limitó a auditar cobertura y calidad; no es un estudio externo completamente ciego. La respuesta parcial es que los datos permiten investigar la pregunta, mientras que la utilidad para predecir debe medirse separadamente.'),p('La fase 2 lleva cuatro hipótesis: sexo y desenlace; distribución de edad; letalidad de usuarios de moto frente a otros vehículos; nocturnidad condicionada a otros factores. En fase 3 se conservan predictores por plausibilidad y disponibilidad, sin hacer selección automática por valores p.'),p('Las limitaciones son cobertura institucional, desenlace registrado sin seguimiento a 30 días, falta de exposición y datos de seguridad, ausencias informativas, cambios de registro y dependencia entre víctimas. Los resultados no representan todos los accidentes de Brasil y no se trasladan directamente a Paraguay.')]
    phase1 += [('Conclusión y puente a inferencia',conclusion1)]
    dictionary=readc('diccionario_final.csv')
    for i in range(0,len(dictionary),15):
        phase1 += [(f'Diccionario final: campos {i+1}-{min(i+15,len(dictionary))}',[L.table(['Campo','Significado / unidad','Tipo','Faltante %'],[[r['variable'],r['descripcion'],r['tipo'],f(r['porcentaje_faltante'],2)] for r in dictionary[i:i+15]],[W*.23,W*.48,W*.14,W*.15]),p('Categorías y rangos observados, tipos, trazabilidad y perfil original se acompañan en las tablas y en los diccionarios oficiales. Cero de id_veiculo es ausencia/no aplicable aunque sea numérico.',True)])]
    h=f2['contrastes']
    hypothesis=[p('Alfa 0,05 y familia de cuatro contrastes declarados antes del cálculo, con corrección de Holm. Pruebas bilaterales; intervalos del 95 % marginales, no simultáneos. No se afirma aceptación de H0 ni se deduce causalidad.')]
    for r in h:hypothesis += [L.sub(r['id']),p('H0: '+r['H0']+'. H1: '+r['H1']+'.'),p('Unidad / cobertura: '+r['alcance']+'.',True)]
    summarytests=[L.table(['Hip. / prueba','Efecto','IC 95 %','p Holm','Decisión'],[[r['id']+' / '+r['prueba'],r['efecto']+': '+f(r['valor_efecto']),f(r['IC95_bajo'])+' a '+f(r['IC95_alto']),pv(r['p_Holm']),r['decision']] for r in h],[W*.25,W*.28,W*.19,W*.12,W*.16]),p('Estadísticos, grados de libertad cuando corresponden y tamaños muestrales se incluyen en contrastes_fase2.csv. Valores p guardados como cero corresponden a subdesbordamiento numérico y se comunican como muy pequeños, no probabilidad exactamente cero.',True)]
    inferdesign=[p('Correcciones y continuidad con la fase 1: se usan fichas reales, se conserva edad ausente sin inventar edades, se enlazan vehículo y accidente por claves y se considera dependencia entre víctimas. No se atribuye al docente una devolución nueva que no fue proporcionada.'),p('H1-H3 usan una víctima elegida al azar por accidente, con semilla 42 y selección independiente del desenlace. Esto evita tratar pasajeros del mismo siniestro como muestras independientes, pero cambia la ponderación: representa una víctima aleatoria por accidente con lesionados, no cada víctima del total con igual peso.'),p(f"La muestra contiene {f(f2['n_muestra_una_victima_por_accidente'],0)} accidentes. H4 utiliza {f(f2['GLM']['n'],0)} víctimas con covariables completas y errores robustos agrupados por {f(f2['GLM']['accidentes'],0)} accidentes. Se requiere independencia aproximada entre accidentes; puede quedar dependencia temporal y geográfica."),p('Se cubren cuatro familias: chi cuadrado de independencia, comparación de rangos Mann-Whitney, diferencia de proporciones y regresión binomial ajustada. No se fuerzan pruebas de normalidad sobre una respuesta binaria.')]
    b=f2['bootstrap']
    phase2=[('Correcciones y diseño inferencial',inferdesign),('Hipótesis nulas y alternativas',hypothesis),('Resultados y tamaños de efecto',summarytests),
            ('Verificación de supuestos',[L.image('f2_01_normalidad.png',width=W),p('Q-Q sobre submuestras de edad; Shapiro en hasta 5.000 por grupo rechaza normalidad. Levene evalúa dispersión, sin ser un requisito de Mann-Whitney. La prueba de rangos compara distribuciones, no se interpreta exclusivamente como prueba de medianas. Las tablas de supuestos conservan valores p y recuentos esperados.'),p('H1 tiene frecuencias esperadas suficientes. H3 tiene suficientes fallecidos y no fallecidos por grupo. En H4 se verifican convergencia y rango de diseño completo; se usa sandwich agrupado. Ninguna de estas comprobaciones garantiza representatividad o elimina confusión.')]),
            ('Bootstrap frente al intervalo clásico',[L.image('f2_02_bootstrap.png',width=W),p(f"Para la diferencia de letalidad moto menos otros, IC bootstrap: {pct(b['IC95_bootstrap'][0])} a {pct(b['IC95_bootstrap'][1])} puntos porcentuales; IC clásico: {pct(b['IC95_clasico'][0])} a {pct(b['IC95_clasico'][1])}. Se hicieron 5.000 remuestras empíricas Bernoulli por grupo, con una víctima por accidente."),p('La diferencia es pequeña y negativa en esta población condicionada a lesión registrada. No significa que usar moto sea más seguro por viaje. Se excluyen ilesos, hay diferentes tipos de siniestro y otros confusores; el denominador es decisivo.')]),
            ('Asociación ajustada y límites',[L.table(['Variable','OR','IC 95 %','p'],[[r['variable'],f(r['OR']),f(r['OR_IC95_bajo'])+' a '+f(r['OR_IC95_alto']),pv(r['p'])] for r in readc('regresion_logistica_inferencial.csv')],[W*.4,W*.15,W*.3,W*.15]),p('Noche frente a pleno día tiene OR ajustado aproximadamente 1,85. Se controla edad cuadrática, sexo, usuario de moto, peatón, ruralidad y tendencia anual. OR es razón de odds, no multiplicador directo de probabilidades; pueden faltar confusores y las ausencias pueden seleccionar casos.')]),
            ('Conclusión de la fase 2',[p('Los cuatro contrastes rechazan sus hipótesis nulas con Holm, pero los efectos no tienen la misma magnitud. Sexo muestra asociación pequeña; edad difiere con superposición; la diferencia de usuarios de moto es pequeña y depende del denominador; nocturnidad conserva asociación condicional en el GLM.'),p('Los registros no provienen de muestreo probabilístico y no permiten extrapolar a toda circulación vial. Los intervalos y valores p dependen de supuestos y no capturan subregistro. Grandes cantidades hacen detectable una diferencia pequeña. La clasificación posterior debe evaluar utilidad fuera del entrenamiento, no usar significancia como sinónimo de predicción.'),p('Se llevan edad, sexo, vehículo, rol, entorno y tiempo al modelado junto con localización y condiciones del evento. Se excluyen las variables que contienen el resultado, los IDs y la atribución posterior de causa; no se hacen nuevos contrastes hasta encontrar resultados favorables.')])]
    initial=readj('modelado/inicial/fase3_resultados.json')
    final=readj('modelado/final/resultados.json');selected=final['seleccionado']
    initial_rows=[r for r in read_csv_path(OUT/'modelado/inicial/metricas_prueba_2025.csv') if r['regla']=='F1_validacion' and r['familia'] in ['Logistica','Arbol','Bayes','LightGBM','Dummy']]
    final_rows=[r for r in final['metricas'] if r['regla']=='F1_validacion']
    design=[p('La tarea clasifica fallecimiento registrado (1) frente a lesiones leves/graves (0). La unidad es una participación real; las víctimas de un mismo accidente permanecen juntas. No se usan IDs, gravedad, conteos de muertos/heridos o atribución posterior de causa para predecir.'),
        p('El proceso tiene dos etapas registradas. Primero se compararon logística, Bayes categórico, árbol, LightGBM y Dummy con 24 variables: 13 configuraciones y 39 ajustes en cortes 2021, 2022 y 2023, entrenando solo con años anteriores. Después se revis? preparación/contexto y se probaron ocho configuraciones de LightGBM (24 ajustes), sin ampliar la grilla según prueba.'),
        p('Ambas etapas usan entrenamiento 2017-2023; enero-junio 2024 calibra sigmoid y julio-diciembre 2024 fija el umbral para F1 de fallecidos. La selección usa AP media de validación. La ronda final exige mejora media y en al menos dos cortes. La elección y los umbrales se congelaron antes de abrir 2026.'),
        p('2025 ya había sido evaluado al diseñar la mejora y su comparación final es retrospectiva. La nueva prueba original fue enero-septiembre 2026. Los protocolos y congelamientos originales se conservan como evidencia. Reejecutar ahora los resultados conocidos no constituye una prueba ciega nueva.'),
        p('Se conserva un único modelo serializado para uso: LightGBM natural, 31 predictores, 400 árboles, tasa 0,04, 15 hojas, mínimo 300 casos por hoja, L2=25 y semilla 42. Las tablas y el código de alternativas permanecen porque comparar familias es obligatorio, no como otras entregas o modelos para elegir.')]
    initial_comparison=[L.table(['Familia inicial','AP','AUC','Precisión','Recall','F1 macro'],[[r['familia'],f(r['AP']),f(r['ROC_AUC']),pct(r['precision']),pct(r['recall']),f(r['F1_macro'])] for r in initial_rows],[W*.25,W*.12,W*.13,W*.17,W*.16,W*.17]),
        p('Comparación inicial sobre las mismas 89.593 víctimas de 2025, con 24 predictores por familia. Son resultados de una etapa anterior, no rivales entrenados con las 31 entradas finales. Se cubren logística, árbol, Bayes y boosting; el modelo final se compara directamente contra la referencia LightGBM de 24 variables con idénticos años de ajuste.'),
        p('La búsqueda inicial compar? pesos naturales/balanceados y distintas complejidades; la final añadió contexto y regularización. No se fuerza una proporción 50/50 ni se balancea validación/prueba. La opción elegida aprende con prevalencia natural y un umbral calibrado con otro período. Los pesos no garantizan mejor ordenamiento.')]
    rank=read_csv_path(OUT/'modelado/final/ranking_CV.csv')
    search=[L.table(['Configuración','AP CV','AUC CV','Cortes mejores'],[[r['modelo'],f(r['AP_media']),f(r['AUC_media']),r['cortes_supera_referencia']+' / 3'] for r in rank],[W*.52,W*.16,W*.16,W*.16]),
        p('La mayor AP media correspondi? a Contexto_regularizado_natural, que mejora la referencia en tres cortes. Las variantes con marca aproximada y trazado descompuesto no quedaron en el ganador. La tabla completa se conserva, sin modelos serializados descartados.'),*graph('01_busqueda_CV.png',g3)]
    metrics_final=[L.table(['Evaluación / modelo','AUC','AP','F1 macro','Precisión','Recall'],[[('2025 retrospectivo' if r['particion'].startswith('2025') else '2026 posterior')+' / '+('Final' if r['modelo']==selected else 'Referencia'),f(r['ROC_AUC']),f(r['AP']),f(r['F1_macro']),pct(r['precision']),pct(r['recall'])] for r in final_rows],[W*.35,W*.12,W*.12,W*.13,W*.14,W*.14]),
        p(f"El modelo final obtiene exactitud {pct(chosen['accuracy'])}, exactitud balanceada {pct(chosen['balanced_accuracy'])}, F1 de fallecidos {f(chosen['F1_fallecido'])}, Brier {f(chosen['Brier'],4)} y log loss {f(chosen['log_loss'],4)}."),
        p('La nueva prueba tiene 67.591 víctimas y 4.610 fallecidos. AUC 0,845 no es 84,5% de aciertos ni de fallecidos detectados. El umbral principal es 0,214245. Una referencia siempre herido alcanza exactitud cercana al 93% sin detectar fallecidos; no se usa exactitud como criterio principal.'),*graph('02_comparacion_2026.png',g3)]
    errors=readc('errores_mayor_confianza_modelo_final.csv')
    error_section=[L.table(['Error','Edad','Rol','Vehículo','P(fallecido)'],[[r['tipo_error'],r['idade'],r['tipo_envolvido'],r['tipo_veiculo'],f(r[selected])] for r in errors[:6]],[W*.12,W*.12,W*.23,W*.30,W*.23]),
        p('Son ejemplos con alta confianza equivocada, no una explicación causal de por qu? ocurri? el desenlace. La tabla completa de veinte casos y las métricas por sexo, edad, rol, vehículo, contexto y UF se acompañan en CSV. La prevalencia y el tamaño por grupo condicionan las diferencias; no se cambian umbrales por grupo mirando prueba.'),
        L.table(['Cambio final - referencia','IC 95% inferior','IC 95% superior'],[[r['metrica'],f(r['IC95_bajo'],4),f(r['IC95_alto'],4)] for r in final['intervalos_delta']],[W*.5,W*.25,W*.25]),
        p('Los IC provienen de 300 remuestras pareadas de accidentes completos y son marginales. Los cinco cambios analizados son positivos en esos intervalos; no incluyen todos los sesgos de cobertura o dependencia temporal/geográfica.')]
    limits=[p('Respuesta consolidada: las características del siniestro y del contexto vehicular permiten clasificar el desenlace mejor que referencias sencillas. Sobre las mismas víctimas de 2026, AUC sube de 0,799 a 0,845 y F1 macro de 0,647 a 0,675. Se detectan 132 fallecidos más y se generan 717 falsas alarmas menos con reglas fijadas anteriormente.'),
        p('El modelo final aún omite 2.657 de 4.610 fallecidos y genera 3.277 falsas alarmas. Al bajar el umbral se alcanza recall 80,95% con precisión 17,03%. No existe una única regla óptima sin definir costos de errores; no se presenta el modelo como una solución clínica validada.'),
        p('El optimismo de entrenamiento se mantiene: AP 0,456 frente a 0,358 en validación y 0,352 en 2026. Faltan velocidad de impacto, elementos de seguridad, exposición y seguimiento clínico. Las variables se observan en un siniestro ya ocurrido; no predicen riesgo previo de accidentarse. No se generaliza automáticamente a todo Brasil ni Paraguay.'),
        p('Se declara asistencia de IA en programación, análisis y redacción. El grupo debe revisar y comprender el material y asumir sus decisiones e interpretaciones. Los legajos y las contribuciones personales/historial del grupo deben completarse por los integrantes; no se inventan aprobaciones o autorías.')]
    phase3=[('Diseño experimental y correcciones',design),('Comparación de familias y línea base',initial_comparison),('Búsqueda temporal de la opción final',search),('Evaluación posterior y comparación',metrics_final)]
    phase3 += [(title,graph(name,g3)) for title,name in [('Curvas ROC y precisión-recall','03_curvas_2026.png'),('Aciertos y errores del modelo final','04_confusion_2026.png'),('Sobreajuste y generalización','f3_05_generalizacion.png'),('Calibración','f3_06_calibracion.png'),('Interpretación y relación con inferencia','f3_07_importancia.png'),('Desbalance y umbrales','f3_08_umbrales.png')]]
    phase3 += [('Casos mal predichos e incertidumbre',error_section),('Conclusión general y límites',limits)]
    build('Comprension_del_problema.pdf','Comprensión del problema',[('Pregunta y objetivos',problem),('Alcance y método previsto',[*sources[:2],*quality[-2:],p('La evaluación se refiere a víctimas de Brasil; cambiar el país exige actualizar título, contexto y alcance. Las fases son acumulativas sobre el mismo dataset individual y las decisiones deben ser defendidas por el grupo.')])],index=False)
    build('Fase_1_Preparacion_y_EDA.pdf','Fase 1 - Preparación y exploración',phase1)
    build('Fase_2_Inferencia.pdf','Fase 2 - Inferencia estadística',phase2)
    build('Fase_3_Modelado_y_Evaluacion.pdf','Fase 3 - Modelado y evaluación',phase3)
    integrated=[('Problema y objetivos',problem),('Fuentes y construcción',sources),('Calidad de los datos',quality),('Desbalance y edad',graph('f1_01_clases.png',f1['interpretaciones'])+graph('f1_02_histograma_edad.png',f1['interpretaciones'])),('Cambios temporales',graph('f1_04_serie_temporal.png',f1['interpretaciones'])),('Inferencia: diseño',inferdesign),('Inferencia: hipótesis',hypothesis),('Inferencia: resultados',summarytests),('Inferencia: conclusión',phase2[-1][1]),*phase3]
    build('Informe_Integrador.pdf','Informe integrador - Tres fases',integrated)


if __name__=='__main__':main()
