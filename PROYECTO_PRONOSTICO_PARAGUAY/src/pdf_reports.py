"""Cinco informes PDF a partir de resultados calculados, sin volver a entrenar.

Puede ejecutarse con el Python que tenga reportlab instalado. Las tablas se
leen como CSV/JSON estandar; no depende del entorno de los modelos.
"""
import csv
import html
import json
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';REPORTS=OUT/'reports'
FONT_DIR=Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('Vera',str(FONT_DIR/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('Vera-Bold',str(FONT_DIR/'VeraBd.ttf')))
pdfmetrics.registerFontFamily('Vera',normal='Vera',bold='Vera-Bold',italic='Vera',boldItalic='Vera-Bold')
STYLES=getSampleStyleSheet()
STYLES.add(ParagraphStyle(name='BodyProject',fontName='Vera',fontSize=9.2,leading=13.2,spaceAfter=8,textColor=colors.HexColor('#20323f')))
STYLES.add(ParagraphStyle(name='TitleProject',fontName='Vera-Bold',fontSize=21,leading=27,spaceAfter=16,textColor=colors.HexColor('#21496d')))
STYLES.add(ParagraphStyle(name='HeadingProject',fontName='Vera-Bold',fontSize=14,leading=19,spaceAfter=13,textColor=colors.HexColor('#21496d')))
STYLES.add(ParagraphStyle(name='SubProject',fontName='Vera-Bold',fontSize=10.5,leading=15,spaceAfter=8,textColor=colors.HexColor('#21496d')))
STYLES.add(ParagraphStyle(name='SmallProject',fontName='Vera',fontSize=7.8,leading=10.4,spaceAfter=6,textColor=colors.HexColor('#465763')))
STYLES.add(ParagraphStyle(name='TableProject',fontName='Vera',fontSize=7.5,leading=10,spaceAfter=0))
STYLES.add(ParagraphStyle(name='TableHeadProject',fontName='Vera-Bold',fontSize=7.5,leading=10,textColor=colors.white))
WIDTH=A4[0]-3.2*cm


def read_json(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def read_csv(name):
    with (OUT/'tables'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def fmt(value,digits=2):
    if value is None or value=='':return '-'
    try:return f'{float(value):,.{digits}f}'.replace(',','X').replace('.',',').replace('X','.')
    except (ValueError,TypeError):return str(value)
def pv(value):
    value=float(value)
    return f'{value:.3g}'.replace('.',',') if value<.001 else fmt(value,4)
def p(text,small=False):return Paragraph(html.escape(str(text)),STYLES['SmallProject' if small else 'BodyProject'])
def heading(text):return Paragraph(html.escape(text),STYLES['HeadingProject'])
def sub(text):return Paragraph(html.escape(text),STYLES['SubProject'])
def bullets(items):return [Paragraph(html.escape(str(x)),STYLES['BodyProject'],bulletText='•') for x in items]
def table(headers,rows,widths=None):
    cells=[[Paragraph(html.escape(str(x)),STYLES['TableHeadProject']) for x in headers]]
    cells += [[Paragraph(html.escape(str(x)),STYLES['TableProject']) for x in row] for row in rows]
    t=Table(cells,colWidths=widths or [WIDTH/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#21496d')),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
                          ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
                          ('BOTTOMPADDING',(0,0),(-1,-1),6),
                          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f4f6')]),
                          ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#b9c7cf'))]))
    return t
def image(name,width=WIDTH):
    from reportlab.lib.utils import ImageReader
    path=OUT/'figures'/name;iw,ih=ImageReader(str(path)).getSize()
    return Image(str(path),width=width,height=width*ih/iw)


def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#c6d2d9'))
    canvas.line(1.6*cm,1.2*cm,A4[0]-1.6*cm,1.2*cm)
    canvas.setFont('Vera',7);canvas.setFillColor(colors.HexColor('#526674'))
    canvas.drawString(1.6*cm,.8*cm,'Proyecto integrador | Pronóstico de siniestros | 31/10/2026')
    canvas.drawRightString(A4[0]-1.6*cm,.8*cm,f'Página {doc.page}');canvas.restoreState()


def cover(label,subtitle):
    return [Spacer(1,1.0*cm),p('CIENCIA DE DATOS · PROYECTO INTEGRADOR',True),Spacer(1,.5*cm),
            Paragraph(label,STYLES['TitleProject']),
            Paragraph('Pronóstico mensual de siniestros de tránsito registrados por la Patrulla Caminera',STYLES['HeadingProject']),
            p(subtitle),Spacer(1,.8*cm),
            sub('Integrantes'),p('Alan Alcaraz · Leandro Ferreira · Jorge Rios'),
            p('Legajos: no informados. Completar antes de la entrega.',True),
            sub('Alcance'),p('Paraguay, zona Central e Interior. Cuadros oficiales del INE con fuente Patrulla Caminera. Serie 2016-2024; desarrollo 2016-2022, calibración 2023 y prueba 2024.'),
            sub('Estado del material'),p('Resultados calculados y reproducibles. Borrador de apoyo académico con asistencia de IA; el grupo debe revisar, comprender y asumir las decisiones metodológicas y la interpretación antes de entregar.'),
            p('Fecha de elaboración: 31 de octubre de 2026.',True)]


def build(name,label,subtitle,sections):
    story=cover(label,subtitle)+[PageBreak(),heading('Índice')]
    for number,(title,_) in enumerate(sections,3):
        story.append(p(f'{number:02d}   {title}'))
    for title,content in sections:story.extend([PageBreak(),heading(title),*content])
    target=REPORTS/name
    SimpleDocTemplate(str(target),pagesize=A4,rightMargin=1.6*cm,leftMargin=1.6*cm,
                      topMargin=1.6*cm,bottomMargin=1.65*cm,
                      title=label,author='Material de apoyo con asistencia de IA').build(story,onFirstPage=footer,onLaterPages=footer)
    return dict(archivo=name,paginas_diseno=len(sections)+2)


def main():
    REPORTS.mkdir(exist_ok=True)
    a=read_json('auditoria_datos.json');f1=read_json('fase1_resultados.json');f2=read_json('fase2_resultados.json');f3=read_json('fase3_resultados.json')
    descript=read_csv('descriptivos_desarrollo.csv')[0]
    contrasts=f2['contrastes'];chosen=f3['metricas_prueba_seleccionado'];compare=f3['comparacion']
    forecasts=read_csv('pronostico_2025_corte_2024.csv');selected=f3['seleccion']['familia']
    inventory=read_csv('inventario_fuentes.csv');dictrows=read_csv('diccionario_final.csv')
    comp_rows=[[r['familia'],fmt(r['MAE_train']),fmt(r['MAE_CV']),fmt(r['MAE_test']),fmt(r['R2'])] for r in compare]
    testmetrics=read_csv('metricas_prueba_2024.csv')
    graph_text=f1['interpretaciones']
    def graph(name):return [image(name),p(graph_text[name],True)]
    question='¿Con qué precisión se pueden pronosticar los siniestros mensuales registrados por la Patrulla Caminera en zona Central e Interior durante doce meses, a partir de su historial y el calendario, frente a referencias sencillas?'
    objectives=[
        'Construir una serie mensual verificable desde los cuadros oficiales, conservando originales, versiones y procedencia por celda.',
        'Describir distribución, evolución temporal, composición y posibles patrones del período de desarrollo.',
        'Contrastar cuatro hipótesis de calendario, semestres, tendencia y dependencia de corto plazo, con supuestos y corrección múltiple.',
        'Comparar modelos de familias distintas mediante validación cronológica a doce meses y evaluar 2024 sin reajustar decisiones a sus resultados.',
        'Interpretar errores y límites, y producir una proyección reproducible posterior al último dato con su fecha de corte claramente indicada.'
    ]
    problem=[sub('Contexto y decisión'),p('Los datos proceden de registros de la Patrulla Caminera publicados en cuadros del INE. Anticipar cantidades mensuales puede orientar planificación de recursos, sin convertir los registros institucionales en una medición completa de todos los accidentes del país.'),
             sub('Pregunta principal'),p(question),
             sub('Objetivo general'),p('Evaluar la capacidad de modelos temporales y de aprendizaje automático para pronosticar doce cantidades mensuales de siniestros de tránsito registrados por la Patrulla Caminera, con trazabilidad y comparación honesta contra referencias.'),
             sub('Objetivos específicos'),*bullets(objectives)]
    scope=[sub('Justificación'),p('El cambio de objetivo aprovecha la unidad realmente observada: una cantidad mensual. Evita expandir cuadros agregados a supuestas fichas individuales. La utilidad del proyecto está en medir qué mejora aporta un modelo y cuándo sus errores impiden usarlo con confianza.'),
           sub('Unidad de análisis y población observada'),p('Una fila representa un mes calendario de registros de la Caminera en Central e Interior. La clave natural es año-mes. La fecha en el CSV usa el primer día solo para representar el período; no es la fecha de un accidente.'),
           sub('Alcance'),p('Se consolidan 108 meses de 2016-2024. Las fases exploratoria e inferencial usan exclusivamente 84 meses de 2016-2022. Se reserva 2023 para calibrar una banda empírica y 2024 para evaluar pronósticos emitidos desde diciembre de 2023.'),
           sub('Limitaciones previstas'),*bullets(['No hay identificadores de accidente, persona o vehículo; no se realiza clasificación individual.',
              'La coincidencia aritmética entre fuentes no prueba estabilidad de cobertura o esfuerzo de registro.',
              'Los datos de 2024 ya eran visibles en la auditoría de fuentes; se separan del ajuste y de las pruebas inferenciales, pero no constituyen una prueba externa ciega.',
              'El número de períodos es limitado y los meses están temporalmente relacionados. No se supone causalidad ni riesgo por viaje.',
              'Un pronóstico con corte en diciembre de 2024 no es una estimación actualizada de 2027.'])]
    sources=[sub('Fuentes primarias y trazabilidad'),p('Catálogo del INE: https://www.ine.gov.py/tabulado/16/anuario. Siete cuadros 12.2.2 descargados el 31/10/2026; sus fuentes internas son MOPC / Patrulla Caminera. Cada original se conserva en data/raw con su SHA-256 y URL exacta en catalogo_fuentes.json e inventario_fuentes.csv.'),
             table(['Edición / archivo conservado','Filas mensuales','Tamaño (KB)'],[[r['archivo'],r['filas_mensuales'],fmt(float(r['bytes'])/1024,1)] for r in inventory],[WIDTH*.67,WIDTH*.14,WIDTH*.19]),
             p('Licencia: el acceso a los cuadros es público; no se encontró en sus hojas una licencia específica que pueda afirmarse sin revisión adicional. Se conserva atribución a las instituciones.'),
             sub('Referencias metodológicas'),*bullets(['Hyndman y Athanasopoulos, Forecasting: Principles and Practice, capítulo 5: https://otexts.com/fpp3/toolbox.html',
                  'Documentación de statsmodels: covarianza HAC, pruebas de diagnóstico y suavizado exponencial. https://www.statsmodels.org/stable/',
                  'Documentación de scikit-learn: Ridge, RandomForestRegressor, SVR, métricas y escalado. https://scikit-learn.org/stable/']),
             p('Las versiones exactas ejecutadas están en requirements.txt y output/entorno.json. La consigna de la asignatura se utilizó como referencia de estructura, sin inventar devoluciones docentes ni resultados.',True)]
    ai=[sub('Declaración de asistencia de IA'),p('Se empleó un asistente de IA para proponer el diseño, redactar y ejecutar código, preparar auditorías y gráficos, calcular resultados y redactar este borrador. No se declara que el grupo haya realizado por sí solo esas tareas.'),
        p('La sección 11 de la consigna reserva al grupo las decisiones metodológicas y la interpretación. Antes de entregar, sus integrantes deben revisar este material, comprender el código, contrastar los resultados y adoptar o ajustar justificadamente las decisiones. La generación de estos archivos no sustituye ese trabajo ni la exposición del grupo.'),
        sub('Correcciones y revisión humana'),p('No se recibió una nueva devolución de la profesora sobre este enfoque. Las listas de cambios describen modificaciones técnicas respecto del proyecto anterior, no observaciones docentes inventadas. Los legajos y cualquier requisito institucional adicional permanecen pendientes.'),
        sub('Cómo reproducir'),p('Desde la carpeta del proyecto: python src/run_all.py. Los originales están incluidos y se verifican por hash. El flujo crea CSV, tablas, figuras, modelos, notebooks y HTML; la generación de PDF requiere reportlab. La consulta de datos y el entrenamiento no necesitan acceso a internet.'),
        sub('Integridad de la evaluación'),p('No se modifica el modelo elegido después de mirar 2024. La repetición reproducible conserva el protocolo; una futura modificación metodológica deberá identificarse como un experimento nuevo, sin reutilizar 2024 como si nunca hubiera sido consultado.')]
    # Comprension: tres paginas, con portada abreviada e indice integrado.
    context_story=[heading('Comprensión del problema'),p('Alan Alcaraz · Leandro Ferreira · Jorge Rios | 31/10/2026'),p('Legajos pendientes de informar. Material de apoyo con asistencia de IA.',True),p('Contenido: contexto y pregunta (p. 1); objetivos (p. 2); alcance y uso (p. 3).',True),
                   sub('Contexto'),p('La Patrulla Caminera registra siniestros dentro de su cobertura institucional. El INE publica cuadros con sus cantidades mensuales. El proyecto estudia si ese historial permite anticipar doce meses mejor que una referencia sencilla para apoyar planificación, sin afirmar que abarque todos los accidentes de Paraguay.'),
                   sub('Pregunta principal'),p(question),p('Se reemplaza la clasificación de víctimas por pronóstico de cantidades. Los conteos agrupados son apropiados para este objetivo agregado, pero siguen sin aportar fichas individuales.'),
                   PageBreak(),heading('Objetivos y relevancia'),sub('Objetivo general'),p('Evaluar modelos para pronosticar doce cantidades mensuales de siniestros registrados, con trazabilidad y evaluación temporal.'),*bullets(objectives),
                   p('El proyecto admite una respuesta negativa: si los modelos no generalizan o solo mejoran referencias débiles, debe decirse y limitarse su uso.'),
                   PageBreak(),heading('Alcance y condiciones de uso'),*scope[2:],
                   p('Se evalúa 2024 retrospectivamente y se produce una proyección de 2025 con corte 2024. Para emitir un pronóstico operativo de 2027 se necesitan datos comparables más recientes y nueva validación.'),
                   p('Asistencia de IA declarada: propuestas, código, cálculos y redacción. El grupo debe revisar y asumir la metodología e interpretación antes de entregar.',True)]
    SimpleDocTemplate(str(REPORTS/'Comprension_del_problema.pdf'),pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=1.6*cm,bottomMargin=1.65*cm).build(context_story,onFirstPage=footer,onLaterPages=footer)
    manifests=[dict(archivo='Comprension_del_problema.pdf',paginas_diseno=3)]
    data_section=[p(f'Se leyeron {a["archivos"]} archivos. Se extrajeron {a["filas_extraidas"]} filas mensuales y se conservaron {a["filas_finales"]} períodos únicos. Los {a["duplicados_coincidentes"]} registros repetidos son versiones coincidentes; no son accidentes adicionales.'),
                  table(['Partición','Meses','Uso'],[['2016-2022','84','Exploración, hipótesis y validación'],['2023','12','Calibración de banda empírica, sin elegir modelos'],['2024','12','Evaluación final a doce meses']],[WIDTH*.22,WIDTH*.15,WIDTH*.63]),
                  sub('Perfilado y selección'),p('Se selecciona el mismo cuadro de tipología por año, con alcance publicado equivalente. Otros PDF, tablas de víctimas, motociclistas y procedimientos se descartan del objetivo principal porque tienen distintas unidades o universos y no deben sumarse al total.'),
                  p('La consolidación concatena ediciones y resuelve la repetición de la clave temporal; no es una unión por persona. Todas las versiones originales quedan disponibles. Exactitud aparente se evalúa por sumas y coincidencias, no contra un registro externo de casos.'),
                  table(['Dimensión de calidad','Resultado'],[['Completitud','108 de 108 meses esperados; objetivo sin faltantes'],['Consistencia','Siete componentes suman el total en cada fila'],['Unicidad','Una fila por año-mes tras resolver versiones'],['Actualidad','Último dato: diciembre 2024'],['Cobertura','Estabilidad institucional no demostrada con estas tablas']],[WIDTH*.28,WIDTH*.72])]
    cleaning=[table(['Decisión','Cantidad','Fundamento'],[[r['operacion'],r['cantidad_afectada'],r['fundamento']] for r in read_csv('bitacora_limpieza.csv')],[WIDTH*.23,WIDTH*.13,WIDTH*.64]),
              p('El guion se trata como cero solo en componentes categóricos donde se verifican las sumas. No se convierte automáticamente cualquier símbolo ausente a cero. No se imputan meses ni se fabrican personas.'),
              sub('Atípicos'),p(f'El criterio IQR señala {f1["atipicos_conservados"]} meses en desarrollo. Se conservan: un cambio real no es un error por ser extremo. El mecanismo de ausencia del objetivo no se clasifica como MCAR/MAR/MNAR porque no hay valores faltantes observados; el subregistro potencial es otra limitación.')]
    dict_section=[table(['Campo','Significado','Unidad / uso'],[['fecha','Clave mensual real','Mes, único'],['accidentes','Total registrado','Siniestros/mes; objetivo'],['choque…atropellamiento','Siete componentes del total','Descriptivos; no predictores del mismo mes'],['ano, mes, semestre','Calendario','Derivados determinísticos'],['dias_mes','Duración del período','Días; conocida anticipadamente'],['tasa_diaria_mes','Total / días','Descriptiva, excluida del modelo contemporáneo'],['archivo, hoja, celdas, edicion','Procedencia','No predictores'],['particion','Desarrollo/calibración/prueba','Asignada por fecha']],[WIDTH*.24,WIDTH*.43,WIDTH*.33]),
                  p('El diccionario completo final informa tipos, rangos, cardinalidad y porcentaje de faltantes por campo en output/tables/diccionario_final.csv. El diccionario original describe B (año/mes), C (total) y D:J (tipos).'),
                  sub('Variables para pronosticar'),p('Cinco rezagos (1, 2, 3, 6 y 12 meses), dos medias anteriores (3 y 12 meses), seno/coseno del mes y días del mes. Todos se construyen con historia disponible. El primer año sirve para formar rezagos; no se rellena con ceros.'),
                  p('La media anterior de tres meses usa t-1, t-2 y t-3, nunca el resultado del mes a predecir. Para horizontes futuros, la recursión utiliza predicciones donde ya no existen observaciones conocidas.')]
    descriptive=[table(['Estadístico de accidentes/mes','Valor'],[[label,fmt(descript[key])] for label,key in [('Media','media'),('Mediana','mediana'),('Moda','moda'),('Desvío','desv_est'),('CV','cv'),('Mínimo','minimo'),('Máximo','maximo'),('IQR','iqr'),('P5','p5'),('P25','p25'),('P50','p50'),('P75','p75'),('P95','p95'),('Asimetría','asimetria'),('Curtosis de exceso','curtosis_exceso')]],[WIDTH*.6,WIDTH*.4]),
                 p(f'La media de {fmt(f1["media"])} y la mediana de {fmt(f1["mediana"])} son cercanas. La asimetría global baja no implica estabilidad temporal ni normalidad independiente. Se describe también la tasa diaria y la dispersión entre años.')]
    f1conclusion=[p('Respuesta parcial: existen suficientes períodos y una unidad coherente para comparar pronósticos mensuales. La descripción por sí sola no prueba que un modelo pueda anticipar doce meses con precisión.'),
                  sub('Patrones y anomalías documentados'),*bullets([f'Los extremos de desarrollo son {f1["minimo"]["valor"]} siniestros ({f1["minimo"]["fecha"]}) y {f1["maximo"]["valor"]} ({f1["maximo"]["fecha"]}); se conservan ambos.',
                  'Los niveles varían entre años y el episodio de 2020 merece examen; no se le asigna una causa exclusivamente desde el gráfico.',
                  f'Las dos clases de siniestro más frecuentes concentran {fmt(f1["concentracion_dos_tipos_pct"],1)}% del total de desarrollo.',
                  'Las correlaciones entre cantidades actuales y rezagadas no equivalen a capacidad de pronóstico; pueden depender del régimen temporal.']),
                  sub('Hipótesis que pasan a Fase 2'),table(['ID','Hipótesis preliminar'],[['H1','Hay un patrón mensual alineado entre años'],['H2','Los semestres difieren en sus promedios dentro del año'],['H3','Hay tendencia monótona en promedios anuales'],['H4','El mes previo aporta asociación condicional al controlar otras variables']],[WIDTH*.12,WIDTH*.88]),
                  p('La muestra temporal pequeña y la posible variación de cobertura condicionan la inferencia. Se preservan las reservas cronológicas para no usar sus resultados al escoger pruebas o predictores.')]
    f1sections=[('Problema, pregunta y objetivos',problem),('Justificación, alcance y límites',scope),('Inventario, selección y calidad',data_section),('Limpieza e integración reproducible',cleaning),('Diccionarios y transformaciones',dict_section),('Descripción univariada',descriptive),
                ('Evolución y distribución',graph('f1_01_serie.png')+graph('f1_02_histograma.png')),
                ('Calendario y asociación bivariada',graph('f1_03_cajas_mes.png')+graph('f1_04_dispersion.png')),
                ('Comparación anual y correlaciones',graph('f1_05_barras_ano.png')+graph('f1_06_correlaciones.png')),
                ('Calendario completo y composición',graph('f1_07_calendario.png')+graph('f1_08_tipos.png')),
                ('Estacionalidad y duración del mes',graph('f1_09_perfil.png')+graph('f1_10_exposicion.png')),
                ('Conclusión y puente inferencial',f1conclusion),('Fuentes y reproducción',sources),('Integridad académica y revisión',ai)]
    manifests.append(build('Fase_1_Preparacion_y_EDA.pdf','Fase 1 · Preparación y análisis exploratorio','Fuentes, calidad, limpieza, estadística descriptiva y diez visualizaciones interpretadas.',f1sections))
    changes=[sub('Cambios respecto del proyecto anterior'),*bullets(['Se reemplaza gravedad individual por cantidad mensual y se conserva la unidad agregada real.',
             'Se consolidan versiones coincidentes en lugar de expandir frecuencias a personas.',
             'Se excluyen prueba y calibración de la exploración y los contrastes.',
             'La dependencia temporal se trata con bloques anuales, referencias circulares y covarianza HAC; no se invoca independencia de miles de filas expandidas.']),
             sub('Marco de contrastación'),p('Cuatro hipótesis primarias bilaterales, alfa 0,05 y Bonferroni para la familia completa (umbral individual equivalente 0,0125). Las decisiones se toman con p ajustado; no rechazar H0 no significa aceptarla.'),
             table(['ID','H0 y alternativa'],[['H1','H0: sin alineación mensual de rangos entre años; H1: existe alineación'],['H2','H0: diferencias semestrales simétricas centradas en cero; H1: centro distinto'],['H3','H0: rho(año, promedio anual)=0; H1: rho distinto de cero'],['H4','H0: beta del rezago 1=0 con controles; H1: beta distinto de cero']],[WIDTH*.1,WIDTH*.9]),
             p('Los desplazamientos circulares son referencias aproximadas que preservan orden temporal, no una aleatorización experimental. Las pruebas de supuestos son diagnósticos, no un filtro para buscar significación.')]
    assumptions=[p('Se usan siete años como bloques para calendario y semestres. Los meses dentro de un año no se consideran doce réplicas independientes de personas. Friedman es una comparación por rangos de medidas apareadas; sustituye una ANOVA de grupos independientes inadecuada para esta estructura.'),
                 table(['Diagnóstico','Variable','p'],[[r['prueba'],r['variable'],pv(r['p'])] for r in f2['supuestos']],[WIDTH*.25,WIDTH*.55,WIDTH*.2]),
                 p('Shapiro-Wilk no rechaza normalidad en estas muestras, pero eso no la demuestra. Wilcoxon se predefinió por el pequeño número de pares; no necesita homogeneidad de varianzas. Levene se informa como diagnóstico, no como supuesto obligatorio de esa prueba.'),
                 p('Ljung-Box sobre residuos no garantiza independencia ni exogeneidad. HAC corrige la covarianza ante dependencia débil; no corrige variables omitidas, no estacionariedad arbitraria ni cambios de cobertura.'),
                 image('f2_01_supuestos_qq.png')]
    h12=[sub('H1 · Calendario mensual'),p(f'Friedman Q={fmt(contrasts[0]["estadistico"])} (11 grados de libertad como referencia). p circular={pv(contrasts[0]["p"])}; p clásico={pv(contrasts[0]["p_clasico"])}. W de Kendall={fmt(contrasts[0]["efecto"],3)}, IC bootstrap aproximado [{fmt(contrasts[0]["ic_bajo"],3)}; {fmt(contrasts[0]["ic_alto"],3)}].'),
         p('No se rechaza H0 tras corrección. No es evidencia de ausencia de estacionalidad: solo siete ciclos y cambios de nivel limitan la potencia. La referencia circular rota cada secuencia anual sin mezclar sus doce valores al azar. El IC percentil de W puede excluir cero por su sesgo y soporte no negativo en muestras pequeñas; no se interpreta como otra prueba de significación.'),
         sub('H2 · Semestres apareados por año'),p(f'Wilcoxon W={fmt(contrasts[1]["estadistico"],0)}, n=7 pares, sin grados de libertad paramétricos. p={pv(contrasts[1]["p"])}; p ajustado={pv(contrasts[1]["p_bonferroni"])}. La diferencia media segundo menos primer semestre es {fmt(contrasts[1]["efecto"])} siniestros/mes.'),
         p(f'IC bootstrap para esa diferencia media: [{fmt(contrasts[1]["ic_bajo"])}; {fmt(contrasts[1]["ic_alto"])}]. El IC de la media y el contraste de centro simétrico de Wilcoxon no son exactamente el mismo estimando; esa distinción impide interpretar automáticamente uno como inversión del otro.'),
         image('f2_02_semestres.png'),p('Cada barra conserva el emparejamiento dentro del año. Las diferencias cambian de signo; el promedio global no implica un aumento constante.',True)]
    h34=[sub('H3 · Tendencia monótona anual'),p(f'Rho de Spearman={fmt(contrasts[2]["efecto"],3)}; p circular={pv(contrasts[2]["p"])}. La referencia que permuta años como independientes da p={pv(contrasts[2]["p_clasico"])}. No se rechaza H0.'),
         p('Con siete rotaciones la resolución mínima de p es 1/7: este contraste es conservador y no puede alcanzar el umbral Bonferroni. Se documenta esta falta de potencia en lugar de reemplazar la prueba por otra que dé significación. No demuestra estabilidad ni ausencia de tendencia.'),
         sub('H4 · Asociación condicional con el mes anterior'),p(f'Sobre 72 filas tras formar el rezago doce, beta del rezago uno={fmt(contrasts[3]["efecto"],3)}, IC HAC 95% [{fmt(contrasts[3]["ic_bajo"],3)}; {fmt(contrasts[3]["ic_alto"],3)}]. t={fmt(contrasts[3]["estadistico"],3)}, gl={fmt(contrasts[3]["gl"],0)}, p ajustado={pv(contrasts[3]["p_bonferroni"])}.'),
         p('Se rechaza H0 bajo los supuestos de la regresión. Se controlan rezago doce, seno/coseno del mes, tendencia, días del mes e indicador histórico de 2020. La asociación no es causal ni garantiza pronósticos de doce pasos. Los meses de 2023 y 2024 no entran en este ajuste.'),
         image('f2_04_residuos.png'),p('Los residuos corresponden al modelo inferencial, no al SVR que se seleccionará en la Fase 3.',True)]
    bootstrap=f2['comparacion_ic_media_semestres'];reg=f2['regresion']
    bootstrap_content=[p(f'Para la diferencia media semestral, el IC clásico t es [{fmt(bootstrap["clasico_t"][0])}; {fmt(bootstrap["clasico_t"][1])}] y el bootstrap de pares anuales es [{fmt(bootstrap["bootstrap"][0])}; {fmt(bootstrap["bootstrap"][1])}]. Ambos estiman el mismo parámetro medio; ambos dependen de la aproximación de independencia entre años.'),
                       image('f2_03_bootstrap.png'),p('Se remuestrean años completos con sus dos semestres emparejados, 3.000 veces, con semilla fija. No se crean víctimas ni meses nuevos como observaciones independientes.',True),
                       sub('Regresión y sensibilidad'),p(f'Para beta del rezago uno: IC OLS [{fmt(reg["ic_OLS"][0],3)}; {fmt(reg["ic_OLS"][1],3)}], IC HAC [{fmt(reg["ic_HAC"][0],3)}; {fmt(reg["ic_HAC"][1],3)}] e IC bootstrap de bloques de doce residuos [{fmt(reg["ic_bootstrap_bloques"][0],3)}; {fmt(reg["ic_bootstrap_bloques"][1],3)}].'),
                       p('El bootstrap residual mantiene el diseño fijo y aproxima dependencia de corto plazo; no resuelve la endogeneidad de rezagos. La tabla de sensibilidad HAC(6)/HAC(12) se conserva y no se utiliza para escoger el p más pequeño.')]
    contrast_table=[table(['ID','Estadístico','p primario','p ajustado','Efecto','Decisión'],[[r['id'],fmt(r['estadistico'],3),pv(r['p']),pv(r['p_bonferroni']),fmt(r['efecto'],3),r['decision']] for r in contrasts],[WIDTH*.07,WIDTH*.15,WIDTH*.16,WIDTH*.17,WIDTH*.13,WIDTH*.32]),
                    p('Los intervalos del 95% informados son marginales por contraste, no intervalos simultáneos para toda la familia. Las decisiones múltiples se basan en los valores p ajustados.'),
                    sub('Interpretación práctica'),p('La evidencia más clara es asociación temporal de corto plazo. El calendario y las diferencias de semestre no presentan evidencia concluyente bajo los contrastes predefinidos. Se mantienen variables de calendario como controles predictivos, pero su utilidad se decidirá por validación, no por exigir p<0,05.'),
                    sub('Confusores y representatividad'),*bullets(['Volumen de tránsito, kilómetros recorridos y esfuerzo de fiscalización no están medidos.',
                       'Cambios de cobertura o registro pueden alterar cantidades sin alterar el riesgo por viaje.',
                       '2020 representa un contexto distinto; el indicador no identifica por sí solo una causa.',
                       'La muestra temporal es pequeña: no se extienden conclusiones a todos los accidentes no registrados.']),
                    sub('Puente a la Fase 3'),p('Se evaluarán rezagos y medias previas junto con calendario, con escalado ajustado dentro de cada entrenamiento. Los resultados inferenciales no se usarán para seleccionar columnas mirando el año de prueba. La comparación temporal determinará si la asociación se transforma en capacidad predictiva.')]
    f2sections=[('Cambios y formulación de hipótesis',changes),('Supuestos y estructura temporal',assumptions),('Contrastes de calendario y semestres',h12),('Tendencia y regresión condicional',h34),('Bootstrap y sensibilidad',bootstrap_content),('Resumen, conclusión y puente predictivo',contrast_table),('Fuentes y reproducción',sources),('Integridad académica y revisión',ai)]
    manifests.append(build('Fase_2_Inferencia.pdf','Fase 2 · Análisis inferencial','Cuatro hipótesis, cuatro familias, diagnósticos, intervalos y corrección por comparaciones múltiples.',f2sections))
    design=[p('Tarea: regresión de conteos mensuales a doce pasos. No corresponde usar accuracy, F1 ni matriz de confusión. Los pronósticos son valores esperados continuos; no se redondean antes de evaluar.'),
            table(['Bloque','Qué se hace','Qué se evita'],[['2016-2022','EDA, cuatro contrastes y búsqueda temporal','Mirar 2024 para elegir variables o parámetros'],['Cortes 2019-2022','Cuatro pronósticos de doce meses: 48 errores/configuración','K-fold aleatorio o actualización con valores futuros reales'],['2023','Calibrar el radio de una banda después de elegir el modelo','Usarlo para cambiar la familia ganadora'],['2024','Evaluar una vez todas las familias con parámetros fijados','Cambiar al ganador por su desempeño de prueba']],[WIDTH*.19,WIDTH*.43,WIDTH*.38]),
            p('Los entrenamientos de validación contienen 36, 48, 60 y 72 meses respectivamente; después del rezago doce quedan 24, 36, 48 y 60 filas supervisadas. El ajuste final para evaluar 2024 usa 96 meses hasta diciembre de 2023 y 84 filas supervisadas.'),
            sub('Prevención de filtraciones'),p('Las medias se desplazan un mes. StandardScaler se ajusta solo dentro de cada entrenamiento. Choques, tipos de siniestro, tasa diaria del propio mes y resultados reales de meses futuros no se usan como entradas. Los doce pasos se generan recursivamente con predicciones.'),
            p('La prueba es interna y temporal: 2024 no participa del ajuste ni la selección. Sus cantidades ya se habían visto en la auditoría de disponibilidad, por lo que no se presenta como una validación externa ciega.')]
    models=[p(f'Se compararon {f3["configuraciones"]} especificaciones fijas: dos referencias y veinte configuraciones de cuatro familias aprendidas. Cada especificación se evaluó en los mismos cuatro cortes. Criterio primario: menor MAE medio; los empates se resuelven por el orden predefinido.'),
            table(['Familia','Configuraciones predefinidas'],[['Referencia estacional','Repite los doce meses del año previo'],['Referencia media12','Repite la media de los doce últimos meses'],['Ridge','alpha: 0,1; 1; 10; 100. Escalado dentro de Pipeline'],['Random Forest','250 árboles; profundidad 3 o sin límite; hoja mínima 2, 5 o 10'],['SVR RBF','C: 1, 10, 100; epsilon: 5 o 15; gamma=scale; escalado'],['ETS','Tendencia ninguna/aditiva; estacionalidad ninguna/aditiva; tendencia amortiguada cuando existe']],[WIDTH*.26,WIDTH*.74]),
            p('Ridge representa un modelo lineal regularizado; Random Forest, árboles; SVR, un método de margen con núcleo; ETS, una familia temporal clásica. La semilla es 20261031. No se ampliaron grillas después de ver prueba.'),
            p('La búsqueda completa por corte, los parámetros, tamaños de entrenamiento y advertencias están en los CSV y JSON de output. Se conservan especificaciones y selección congelada previas a la prueba.')]
    ranking=[table(['Familia','MAE validación','RMSE validación','Parámetros elegidos'],[[r['familia'],fmt(r['MAE_CV']),fmt(r['RMSE_CV']),r['parametros']] for r in f3['ranking_CV']],[WIDTH*.21,WIDTH*.17,WIDTH*.18,WIDTH*.44]),
             p(f'Se eligió {selected}, con C=1, epsilon=15 y gamma=scale, por su menor MAE de validación ({fmt(f3["ranking_CV"][0]["MAE_CV"])}). La elección precede a 2023 y 2024.'),
             image('f3_04_cortes.png'),p('Cada punto cambia el año pronosticado y agrega historia. No es una curva de aprendizaje con un conjunto de validación fijo; los saltos reflejan también cambios del fenómeno.',True)]
    learning=[table(['Familia','MAE ajuste','MAE CV','MAE prueba','R² prueba'],comp_rows,[WIDTH*.28,WIDTH*.18,WIDTH*.18,WIDTH*.18,WIDTH*.18]),
              image('f3_01_comparacion.png'),p('El ajuste de entrenamiento usa predicciones a un paso con antecedentes reales; validación y prueba son pronósticos a doce pasos. Las brechas son diagnósticas y no una medida pura de sobreajuste, porque cambian el horizonte y los períodos.',True),
              p('Random Forest presenta ajuste mucho más favorable que su validación y prueba, compatible con sobreajuste y falta de generalización. SVR está fuertemente regularizado y produce un perfil casi plano: su mejora corresponde sobre todo a estimar el nivel, no a recuperar cada oscilación mensual.')]
    results_test=[table(['Métrica seleccionada','Resultado 2024'],[['MAE',fmt(chosen['MAE'])+' siniestros/mes'],['RMSE',fmt(chosen['RMSE'])+' siniestros/mes'],['MAPE',fmt(chosen['MAPE'])+'%'],['R²',fmt(chosen['R2'],3)],['Sesgo medio',fmt(chosen['sesgo'])+' siniestros/mes'],['Total real',fmt(chosen['total_real'],0)],['Total predicho',fmt(chosen['total_predicho'])],['Error de total',fmt(chosen['error_total'])]],[WIDTH*.5,WIDTH*.5]),
                  p(f'La reducción de MAE frente a la referencia estacional es {fmt(f3["mejora_MAE_vs_estacional_pct"])}%; frente a la media12 es {fmt(f3["mejora_MAE_vs_media12_pct"])}%. Eso no equivale a un porcentaje de exactitud.'),
                  p('El R² negativo indica que el error cuadrático supera el de una constante igual a la media real de 2024. Esa media se conoce después de observar el año y no es una referencia operativa disponible al pronosticar. Aun así, el resultado evidencia escasa explicación de las variaciones mensuales.'),
                  p('Ridge obtiene un MAE de prueba ligeramente menor que SVR. No se cambia la selección: elegirlo después de observar 2024 contaminaría la evaluación. Su resultado se muestra para transparencia, no para retocar al ganador.')]
    errors=[image('f3_02_prueba.png'),p('Las doce predicciones se emiten desde un único origen: diciembre de 2023. No se actualiza el modelo con los valores reales de enero, febrero u otros meses de 2024.',True),
            table(['Mes','Real','Predicho','Error absoluto'],[[r['fecha'][:7],fmt(r['real'],0),fmt(r['prediccion']),fmt(r['error_absoluto'])] for r in f3['errores_mayores']],[WIDTH*.22,WIDTH*.23,WIDTH*.27,WIDTH*.28]),
            p('Los meses peor predichos concentran picos que el perfil plano no anticipa. No se atribuyen sus causas a clima, movilidad o fiscalización porque esas variables no están observadas en el dataset.')]
    residuals=[image('f3_03_residuos.png'),p('Error definido como predicho menos real: negativo indica subestimación. El sesgo global es negativo, coherente con un total anual subestimado. Doce residuos de prueba son pocos para diagnosticar dependencia con potencia suficiente.',True),
               image('f3_07_horizonte.png'),p('Hay una sola observación por horizonte en la prueba anual. No se afirma que el modelo siempre empeore o mejore a determinado número de meses.',True)]
    interpretation=[image('f3_05_importancia.png'),p('La perturbación se calcula en los cuatro cortes de validación, reemplazando una entrada por valores históricos de su distribución y ejecutando la recursión. No usa prueba para seleccionar variables. Las perturbaciones pueden romper relaciones entre rezagos: son diagnóstico, no efecto causal.',True),
                    p('En SVR los cambios medios de MAE por variable son menores a 0,1 siniestros/mes y su dispersión es comparable o mayor. No hay evidencia robusta de una variable claramente dominante mediante este diagnóstico. El modelo es casi constante y fuertemente regularizado.'),
                    sub('Relación con Fases 1 y 2'),p('La asociación inferencial con el mes previo no se convierte automáticamente en capacidad de pronóstico anual: al avanzar doce pasos, cada predicción alimenta la siguiente. La inferencia condicional y la generalización fuera de muestra responden preguntas diferentes.'),
                    p('Se conservan coeficientes estandarizados de Ridge e importancias de impureza de Random Forest como diagnósticos de esas familias, sin atribuirlos al SVR ganador.')]
    uncertainty=[p(f'El modelo seleccionado se entrenó hasta 2022 para pronosticar 2023, sin usar ese año al elegir hiperparámetros. Se tomó el máximo de sus doce errores absolutos: radio {fmt(f3["calibracion"]["radio_banda"])} siniestros/mes. Es el orden 12 de ceil((12+1)×0,9).'),
                 p(f'La banda contiene {fmt(100*f3["calibracion"]["cobertura_observada_2024"],0)}% de los doce valores de 2024. Es amplia y su cobertura observada en un solo año no prueba una garantía del 90% en futuros períodos.'),
                 p('La construcción se inspira en cuantiles de errores de calibración, pero los errores temporales y por horizonte no son necesariamente intercambiables. Se etiqueta como banda empírica aproximada, no como intervalo conformal con cobertura demostrada.'),
                 sub('Incertidumbre del total anual'),p('No se suman los extremos mensuales ni se combinan varianzas como si los doce errores fueran independientes. Se informa un total puntual y se omite un intervalo anual formal: un único bloque anual de calibración no permite sostenerlo con fiabilidad.'),
                 sub('Aplicación práctica'),p('La mejora frente a referencias no compensa la incapacidad de anticipar picos. Puede servir como ejercicio de planificación agregada con revisión humana, no como asignación automática de recursos ni promesa de seguridad para una ruta o persona.')]
    projection=[image('f3_06_proyeccion.png'),p(f'Después de cerrar la evaluación, se reajustó la misma especificación SVR con 2016-2024. La proyección posterior al último dato suma {fmt(f3["proyeccion"]["total"])} siniestros para 2025. No se evaluó con datos reales de 2025 y no es un pronóstico actualizado de 2027.',True),
                table(['Mes 2025','Pronóstico','Banda inferior','Banda superior'],[[r['fecha'][:7],fmt(r['prediccion']),fmt(r['banda_inferior']),fmt(r['banda_superior'])] for r in forecasts],[WIDTH*.2,WIDTH*.24,WIDTH*.28,WIDTH*.28]),
                p('El archivo modelo_pronostico.joblib contiene el reajuste de producción; modelo_evaluado_2024.joblib conserva el ajuste que realmente produjo las métricas de prueba. El script de inferencia acepta historial nuevo mensual completo y mantiene los parámetros elegidos.')]
    conclusion3=[sub('Respuesta final'),p(f'Con este diseño, {selected} mejora las dos referencias operativas en 2024 y reduce el MAE a {fmt(chosen["MAE"])}. Sin embargo, su R² de {fmt(chosen["R2"],3)} y su perfil casi plano muestran que no anticipa satisfactoriamente las fluctuaciones mensuales. El resultado es una mejora relativa de nivel, no evidencia de alta capacidad predictiva.'),
                 sub('Qué aprendió y qué no'),p('El criterio temporal favoreció un modelo de muy baja flexibilidad. No reproduce picos y subestima el total de 2024. Random Forest muestra que memorizar mejor el entrenamiento no asegura pronosticar mejor. No se ocultaron resultados negativos ni se cambió la especificación para mejorar prueba.'),
                 sub('Limitaciones y continuación'),*bullets(['Solo nueve años de datos, cuatro cortes de validación, un año de calibración y uno de prueba.',
                    'Faltan exposición vial, cambios de registro y factores externos conocidos anticipadamente.',
                    'No hay validación externa o multianual posterior a 2024; deben conseguirse datos comparables recientes.',
                    'Evaluar otro dataset o nuevos predictores sería un experimento nuevo y necesitaría otra reserva temporal.',
                    'No deben asignarse recursos únicamente con estas predicciones ni extrapolarse a víctimas individuales.']),
                 sub('Lista de correcciones aplicada desde Fase 2'),p('La selección se basa en validación predictiva, no solo en significación inferencial. Se respetan autocorrelación e incertidumbre. Las variables contemporáneas del objetivo quedan excluidas y se informa cuándo los resultados inferenciales no se traducen en generalización.')]
    f3sections=[('Tarea y diseño temporal',design),('Familias, grillas y referencias',models),('Selección por validación',ranking),('Aprendizaje, brechas y generalización',learning),('Evaluación final: métricas e interpretación',results_test),('Predicciones y casos peor estimados',errors),('Residuos y error por horizonte',residuals),('Interpretación de variables',interpretation),('Calibración, incertidumbre y uso',uncertainty),('Proyección retrospectiva y modelo guardado',projection),('Conclusión y respuesta consolidada',conclusion3),('Fuentes y reproducción',sources),('Integridad académica y revisión',ai)]
    manifests.append(build('Fase_3_Modelado_y_Evaluacion.pdf','Fase 3 · Modelado y evaluación','Comparación temporal de familias, errores de entrenamiento y prueba, interpretación y límites de generalización.',f3sections))
    # Integrador: resultados centrales, sin copiar todas las paginas de las fases.
    integrated=[('Pregunta, objetivo y decisión',problem),('Alcance y reservas temporales',scope),('Fuentes, calidad y limpieza',data_section),('Diccionario y variables derivadas',dict_section),
                ('Distribución y evolución',graph('f1_01_serie.png')+graph('f1_02_histograma.png')),
                ('Asociaciones y composición',graph('f1_04_dispersion.png')+graph('f1_08_tipos.png')),
                ('Hipótesis y supuestos',changes),('Resultados inferenciales',contrast_table),('Bootstrap y limitaciones inferenciales',bootstrap_content),
                ('Diseño de la comparación predictiva',design),('Modelos y selección',ranking),('Entrenamiento, validación y prueba',learning),('Métricas finales y sus límites',results_test),
                ('Pronósticos evaluados y errores',errors),('Interpretación y coherencia entre fases',interpretation),('Incertidumbre y proyección',uncertainty[:4]+[image('f3_06_proyeccion.png'),p(f'Proyección retrospectiva de 2025 con corte 2024: total {fmt(f3["proyeccion"]["total"])}. No es una estimación actualizada de 2027.',True)]),
                ('Respuesta final y trabajo futuro',conclusion3),('Fuentes y reproducción',sources),('Integridad académica y revisión',ai)]
    manifests.append(build('Informe_Integrador.pdf','Informe integrador · Tres fases','Del dato agregado a la evaluación honesta de un pronóstico mensual.',integrated))
    (OUT/'manifiesto_informes.json').write_text(json.dumps(manifests,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in manifests:print(row)


if __name__=='__main__':main()
