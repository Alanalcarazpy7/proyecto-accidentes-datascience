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
            p('Carreteras federales de Brasil - PRF - Período 2017-2025'),Spacer(1,.7*cm),
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
    chosen=f3['prueba'];results=[r for r in readc('metricas_prueba_2025.csv') if r['regla']=='F1_validacion']
    def graph(name,texts):return [L.image(name,width=W*.92),p(texts[name],True)]
    objectives=['Construir una tabla individual de víctimas con sus características personales, vehiculares y del siniestro mediante claves reales y controles de unión.',
                'Evaluar la calidad, las ausencias y los patrones de edad, sexo, vehículo, lugar y tiempo en 2017-2023.',
                'Contrastar cuatro hipótesis con tamaños de efecto, intervalos y corrección de multiplicidad, considerando víctimas del mismo accidente.',
                'Comparar modelos de varias familias con validación temporal, calibración y tratamiento explícito del desbalance.',
                'Medir en 2025 el aporte de las nuevas variables frente a sexo/edad y referencias triviales, comunicando errores y límites.']
    problem=[L.sub('Contexto y relevancia'),p('PRF publica registros administrativos de siniestros en carreteras federales y sus involucrados. Comprender qué características distinguen lesiones no fatales y fallecimientos registrados permite formular hipótesis y evaluar predicción académica. El trabajo anterior de Paraguay solo disponía de totales agrupados: expandirlos no creaba información individual.'),
             L.sub('Pregunta principal'),p(proto['pregunta']),L.sub('Objetivo general'),p('Analizar asociaciones entre características individuales y del siniestro con el desenlace y evaluar la capacidad de modelos para clasificar víctimas heridas o fallecidas registradas, mediante un procedimiento reproducible y sin filtraciones del resultado.'),L.sub('Objetivos específicos'),*L.bullets(objectives)]
    sources=[p('Se descargaron 18 ZIP CSV y 2 diccionarios PDF el 31/10/2026. Los archivos contienen 632.713 accidentes distintos y 1.654.197 filas en la exportación de personas. Se descartaron del objetivo ilesos y desenlaces desconocidos; 144.628 filas con pesid=0 no se cuentan como individuos identificados.'),
             p('Se conservan 754.098 víctimas con desenlace válido: 703.273 heridas y 50.825 fallecidas. La unión personas.id a accidentes.id es muchos a uno, sin expansión ni víctimas sin pareja. Las claves de víctimas son únicas; los datos de vehículo ya están asociados en personas. No se inventó una tercera fuente independiente.'),
             L.table(['Partición','Víctimas','Fallecidos','Accidentes'],[[r['particion'],f(r['filas'],0),f(r['fallecidos'],0),f(r['accidentes'],0)] for r in readc('particiones.csv')],[W*.46,W*.18,W*.18,W*.18]),
             p('No hay accidentes compartidos entre particiones. pesid identifica una participación, no identidad civil longitudinal. Se inicia en 2017 por el cambio al sistema BAT y se excluye 2026 por ser un año en curso.'),
             p('Fuente y licencia de datos: PRF los presenta como datos abiertos reutilizables. Se conserva atribución; la licencia del sitio web no se confunde con una licencia adicional de cada CSV. URLs exactas, tamaños y SHA-256 están en descargas_prf.json.'),
             p('https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf',True),p('https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes',True)]
    quality=[p('El CSV original usa Latin-1 y punto y coma; las salidas usan UTF-8. Se normalizan mayúsculas, espacios y acentos de categorías, conservando la semántica. Se verifican hashes, claves, fechas y cardinalidad de la unión. La bitácora registra afectados por regla y por año.'),
             p('Edad cero se considera ambigua y se trata como faltante sin eliminar la víctima, al igual que edades negativas o mayores de 110. Se invalida año de vehículo cero o posterior al siniestro y se calcula antigüedad. Coordenadas fuera de límites geográficos amplios y posiciones imposibles se conservan como ausencia, no se imputan como cero.'),
             p('Las categorías desconocidas se conservan. Medianas, escalado, categorías y discretización se aprenden dentro de cada entrenamiento. Los faltantes pueden depender de gravedad, rol y calidad de registro; no se presume mecanismo completamente aleatorio.'),
             p('Se obtienen 24 predictores: edad, antigüedad de vehículo, hora y ciclos horarios/mensuales, ubicación, sexo, rol, tipo de vehículo, UF, BR, municipio, tipo de evento, fase del día, sentido, clima, calzada, trazado, suelo y día semanal. IDs y campos que revelan gravedad se excluyen; causa principal también se excluye por atribución retrospectiva.'),
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
    inferdesign=[p('Correcciones respecto del proyecto anterior: se usan fichas reales, se conserva edad ausente sin inventar edades, se enlazan vehículo y accidente por claves y se considera dependencia entre víctimas. No se atribuye al docente una devolución nueva que no fue proporcionada.'),p('H1-H3 usan una víctima elegida al azar por accidente, con semilla 42 y selección independiente del desenlace. Esto evita tratar pasajeros del mismo siniestro como muestras independientes, pero cambia la ponderación: representa una víctima aleatoria por accidente con lesionados, no cada víctima del total con igual peso.'),p(f"La muestra contiene {f(f2['n_muestra_una_victima_por_accidente'],0)} accidentes. H4 utiliza {f(f2['GLM']['n'],0)} víctimas con covariables completas y errores robustos agrupados por {f(f2['GLM']['accidentes'],0)} accidentes. Se requiere independencia aproximada entre accidentes; puede quedar dependencia temporal y geográfica."),p('Se cubren cuatro familias: chi cuadrado de independencia, comparación de rangos Mann-Whitney, diferencia de proporciones y regresión binomial ajustada. No se fuerzan pruebas de normalidad sobre una respuesta binaria.')]
    b=f2['bootstrap']
    phase2=[('Correcciones y diseño inferencial',inferdesign),('Hipótesis nulas y alternativas',hypothesis),('Resultados y tamaños de efecto',summarytests),
            ('Verificación de supuestos',[L.image('f2_01_normalidad.png',width=W),p('Q-Q sobre submuestras de edad; Shapiro en hasta 5.000 por grupo rechaza normalidad. Levene evalúa dispersión, sin ser un requisito de Mann-Whitney. La prueba de rangos compara distribuciones, no se interpreta exclusivamente como prueba de medianas. Las tablas de supuestos conservan valores p y recuentos esperados.'),p('H1 tiene frecuencias esperadas suficientes. H3 tiene suficientes fallecidos y no fallecidos por grupo. En H4 se verifican convergencia y rango de diseño completo; se usa sandwich agrupado. Ninguna de estas comprobaciones garantiza representatividad o elimina confusión.')]),
            ('Bootstrap frente al intervalo clásico',[L.image('f2_02_bootstrap.png',width=W),p(f"Para la diferencia de letalidad moto menos otros, IC bootstrap: {pct(b['IC95_bootstrap'][0])} a {pct(b['IC95_bootstrap'][1])} puntos porcentuales; IC clásico: {pct(b['IC95_clasico'][0])} a {pct(b['IC95_clasico'][1])}. Se hicieron 5.000 remuestras empíricas Bernoulli por grupo, con una víctima por accidente."),p('La diferencia es pequeña y negativa en esta población condicionada a lesión registrada. No significa que usar moto sea más seguro por viaje. Se excluyen ilesos, hay diferentes tipos de siniestro y otros confusores; el denominador es decisivo.')]),
            ('Asociación ajustada y límites',[L.table(['Variable','OR','IC 95 %','p'],[[r['variable'],f(r['OR']),f(r['OR_IC95_bajo'])+' a '+f(r['OR_IC95_alto']),pv(r['p'])] for r in readc('regresion_logistica_inferencial.csv')],[W*.4,W*.15,W*.3,W*.15]),p('Noche frente a pleno día tiene OR ajustado aproximadamente 1,85. Se controla edad cuadrática, sexo, usuario de moto, peatón, ruralidad y tendencia anual. OR es razón de odds, no multiplicador directo de probabilidades; pueden faltar confusores y las ausencias pueden seleccionar casos.')]),
            ('Conclusión de la fase 2',[p('Los cuatro contrastes rechazan sus hipótesis nulas con Holm, pero los efectos no tienen la misma magnitud. Sexo muestra asociación pequeña; edad difiere con superposición; la diferencia de usuarios de moto es pequeña y depende del denominador; nocturnidad conserva asociación condicional en el GLM.'),p('Los registros no provienen de muestreo probabilístico y no permiten extrapolar a toda circulación vial. Los intervalos y valores p dependen de supuestos y no capturan subregistro. Grandes cantidades hacen detectable una diferencia pequeña. La clasificación posterior debe evaluar utilidad fuera del entrenamiento, no usar significancia como sinónimo de predicción.'),p('Se llevan edad, sexo, vehículo, rol, entorno y tiempo al modelado junto con localización y condiciones del evento. Se excluyen las variables que contienen el resultado, los IDs y la atribución posterior de causa; no se hacen nuevos contrastes hasta encontrar resultados favorables.')])]
    design=[p('Desarrollo 2017-2023: 573.747 víctimas. Tres cortes de búsqueda entrenan hasta 2020/2021/2022 y validan respectivamente 2021/2022/2023. Cada transformación se aprende en el entrenamiento de ese corte.'),p('Se elige por AP media de fallecidos, sin consultar prueba. El mejor de cada familia se reajusta en desarrollo. Enero-junio 2024 calibra puntuaciones mediante sigmoid; julio-diciembre 2024 elige el umbral que maximiza F1 de fallecidos. Se fija además un punto para recall >=80 % en esa validación y se compara con 0,50.'),p('La selección y los umbrales se escriben antes de predecir 2025; la prueba se evalúa una vez y no modifica decisiones. El perfilado de fuentes sí había observado cantidades y cobertura de todos los años; se declara esa auditoría previa.'),p('Se comparan 13 configuraciones, 39 ajustes CV, de logística, Bayes categórico, árbol y LightGBM; también dos modelos con solo sexo/edad y Dummy. La búsqueda completa está en grilla_predefinida.json. Bayes discretiza numéricas en seis intervalos de entrenamiento; árboles no necesitan escalado pero comparten preparación documentada.'),p('Pesos de clase: logística natural frente a balanced y LightGBM natural frente a raíz de heridos/fallecidos, siempre calculados en entrenamiento. No se fabrican fallecidos ni se balancea prueba. Los pesos pueden perjudicar la calibración; se corrige con un período independiente de prevalencia natural.')]
    cvrows=readc('ranking_CV.csv')
    cvsection=[L.table(['Configuración','AP CV media','SD','AUC CV'],[[r['nombre'],f(r['AP_media']),f(r['AP_sd']),f(r['ROC_media'])] for r in cvrows],[W*.55,W*.16,W*.13,W*.16]),p('La variante ganadora fue LightGBM con 15 hojas, 240 árboles, tasa 0,06, mínimo 120 casos por hoja, regularización L2=8 y peso positivo raíz de la razón de clases. La tabla completa conserva la grilla, los cortes y los tiempos. No se eligió el ganador mirando 2025.')]
    metricsection=[L.table(['Modelo','AP','ROC AUC','Precisión','Recall','F1 macro','Exactitud'],[[r['familia'],f(r['AP']),f(r['ROC_AUC']),pct(r['precision']),pct(r['recall']),f(r['F1_macro']),pct(r['accuracy'])] for r in results],[W*.23,W*.11,W*.13,W*.14,W*.12,W*.14,W*.13]),
                   p('Las filas sexo_edad usan únicamente esas dos variables; los demás usan 24 predictores. La prueba conserva 83.550 heridos y 6.043 fallecidos entre 89.593 víctimas. Los intervalos por remuestreo de accidentes conservan dependencia de víctimas del mismo evento.'),
                   p('Una regla siempre herido obtiene 93,26 % de exactitud y recall de fallecidos cero. AP no es porcentaje de aciertos: su referencia para puntuación constante es la prevalencia. Precisión responde qué proporción de alertas de fallecimiento acertó; recall responde qué proporción de fallecidos reales se detectó.')]
    limits=[p(f"Respuesta a la pregunta: sí hay capacidad predictiva adicional al incorporar características vehiculares y del siniestro. En el mismo Brasil de 2025, AUC pasa de 0,619 con sexo/edad a {f(chosen['ROC_AUC'])}; AP de 0,104 a {f(chosen['AP'])}, y F1 macro de 0,512 a {f(chosen['F1_macro'])}. El IC bootstrap pareado de la mejora de AP es aproximadamente 0,187 a 0,211."),
            p('Frente al documento anterior de Paraguay, AUC 0,581 y F1 macro 0,530 son referencias descriptivas. País, población, prevalencia, variables y división son diferentes; no es una prueba causal de mejora. El recall anterior era 45,41 % y el principal actual 40,58 %: no todos los indicadores mejoraron al mismo umbral.'),
            p('El modelo sigue perdiendo 3.591 de 6.043 fallecidos al umbral principal y genera 5.264 falsas alarmas. El punto de mayor detección encuentra 81,98 % pero tiene precisión 13,51 % y 31.721 falsas alarmas. No hay un único umbral óptimo para todos los objetivos: los costos reales no fueron definidos por una institución usuaria.'),
            p('AP de entrenamiento 0,395, validación 0,298 y prueba 0,302 muestra optimismo del ajuste y buena proximidad entre los dos períodos posteriores, sin garantizar estabilidad futura. Ubicación y tipo de evento son útiles, pero no están disponibles antes de que exista el siniestro: esto no es predicción del riesgo de accidentarse ni mortalidad clínica al ingreso.'),
            p('Persisten cobertura parcial, falta de exposición y seguimiento, ausencias, cambios de registro y dependencia geográfica/temporal. La finalidad es académica; cualquier aplicación real requeriría validar disponibilidad de variables, calibración, grupos, costos y otro período de evaluación independiente. No se reajusta este experimento con 2025 como si continuara siendo una prueba nueva.'),
            L.sub('Reproducibilidad e integridad'),p('Código, datos preparados, modelos, tablas, notebooks y protocolo acompañan el informe. Se declara asistencia de IA en programación, análisis y redacción; el grupo debe verificar y comprender el material y adoptar sus propias decisiones e interpretaciones. No se fabrican contribuciones personales, legajos ni aprobación docente del cambio de dataset.')]
    phase3=[('Diseño experimental y desbalance',design),('Búsqueda y selección temporal',cvsection),('Prueba final de 2025',metricsection)]
    phase3 += [(title,graph(name,g3)) for title,name in [('Aporte de las variables','f3_01_AP_modelos.png'),('Discriminación y clase minoritaria','f3_02_curvas.png'),('Aciertos y errores','f3_03_confusion.png'),('Sobreajuste y generalización','f3_04_generalizacion.png'),('Calibración de puntuaciones','f3_05_calibracion.png'),('Qué variables aprendió a utilizar','f3_06_importancia.png'),('Umbrales: detección frente a falsas alarmas','f3_07_umbrales.png')]]
    phase3 += [('Conclusión y comparación con el trabajo anterior',limits)]
    build('Comprension_del_problema.pdf','Comprensión del problema',[('Pregunta y objetivos',problem),('Alcance y método previsto',[*sources[:2],*quality[-2:],p('La evaluación se refiere a víctimas de Brasil; cambiar el país exige actualizar título, contexto y alcance. Las fases son acumulativas sobre el mismo dataset individual y las decisiones deben ser defendidas por el grupo.')])],index=False)
    build('Fase_1_Preparacion_y_EDA.pdf','Fase 1 - Preparación y exploración',phase1)
    build('Fase_2_Inferencia.pdf','Fase 2 - Inferencia estadística',phase2)
    build('Fase_3_Modelado_y_Evaluacion.pdf','Fase 3 - Modelado y evaluación',phase3)
    integrated=[('Problema y objetivos',problem),('Fuentes y construcción',sources),('Calidad de los datos',quality),('Desbalance y edad',graph('f1_01_clases.png',f1['interpretaciones'])+graph('f1_02_histograma_edad.png',f1['interpretaciones'])),('Cambios temporales',graph('f1_04_serie_temporal.png',f1['interpretaciones'])),('Inferencia: diseño',inferdesign),('Inferencia: hipótesis',hypothesis),('Inferencia: resultados',summarytests),('Inferencia: conclusión',phase2[-1][1]),*phase3]
    build('Informe_Integrador.pdf','Informe integrador - Tres fases',integrated)


if __name__=='__main__':main()
