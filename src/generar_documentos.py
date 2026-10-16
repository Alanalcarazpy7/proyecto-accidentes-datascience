"""Genera los informes Word y la documentación desde las salidas verificadas.

No ajusta modelos ni contiene métricas predictivas prefijadas. Las páginas del
informe se componen explícitamente; el conteo real se comprueba al exportar PDF.
"""
from pathlib import Path
import json
import re
import argparse
import sys
from io import BytesIO
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.complementos_fase3 import leer_resultados, leer_figuras
FIGURAS = {}
DOCS = ROOT / 'docs'
SOURCE = 'https://www.datos.gov.py/dataset/anuario-2021-estadisticas-policiales-y-de-accidentes-de-transito'
FECHA = '16 de octubre de 2026'
AUTORES = 'Alan Alcaraz · Leandro Ferreira · Jorge Rios'


def ruta_informe(nombre, extension):
    carpeta = DOCS / ('fase3' if nombre == 'Informe_Fase3' else 'integrador')
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / (nombre + extension)


def text(s):
    return ('p', s)


def tabla(df, caption):
    return ('t', df, caption)


def imagen(nombre, caption):
    return ('i', nombre, caption)


def limpiar(s):
    return re.sub(r'\*\*|`', '', str(s)).replace('—', '-').replace('–', '-')


def formatear(v):
    return f'{v:.4f}' if isinstance(v, float) else str(v)


def geometria(t):
    n = len(t.columns)
    # Primera columna de etiqueta más ancha; las demás se distribuyen exactamente.
    widths = [2600] + [(9360 - 2600) // (n-1)] * (n-1) if n > 1 else [9360]
    widths[-1] += 9360 - sum(widths)
    t.autofit = False
    pr = t._tbl.tblPr
    for tag, attrs in [('tblW', {'w': '9360', 'type': 'dxa'}),
                       ('tblInd', {'w': '120', 'type': 'dxa'}),
                       ('tblLayout', {'type': 'fixed'})]:
        el = pr.find(qn('w:' + tag))
        if el is None:
            el = OxmlElement('w:' + tag)
            pr.append(el)
        for k, v in attrs.items():
            el.set(qn('w:' + k), v)
    margins = OxmlElement('w:tblCellMar')
    for tag, val in [('top', 80), ('bottom', 80), ('start', 120), ('end', 120)]:
        el = OxmlElement('w:' + tag); el.set(qn('w:w'), str(val)); el.set(qn('w:type'), 'dxa'); margins.append(el)
    pr.append(margins)
    grid = t._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for w in widths:
        el = OxmlElement('w:gridCol'); el.set(qn('w:w'), str(w)); grid.append(el)
    for i, row in enumerate(t.rows):
        for cell, w in zip(row.cells, widths):
            cell.width = Inches(w / 1440)
            cell._tc.get_or_add_tcPr().find(qn('w:tcW')).set(qn('w:w'), str(w))
            for p in cell.paragraphs:
                p.style = 'CompactTable'
            if i == 0:
                shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), 'F2F4F7'); cell._tc.get_or_add_tcPr().append(shade)
        no_split = OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(no_split)
    repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)


def crear_docx(nombre, subtitulo, paginas):
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)
    s.header_distance = s.footer_distance = Inches(.492)
    # standard_business_brief + editorial_cover; CompactTable/Caption son overrides.
    presets = {'Normal': (11, 0, 6, 1.10, '202A35'), 'Title': (26, 0, 12, 1.1, '0B2545'),
               'Subtitle': (13, 0, 8, 1.1, '555555'), 'Heading 1': (16, 16, 8, 1.1, '2E74B5'),
               'Heading 2': (13, 12, 6, 1.1, '2E74B5'), 'Heading 3': (12, 8, 4, 1.1, '1F4D78'),
               'Caption': (9, 4, 4, 1.1, '555555')}
    for name, (size, before, after, line, color) in presets.items():
        st = d.styles[name]; st.font.name = 'Calibri'; st.font.size = Pt(size); st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before, st.paragraph_format.space_after = Pt(before), Pt(after)
        st.paragraph_format.line_spacing = line
        st.paragraph_format.widow_control = True
    st = d.styles.add_style('CompactTable', 1)
    st.base_style = d.styles['Normal']; st.font.size = Pt(8.5)
    st.paragraph_format.space_before = Pt(0); st.paragraph_format.space_after = Pt(3); st.paragraph_format.line_spacing = 1.0
    h = s.header.paragraphs[0]; h.text = 'FP-UNA · Ciencia de Datos · Paraguay 2021'; h.style = 'Caption'
    footer = s.footer.paragraphs[0]; footer.alignment = 2
    footer.add_run('Página ')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    footer.style = 'Caption'
    d.add_paragraph('UNIVERSIDAD NACIONAL DE ASUNCIÓN', 'Subtitle')
    d.add_paragraph('Facultad Politécnica · Ingeniería Informática', 'Subtitle')
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(44)
    d.add_paragraph('Factores asociados a la gravedad de las víctimas en los accidentes de tránsito en Paraguay (2021)', 'Title')
    d.add_paragraph(subtitulo, 'Subtitle')
    d.add_paragraph('Asignatura: Ciencia de Datos (Electiva) · Curso TQ')
    d.add_paragraph('Integrantes: ' + AUTORES)
    d.add_paragraph('Legajos: no proporcionados para esta revisión. Deben incorporarse antes de presentar.')
    d.add_paragraph('Fecha de la versión: ' + FECHA)
    d.add_paragraph('Resultados reproducidos. Interpretación acotada validada por el grupo.')
    d.add_page_break()
    d.add_heading('Índice', level=1)
    for idx, (titulo, _) in enumerate(paginas, 3):
        d.add_paragraph(f'{titulo}  ................................................................  {idx}')
    d.add_paragraph('El índice corresponde a la composición paginada de esta versión; verificarlo después de editar la carátula.', 'Caption')
    for titulo, elementos in paginas:
        d.add_page_break()
        d.add_heading(titulo, level=1)
        for item in elementos:
            if item[0] == 'p':
                d.add_paragraph(limpiar(item[1]))
            elif item[0] == 't':
                df, cap = item[1], item[2]
                d.add_paragraph(cap, 'Caption')
                t = d.add_table(rows=1, cols=len(df.columns)); t.style = 'Table Grid'
                for cell, col in zip(t.rows[0].cells, df.columns):
                    cell.text = str(col)
                for _, row in df.iterrows():
                    for cell, val in zip(t.add_row().cells, row):
                        cell.text = formatear(val)
                geometria(t)
            elif item[0] == 'i':
                d.add_picture(BytesIO(FIGURAS[item[1]]), width=Inches(6.5))
                d.add_paragraph(item[2], 'Caption')
    d.core_properties.title = subtitulo
    d.core_properties.author = 'Alan Alcaraz; Leandro Ferreira; Jorge Rios'
    d.core_properties.subject = 'Versión técnica reproducida para revisión académica'
    d.save(ruta_informe(nombre, '.docx'))
    return 2 + len(paginas)


def crear_pdf(nombre, subtitulo, paginas):
    """Alternativa cuando no hay LibreOffice: mismo contenido, maquetación PDF propia.

    No se presenta como una conversión o revisión visual del DOCX.
    """
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from xml.sax.saxutils import escape
    from PIL import Image as PILImage
    fonts = Path('C:/Windows/Fonts')
    if (fonts / 'calibri.ttf').exists():
        pdfmetrics.registerFont(TTFont('Informe', str(fonts / 'calibri.ttf')))
        pdfmetrics.registerFont(TTFont('InformeBold', str(fonts / 'calibrib.ttf')))
        pdfmetrics.registerFontFamily('Informe', normal='Informe', bold='InformeBold', italic='Informe', boldItalic='InformeBold')
        font, bold = 'Informe', 'InformeBold'
    else:
        font, bold = 'Helvetica', 'Helvetica-Bold'
    styles = getSampleStyleSheet()
    body = ParagraphStyle('CuerpoInforme', fontName=font, fontSize=11, leading=12.1, spaceAfter=6,
                          textColor=HexColor('#202A35'), alignment=TA_LEFT)
    heading = ParagraphStyle('TituloInforme', parent=body, fontName=bold, fontSize=16, leading=18,
                             spaceBefore=16, spaceAfter=8, textColor=HexColor('#2E74B5'), keepWithNext=True)
    title = ParagraphStyle('PortadaInforme', parent=body, fontSize=26, leading=29, spaceAfter=12, textColor=HexColor('#0B2545'))
    caption = ParagraphStyle('PieInforme', parent=body, fontSize=9, leading=10.5, spaceBefore=4, spaceAfter=4, textColor=HexColor('#555555'))
    small = ParagraphStyle('TablaInforme', parent=body, fontSize=8.5, leading=10, spaceAfter=0)

    def p(s, style=body):
        return Paragraph(escape(limpiar(s)).replace('\n', '<br/>'), style)

    story = [p('UNIVERSIDAD NACIONAL DE ASUNCIÓN'), p('Facultad Politécnica · Ingeniería Informática'), Spacer(1, 44),
             p('Factores asociados a la gravedad de las víctimas en los accidentes de tránsito en Paraguay (2021)', title),
             p(subtitulo, heading), p('Asignatura: Ciencia de Datos (Electiva) · Curso TQ'), p('Integrantes: ' + AUTORES),
             p('Legajos: no proporcionados para esta revisión. Deben incorporarse antes de presentar.'),
             p('Fecha de la versión: ' + FECHA), p('Resultados reproducidos. Interpretación acotada validada por el grupo.'), PageBreak(), p('Índice', heading)]
    for idx, (titulo_p, _) in enumerate(paginas, 3):
        story.append(p(f'{titulo_p} ................................................................ {idx}'))
    for titulo_p, items in paginas:
        story.extend([PageBreak(), p(titulo_p, heading)])
        for item in items:
            if item[0] == 'p': story.append(p(item[1]))
            elif item[0] == 't':
                df = item[1]; story.append(p(item[2], caption))
                data = [[p(x, small) for x in df.columns]] + [[p(formatear(x), small) for x in row] for row in df.itertuples(index=False, name=None)]
                n = len(df.columns); widths = [130] + [(468-130)/(n-1)] * (n-1) if n > 1 else [468]
                t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), HexColor('#F2F4F7')),
                         ('GRID', (0,0), (-1,-1), .4, HexColor('#C5CBD1')), ('VALIGN', (0,0), (-1,-1), 'TOP'),
                         ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
                         ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
                story.extend([t, Spacer(1, 6)])
            else:
                datos = FIGURAS[item[1]]
                with PILImage.open(BytesIO(datos)) as im: width, height = im.size
                story.extend([Image(BytesIO(datos), width=468, height=468*height/width), p(item[2], caption)])

    def furniture(canvas, doc):
        canvas.setFont(font, 9); canvas.setFillColor(HexColor('#555555'))
        canvas.drawString(72, 760, 'FP-UNA · Ciencia de Datos · Paraguay 2021')
        canvas.drawRightString(540, 36, f'Página {doc.page}')
    pdf = SimpleDocTemplate(str(ruta_informe(nombre, '.pdf')), pagesize=(612,792), topMargin=72, bottomMargin=72,
                            leftMargin=72, rightMargin=72, title=subtitulo, author=AUTORES)
    pdf.build(story, onFirstPage=furniture, onLaterPages=furniture)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', action='store_true', help='Maquetar PDF con ReportLab cuando no hay conversor Word/LibreOffice.')
    parser.add_argument('--guia-local', action='store_true', help='Crear opcionalmente una guía en docs/local/, fuera de Git y del ZIP.')
    args = parser.parse_args()
    DOCS.mkdir(exist_ok=True)
    global FIGURAS
    resultados = leer_resultados()
    FIGURAS = leer_figuras()
    tablas = resultados['tablas']
    m, cv, b = tablas['metricas_test'], tablas['validacion'], tablas['brechas']
    g, cm = tablas['gini_variables'], tablas['matrices']
    se = tablas['errores_sexo'].reset_index()
    ed = tablas['errores_edad'].reset_index().sort_values('tasa_error', ascending=False)
    sens = tablas['sensibilidad_todos'].groupby('Modelo')[['F1_macro', 'AUC_ROC']].mean()
    sel = resultados['seleccion']
    w = sel['modelo']; r = m.loc[w]; base = m.loc['Línea Base (Dummy)']; z = cm.loc[w]
    nombres = {'Línea Base (Dummy)': 'Dummy', 'Regresión Logística': 'Logística', 'Árbol de Decisión': 'Árbol',
               'Random Forest': 'Bosque', 'Naive Bayes Categórico': 'Naive Bayes'}
    mt = m[['Accuracy', 'Precision (Fallecido)', 'Recall (Fallecido)', 'F1-Score (Fallecido)', 'F1-Macro', 'ROC-AUC']].copy()
    mt.index = mt.index.map(nombres)
    mt.columns = ['Accuracy', 'Prec. 1', 'Recall 1', 'F1 clase 1', 'F1 macro', 'AUC']
    mt = mt.reset_index(names='Modelo')
    cvt = cv[['F1-Macro (Train CV)', 'F1-Macro (Validación CV)', 'Desvío CV']].copy()
    cvt.index = cvt.index.map(nombres); cvt.columns = ['Train CV', 'Validación CV', 'Desvío CV']; cvt = cvt.reset_index(names='Modelo')
    resumen = (f'Se seleccionó {w} por F1 macro de validación cruzada {cv.loc[w, "F1-Macro (Validación CV)"]:.4f}. '
        f'En la reserva interna obtuvo F1 macro {r["F1-Macro"]:.4f}, frente a {base["F1-Macro"]:.4f} del Dummy '
        f'(diferencia {r["F1-Macro"]-base["F1-Macro"]:+.4f}); recall de fallecidos {r["Recall (Fallecido)"]:.4f}, '
        f'precisión {r["Precision (Fallecido)"]:.4f} y AUC {r["ROC-AUC"]:.4f}. La mejora es descriptiva del protocolo, '
        'sin prueba de superioridad poblacional ni validación externa.')
    limitacion = ('Las 5.493 filas reconstruyen frecuencias de sexo, grupo de edad y desenlace, no son microdatos originales. '
        'Solo existen 16 perfiles predictivos. La partición aleatoria distribuye frecuencias de esos mismos perfiles en train y test. '
        'No acredita capacidad para anticipar desenlaces de personas o siniestros nuevos. La reserva ya fue inspeccionada en versiones anteriores; '
        'no se presenta como holdout virgen. Ninguna unión artificial vincula demografía, zona y vehículo.')
    diseno = ('Se conservó la partición 80/20 estratificada por desenlace, con semilla 42: 4.394 filas de entrenamiento y '
        '1.099 de prueba (196 fallecidos). En entrenamiento se fijaron cinco pliegues estratificados idénticos para todos. '
        'GridSearchCV optimiza F1 macro; se cierra la selección antes de calcular las métricas de test en esta ejecución. '
        'No se cambian umbrales ni hiperparámetros a partir de la reserva. Las medias CV de la mejor grilla tienen sesgo de selección; '
        'no equivalen a una evaluación anidada. No existen fechas individuales que permitan una partición cronológica válida.')
    preparacion = ('Se utilizan únicamente sexo y grupo_edad. Se excluyen id_victima y gravedad por ser identificador y objetivo directo; '
        'es_hombre, es_adulto_mayor y edad_orden duplican las variables disponibles. Ignorado se conserva como edad no informada. '
        'OneHotEncoder(drop=first, handle_unknown=ignore) se ajusta dentro de los pipelines de los tres modelos originales. '
        'No se requiere escalado de indicadores binarios o árboles. No se silencian advertencias globalmente.')
    modelos = ('Logística: modelo discriminativo con efectos aditivos en log-odds, regularización L2. Árbol: reglas con interacciones '
        'y control de complejidad por profundidad y hojas mínimas. Random Forest: ensamble de árboles para reducir varianza; pertenece a '
        'la familia de árboles. Naive Bayes categórico: modelo generativo que supone independencia de sexo y edad dado el desenlace. '
        'OrdinalEncoder asigna índices nominales; sumar uno reserva el cero para categorías desconocidas. No hay interpretación ordinal '
        'de esos números. Suavizado alpha evita frecuencias condicionales nulas; min_categories=[3,9] reserva el dominio conocido más desconocido.')
    balance = ('La prevalencia es 980/5.493 = 17,84 %. Los tres modelos originales usan class_weight=balanced; Naive Bayes usa prior '
        '0,5/0,5 para dar igual prioridad a las clases, conservando conteos condicionales naturales. El umbral permanece en la regla '
        'predict del estimador. Los puntajes no se presentan como probabilidades absolutas calibradas. No se utiliza SMOTE.')
    metricas = ('Accuracy mide aciertos totales; precisión de clase 1 mide la fracción de fatalidades entre predicciones positivas; '
        'recall mide la fracción de fatalidades detectadas; F1 combina precisión y recall. F1 macro promedia los F1 de ambas clases. '
        'AUC mide ordenamiento de puntuaciones, no calibración. Specificity y balanced accuracy complementan el desbalance. '
        'Brier evalúa error cuadrático de la puntuación; Average Precision resume la curva PR. Las tablas completas quedan embebidas en el notebook ejecutado.')
    errores = (f'En el seleccionado: TN={int(z.TN)}, FP={int(z.FP)}, FN={int(z.FN)}, TP={int(z.TP)}. '
        'TN: lesión clasificada herido; TP: fatalidad clasificada fallecido; FP: lesión clasificada fallecido; FN: fatalidad clasificada herido. '
        'El FN tiene prioridad académica al estudiar omisiones de fatalidad; no se asigna un costo clínico ni se optimiza un umbral en test. '
        f'La mayor tasa global de error por edad aparece en {ed.iloc[0].grupo_edad}: {ed.iloc[0].tasa_error:.2%}, '
        f'con n={int(ed.iloc[0].n)}. Tasa de error global y tasa FN entre fallecidos tienen denominadores diferentes.')
    solapamiento = resultados['solapamiento']
    sexo_ind = se.set_index('sexo')
    edades_jovenes = ed[ed.grupo_edad.isin(['De 0 a 13 anos', 'De 14 a 17 anos', 'De 18 a 29 anos'])]
    errores += (f' El árbol omite {int(sexo_ind.loc["Mujer", "FN"])} de {int(sexo_ind.loc["Mujer", "fallecidos"])} fatalidades entre mujeres '
        f'(recall={sexo_ind.loc["Mujer", "recall_fallecidos"]:.4f}), frente a recall {sexo_ind.loc["Hombre", "recall_fallecidos"]:.4f} en hombres. '
        f'En 0-29 años omite {int(edades_jovenes.FN.sum())} de {int(edades_jovenes.fallecidos.sum())} fatalidades. '
        'Este fallo sistemático hace especialmente inadecuado utilizar la clasificación para decisiones individuales.')
    errores += (f' Los dos grupos se superponen: {solapamiento["interseccion"]} omisiones son mujeres de 0-29 años. '
        f'La unión contiene {solapamiento["mujeres"]}+{solapamiento["edades_0_29"]}-{solapamiento["interseccion"]}'
        f'={solapamiento["union"]} filas, no la suma directa. Los {solapamiento["restantes"]} FN restantes son hombres con edad ignorada. '
        'Son conteos del protocolo sobre frecuencias reconstruidas, no expedientes individuales.')

    brecha = (f'El seleccionado tiene F1 macro train {b.loc[w, "F1-Macro (Train)"]:.4f}, CV '
        f'{cv.loc[w, "F1-Macro (Validación CV)"]:.4f} y test {r["F1-Macro"]:.4f}. '
        f'Train menos test = {b.loc[w, "Brecha Absoluta"]:+.4f}; train CV menos validación CV = '
        f'{cv.loc[w, "Brecha Sobreajuste (CV)"]:+.4f}. Una brecha pequeña puede resultar de repetir perfiles, '
        'no de generalización robusta. Los pliegues no son réplicas independientes de otras poblaciones.')
    principal = g.loc['Árbol de Decisión'].idxmax()
    interpretacion = (f'En el árbol, {principal} tiene la mayor importancia Gini ({g.loc["Árbol de Decisión", principal]:.4f}). '
        'Esta importancia suma reducciones de impureza de sus indicadores y no tiene signo. Random Forest ofrece otra agregación, '
        'no una medida causal. La permutación desordena cada variable original y cuantifica caída de F1 macro con 30 repeticiones. '
        'Puede generar combinaciones artificiales y verse afectada por dependencia entre variables. Sus desvíos son de permutación, '
        'no intervalos poblacionales. Ninguna importancia demuestra que sexo o edad causen fatalidades.')
    logits = ('Los coeficientes logísticos se interpretan respecto de Hombre y De 0 a 13 anos, referencias del encoder. '
        'exp(beta) representa un odds ratio del modelo regularizado y ponderado, condicionado por sus otras covariables; '
        'no es el OR sin ajuste de la Fase 2, ni una razón de riesgos ni una prueba de significancia. '
        'La coincidencia de señales por sexo y edad con Fase 2 no hace equivalentes asociación e importancia predictiva.')
    sensibilidad = (f'GroupKFold de cuatro pliegues deja perfiles completos fuera del entrenamiento. Para {w}, '
        f'F1 macro medio = {sens.loc[w, "F1_macro"]:.4f} y AUC media = {sens.loc[w, "AUC_ROC"]:.4f}. '
        'Se repite con todos los candidatos manteniendo hiperparámetros fijos. Se ajusta cada transformación dentro del pliegue; '
        'una categoría desconocida carece de señal aprendida (OHE la representa por ceros; NB usa el índice reservado y suavizado). '
        'La búsqueda previa vio todos los perfiles de train; este análisis condicionado no es una validación anidada de perfiles.')
    sensibilidad += ' Con OHE drop=first, una categoría desconocida queda además indistinguible de la referencia en ese bloque de indicadores.'
    calibracion = (f'El Brier del seleccionado es {r["Brier"]:.4f}; el Dummy obtiene {base["Brier"]:.4f}. '
        'La gráfica compara puntuación media y fracción observada usando cinco intervalos uniformes; puede haber intervalos vacíos '
        'porque existen pocas puntuaciones distintas. No se ajusta calibración con test. La mejora de F1 o recall no garantiza '
        'calibración ni utilidad para decisiones individuales.')
    vehicular = ('12.2.10 registra 539 víctimas de siniestros protagonizados por motociclistas: 384 heridos y 155 fallecidos '
        '(28,76 %). 12.2.5 registra 1.324 víctimas en su cobertura: 1.055 heridos y 269 fallecidos. La resta histórica da '
        '671 heridos y 114 fallecidos (14,52 %). Esa resta es aritmética; la equivalencia de cobertura y vehículo individual no '
        'está demostrada. Se conserva como contexto exploratorio, sin enlazar sus 1.324 filas con las 5.493 demográficas.')
    respuesta = ('La pregunta original plantea la asociación del usuario motociclista, perfil demográfico y geografía con el desenlace fatal. '
        'Se responde parcialmente: las tablas documentan asociaciones separadas, y sexo/edad ofrecen una capacidad retrospectiva limitada. '
        'No se puede estimar el efecto conjunto ni la probabilidad de una víctima futura al no existir microdatos vinculados. '
        'Volumen de víctimas, proporción de fallecidos entre víctimas y riesgo de accidente en la población son conceptos diferentes.')
    futuro = ('El uso admisible de estos artefactos es docente, retrospectivo y de comparación de procedimientos. Se excluyen triaje, seguros '
        'y vigilancia por perfil. Para avanzar se necesitan registros genuinos vinculados de víctima y siniestro con vehículo real, '
        'fechas, casco/cinturón, velocidad, lesión inicial y tiempos de atención; diccionarios de cobertura; validación externa temporal '
        'y de calibración. Se debe controlar subregistro, selección de víctimas registradas y sesgos por sexo, edad y territorio.')
    ia = ('Se utilizó Codex como apoyo en auditoría, implementación, depuración, documentación y propuestas de interpretación. '
        'El grupo validó el alcance retrospectivo, la incorporación de Naive Bayes y la interpretación acotada de los resultados. Debe revisar y comprender personalmente '
        'las decisiones, métricas e interpretaciones; esa validación no acredita automáticamente el dominio personal de todo el contenido. La asistencia '
        'excedió sintaxis y redacción: corresponde al grupo comprobar la compatibilidad con el apartado 11 y consultar al docente '
        'si procede. No se atribuyen a los integrantes decisiones o validaciones que no hayan comunicado.')
    refs = ('INE. Anuario 2021 - Estadísticas policiales y de accidentes de tránsito. Tablas originales del repositorio. Catálogo: ' + SOURCE,
        'Scikit-learn. Documentación oficial: https://scikit-learn.org/stable/modules/naive_bayes.html ; '
        'https://scikit-learn.org/stable/modules/cross_validation.html ; '
        'https://scikit-learn.org/stable/modules/permutation_importance.html ; https://scikit-learn.org/stable/modules/calibration.html . Consulta: 16/10/2026.',
        'Consigna académica Proyecto_DataScience_Tres_Fases.pdf, apartados 7, 9.3, 9.5, 10, 11 y 12. '
        'Antecedentes: notebooks Fase1_Accidentes_Transito y Fase2_Analisis_Inferencial; tabla y JSON consolidados de Fase 2.')
    hp = pd.DataFrame([{'Modelo': nombres[k], 'Hiperparámetros elegidos por CV': str(v).replace('clf__', '')} for k, v in sel['hiperparametros'].items()])
    matriz_reporte = pd.DataFrame({'Real / Predicho': ['Herido (0)', 'Fallecido (1)'],
                                   'Herido (0)': [int(z.TN), int(z.FN)], 'Fallecido (1)': [int(z.FP), int(z.TP)]})
    errores_sexo_reporte = se[['sexo', 'n', 'FN', 'FP', 'tasa_error', 'recall_fallecidos']].rename(columns={
        'sexo': 'Sexo', 'n': 'N', 'tasa_error': 'Error global', 'recall_fallecidos': 'Recall fatal'})
    p3 = [
        ('1. Introducción, datos y correcciones', [text('Objetivo: comparar modelos supervisados de desenlace fatal con una línea base en los conteos de Paraguay de 2021, dando continuidad a CRISP-DM.'), text(resumen), text(limitacion), text('No hubo devolución docente de Fase 2, confirmado por el grupo. Se corrigieron en Fase 3 la descripción de familias, la denominación de test independiente y los faltantes de inferencia, evaluación y documentación. Los notebooks históricos se preservaron.'), text('La tabla 12.2.1 procede de la Policía Nacional; las tablas territoriales y de siniestros con motociclistas, de la Patrulla Caminera. Comparten año, pero no necesariamente universo o unidad de registro.')]),
        ('2. Preparación y diseño experimental', [text(preparacion), text(diseno), text(balance), text('Calidad: reconstrucción desde 12.2.1 idéntica al CSV histórico, incluidos orden e identificador; comprobación de 4.513 heridos, 980 fallecidos, dos sexos, ocho edades y 16 perfiles. Se verifica consistencia entre gravedad y es_fallecido y ausencia de nulos en predictores/objetivo. Solo se conserva el orden para reproducir la partición, sin usarlo como predictor.')]),
        ('3. Modelos e hiperparámetros', [text(modelos), tabla(hp, 'Tabla F3-1. Configuraciones seleccionadas.'), text('Grillas: logística C={0,01; 0,1; 1; 5; 10}, lbfgs, max_iter=1000; árbol profundidad={2;3;4;5;6}, hoja mínima={10;25;50}; bosque n_estimators={50;100;150}, profundidad={3;4;5}, hoja={10;25}; NB alpha={0,1;1;10}. Semilla 42 y n_jobs=1. Se conservó el experimento previo, sin ampliar grillas para perseguir test.')]),
        ('4. Validación y comparación de resultados', [tabla(cvt, 'Tabla F3-2. F1 macro en los cinco pliegues de entrenamiento.'), tabla(mt, 'Tabla F3-3. Evaluación en la misma reserva interna (n=1.099).'), text(resumen), text(metricas)]),
        ('5. Discriminación y brecha de rendimiento', [imagen('F3-01', 'Figura F3-01. ROC y Precision-Recall de todos los modelos en la misma prueba. Las leyendas ROC incluyen AUC; la línea PR representa prevalencia.'), text('Las curvas revelan capacidad de ordenamiento limitada. La exactitud de la mayoría puede ser elevada sin detectar ninguna fatalidad. El gráfico PR debe interpretarse en relación con la prevalencia de fallecidos y no como curva de calibración.'), imagen('F3-07', 'Figura F3-07. F1 macro de entrenamiento, validación y prueba.'), text(brecha)]),
        ('6. Análisis de errores por perfil', [text(errores), tabla(matriz_reporte, 'Tabla F3-4A. Matriz de confusión del seleccionado en prueba.'), tabla(errores_sexo_reporte, 'Tabla F3-4B. Errores por sexo, con denominadores.'), imagen('F3-04', 'Figura F3-04. Tasa de clasificación errónea y tasa de omisión entre fallecidos, por edad y sexo.'), text('Las tablas del notebook detallan los errores por perfil y sus residuos absolutos. Si el modelo asigna una sola clase a un perfil, falla en el desenlace contrario a su predicción, que puede ser mayoritario por la ponderación de clases. Con dos predictores no distingue gravedad del choque, protección o atención dentro del perfil; no puede explicar historias individuales.')]),
        ('7. Interpretabilidad y continuidad inferencial', [text(interpretacion), imagen('F3-05', 'Figura F3-05. Importancia Gini por variable y permutación del seleccionado. Las barras de error de permutación son desvíos de 30 repeticiones.'), text(logits), text('La Fase 2 informó OR por sexo 2,0370 y V de Cramér 0,0971. La dirección de asociación es compatible con señal demográfica, pero un efecto pequeño y perfiles compartidos limitan discriminación. Importancia predictiva no es una estimación del mecanismo causal ni del riesgo en población general.')]),
        ('8. Sensibilidad y calibración', [text(sensibilidad), imagen('F3-06', 'Figura F3-06. Diagnóstico de calibración y Brier de las puntuaciones originales, sin reajuste.'), text(calibracion), text('La equivalencia entre logística expandida y frecuencias ponderadas se comprobó mediante un ajuste adicional solo en train; sus diferencias numéricas quedan en las salidas del notebook. No es una validación independiente: demuestra que expandir no crea nueva información.')]),
        ('9. Discusión y conclusiones académicas', [text(resumen), text(vehicular), text(respuesta), text(futuro), text('La prueba ya observada y la optimización dentro de CV impiden presentar estas métricas como garantía externa. El ejercicio demuestra un proceso reproducible y expone su límite informativo. El grupo validó la interpretación acotada: mejora de F1 macro dentro del protocolo, capacidad limitada y ausencia de uso individual o generalización externa.')]),
        ('10. Reproducibilidad, referencias y uso de IA', [text('Ejecutar desde la raíz con Python 3.12.1 y las versiones declaradas: preparar_datos.py, ejecutar_fase3.py, unittest y generar_documentos.py --pdf. El notebook conserva resultados, grillas, particiones y figuras embebidas; output/fase3 contiene el HTML y el modelo ganador serializado. El CLI inferencia.py valida categorías y carga el joblib sin abrir Jupyter. README documenta comandos.'), text('Faltan legajos y revisión personal de las conclusiones. Los Word históricos anunciados por el grupo se incorporarán cuando estén disponibles; el integrador actual usa notebooks y resultados existentes. La fecha del campus debe confirmarse: la consigna dice viernes 24 de octubre sin año compatible con el contexto 2026.'), *[text(x) for x in refs], text(ia)])]
    f2 = json.loads((ROOT / 'output/fase2/resultados_fase2_consolidados.json').read_text(encoding='utf-8'))['hipotesis']
    f2table = pd.DataFrame([{'Hipótesis': h['hipótesis'], 'Estadístico': h['estadístico'], 'p Bonferroni': f'{h["p_valor_ajustado_bonferroni"]:.3g}', 'Efecto histórico': h['tamaño_del_efecto']} for h in f2])
    demo = pd.read_csv(ROOT / 'output/victimas_individual_limpio.csv')
    sexo = demo.groupby('sexo').es_fallecido.agg(['size', 'sum']).reset_index()
    sexo.columns = ['Sexo', 'Víctimas', 'Fallecidos']; sexo['Fracción fatal'] = sexo.Fallecidos / sexo['Víctimas']
    edad = demo.groupby('grupo_edad').es_fallecido.agg(['size', 'sum']).reset_index()
    edad.columns = ['Grupo etario', 'Víctimas', 'Fallecidos']; edad['Fracción fatal'] = edad.Fallecidos / edad['Víctimas']
    pi = [
        ('1. Problema y pregunta de investigación', [text('Los siniestros viales generan lesiones y fallecimientos. El proyecto caracteriza las víctimas registradas en Paraguay en 2021 y distingue descripción, asociación y clasificación retrospectiva. No dispone de población expuesta o kilómetros recorridos para estimar incidencia de accidentes.'), text('Pregunta original: ¿En qué medida la condición de usuario (motociclista frente a otros vehículos), el perfil biológico (sexo, grupo etario) y la localización geográfica (Asunción, Central e Interior) se asocian con una mayor probabilidad de fallecer en un siniestro vial en Paraguay durante 2021?'), text('Objetivo general: examinar asociaciones del desenlace en las tablas disponibles. Objetivos específicos: preparar fuentes y describir distribuciones; contrastar asociaciones en sus universos separados; comparar clasificadores del desenlace demográfico frente a una base; comunicar límites y necesidades de información.'), text('CRISP-DM articula comprensión del problema, comprensión y preparación de datos, análisis, modelado, evaluación y comunicación. La Fase 3 acota el objetivo predictivo inicial al alcance que permiten datos agregados.'), text(limitacion)]),
        ('2. Fuentes, cobertura y calidad', [text('Fuente pública: INE, Anuario 2021. 12.2.1: conteos demográficos de Policía Nacional (5.493 víctimas). 12.2.2 a 12.2.12: tablas de Patrulla Caminera según su encabezado y metadatos. 12.2.5: 1.324 víctimas Central/Interior; 12.2.6: 1.491 víctimas incluidas Asunción, Central e Interior. Los totales distintos no se fusionan ni se imputan como faltantes de una tabla común.'), text('Los originales únicos se conservan en data/; se retiraron doce copias idénticas de data/raw/. Se parsean separadores de miles, filas TOTAL y encabezados repetidos. Los guiones requieren contexto: no son una edad o un valor individual. Ignorado conserva edad desconocida. Las filas repetidas de la expansión son esperadas y no se deduplican como si fueran errores.'), text(preparacion), text('La verificación nueva reconstruye íntegramente 12.2.1 sin ejecutar los notebooks históricos, de modo que las entregas previas no se alteran. Las pruebas verifican por SHA-256 que las Fases 1 y 2 permanecen intactas.')]),
        ('3. Fase 1: preparación y descripción demográfica', [text('Se resume el desenlace en la tabla demográfica expandida, cuya unidad sustantiva es el conteo de cada combinación. Los identificadores consecutivos son auxiliares, sin identidad personal.'), tabla(sexo, 'Tabla I-1. Conteos demográficos por sexo, recalculados desde el CSV auditado.'), tabla(edad, 'Tabla I-2. Conteos por edad; Ignorado no representa una edad inferior.'), text('Los jóvenes pueden concentrar mayor volumen de víctimas sin presentar la mayor proporción fatal. La interpretación separa carga absoluta y composición del desenlace. Las proporciones corresponden a víctimas registradas, no al riesgo por habitante o usuario vial.')]),
        ('4. Fase 1: contexto temporal y territorial', [text('El archivo siniestros_mensual_2021.csv contiene los 12 meses de 2021. La tabla 12.2.2 totaliza 1.942 siniestros y octubre alcanza 201. La Ruta PY02 registra 711 hechos, 36,61 % de ese total. Son estadísticas descriptivas de su cobertura; no se prueban mecanismos de movilidad, pandemia o velocidad con estas tablas.'), tabla(pd.read_csv(ROOT / 'output/victimas_zona_resumen.csv'), 'Tabla I-3. Contexto territorial de 12.2.6, universo de 1.491 víctimas.'), text('La concentración del volumen y la diferencia territorial justifican investigar condiciones de vía, exposición y atención. No prueban que una ruta o lugar cause mayor gravedad, ni permiten trasladar la localización de una tabla al perfil demográfico de otra.'), text('Las visualizaciones históricas permanecen en las Fases 1 y 2. Este integrador resume sus conteos, corrige el alcance interpretativo en esta versión y no reescribe sus entregas.')]),
        ('5. Fase 2: contrastes y tamaños del efecto', [text('Se conservan como antecedentes los cuatro contrastes de resultados_fase2_consolidados.json y tabla_resumen_fase2.csv. Nivel alpha 0,05, corrección principal Bonferroni de cuatro pruebas y ajuste complementario Benjamini-Hochberg. La tabla siguiente transcribe resultados históricos: no se afirma una reejecución completa de Fase 2 en esta revisión.'), tabla(f2table, 'Tabla I-4. Resultados inferenciales históricos, con efecto y p ajustado.'), text('H1 compara Interior y Metropolitana; H2 sexo; H3 grupos vehiculares derivados; H4 edad codificada y desenlace. En H2 el intervalo bootstrap del OR histórico es [1,6787; 2,5066], con 10.000 remuestreos; el clásico [1,6729; 2,4803]. Ambos acompañan OR 2,0370, con V de Cramér 0,0971. Evidencia estadística no equivale a asociación grande o relevancia predictiva.')]),
        ('6. Fase 2: alcance de la inferencia', [text('Para tablas de contingencia, la Fase 2 verificó frecuencias esperadas; Shapiro y Levene no son requisitos de chi-cuadrado. Para edad codificada se reportaron Shapiro, Levene y una alternativa de rangos. La codificación representa intervalos de diferente amplitud, no edades exactas; Ignorado exige exclusión o tratamiento separado en cualquier análisis ordinal.'), text('La expansión reproduce exactamente las frecuencias de contingencia: el tamaño de la tabla no equivale al número de perfiles. Las pruebas clásicas suponen un mecanismo de muestreo y unidades generadoras cuya independencia no se acredita solo con expandir conteos. Un bootstrap de filas expandidas reproduce un supuesto multinomial sobre la tabla, sin capturar subregistro, agrupación por siniestro o incertidumbre de cobertura. Por ello los p e intervalos históricos son resultados condicionados, no garantías sobre toda la población.'), text(vehicular), text('Posibles confusores: exposición vial, casco y cinturón, velocidad, tipo de vía, lesión inicial, acceso a atención y cobertura institucional. Ninguno puede controlarse conjuntamente con los datos disponibles. No hubo devolución formal docente de Fase 2; esta revisión contextualiza sin atribuir correcciones inexistentes.')]),
        ('7. Fase 3: diseño y familias', [text(diseno), text(modelos), text(balance), tabla(hp, 'Tabla I-5. Hiperparámetros ganadores del experimento demográfico.')]),
        ('8. Fase 3: resultados reproducidos', [tabla(cvt, 'Tabla I-6. F1 macro de validación cruzada.'), tabla(mt, 'Tabla I-7. Resultados en la reserva interna de 1.099 filas.'), text(resumen), text(metricas)]),
        ('9. Fase 3: errores y sobreajuste', [text(errores), imagen('F3-04', 'Figura F3-04. Errores por sexo y grupo etario.'), text(brecha), text('Las tablas por perfil completo del notebook muestran las combinaciones con clasificación sistemática de una clase. No corresponden a expedientes individuales. La escasez de predictores impide distinguir circunstancias entre víctimas del mismo perfil.')]),
        ('10. Fase 3: interpretación y sensibilidad', [text(interpretacion), imagen('F3-05', 'Figura F3-05. Dos medidas de relevancia predictiva con alcances distintos.'), text(logits), text(sensibilidad)]),
        ('11. Integración de los tres niveles de evidencia', [text('Descripción: los conteos caracterizan víctimas y siniestros dentro de cada fuente. Inferencia: los contrastes históricos cuantifican asociaciones bajo supuestos y corrección múltiple. Predicción: los modelos asignan clases/puntajes y se comparan mediante un protocolo interno fijo. Una asociación significativa puede coexistir con AUC limitada; ni los p-valores ni las importancias prueban causalidad.'), text(respuesta), text(calibracion), imagen('F3-01', 'Figura F3-01. Discriminación limitada en los mismos perfiles reconstruidos; no equivale a validación externa.')]),
        ('12. Conclusión general y recomendaciones', [text(resumen), text('La contribución defendible es una cadena trazable desde conteos oficiales hasta evaluación comparativa, acompañada de un reconocimiento explícito de cobertura, repetición y revisión histórica del test. El objetivo de superar una base puede cumplirse en F1 macro dentro del protocolo, mientras la utilidad fuera de esa tabla permanece sin demostrar.'), text(futuro), text('El grupo debe revisar los errores por sexo y edad sin estigmatizar categorías, y distinguir incertidumbre de datos de incertidumbre algorítmica. Priorizar obtención y enlace legítimo de microdatos aporta más información potencial que aumentar la complejidad de modelos sobre 16 perfiles.'), text('El grupo validó el alcance y la interpretación acotada de estos resultados; debe revisar personalmente todo el código y texto para su defensa. Los Word históricos anunciados por el grupo aún no estaban disponibles al generar esta versión.')]),
        ('13. Reproducción, referencias y uso de IA', [text('El repositorio conserva data/, notebooks/, src/ y output/, y añade docs/ y tests/. README registra instalación, reconstrucción, kernel nuevo, HTML, inferencia, pruebas y documentos. Las versiones exactas y la partición reproducible se documentan dentro del notebook; los informes se componen a partir de tablas calculadas. No se hicieron commits ni pushes.'), *[text(x) for x in refs], text(ia), text('Antes de presentar: incorporar legajos, verificar apellidos y nomenclatura ZIP, confirmar fecha del campus y revisar personalmente las conclusiones. Los límites de 15 páginas para Fase 3 y 30 para integrador se comprueban sobre los PDF exportados, no sobre estimaciones de Word.')])]
    esperadas = {'Informe_Fase3': crear_docx('Informe_Fase3', 'Fase 3 · Análisis predictivo', p3),
                 'Informe_Integrador_DataScience': crear_docx('Informe_Integrador_DataScience', 'Informe integrador · Fases 1, 2 y 3', pi)}
    if args.pdf:
        crear_pdf('Informe_Fase3', 'Fase 3 · Análisis predictivo', p3)
        crear_pdf('Informe_Integrador_DataScience', 'Informe integrador · Fases 1, 2 y 3', pi)
    guia = f'''# Guía de defensa de Fase 3

## Relato en tres minutos
{resumen}

{limitacion}

## Algoritmos y decisiones
{modelos}

{diseno}

## Métricas
{metricas}

## Preguntas esperables
- ¿Por qué no basta accuracy? Dummy clasifica toda fatalidad como herido y aun así acierta la clase mayoritaria; contrastar F1 macro y recall.
- ¿Por qué cuatro modelos? Logística, familia de árboles (árbol y bosque) y familia generativa categórica. Bosque y árbol no acreditan dos familias independientes.
- ¿Por qué no incorporar vehículo y zona? No hay claves individuales que enlacen las fuentes; hacerlo crearía observaciones ficticias.
- ¿Se usó test una sola vez? En esta ejecución se evaluó después del cierre de CV. Se inspeccionó en versiones anteriores y por eso no se afirma reserva virgen.
- ¿Qué es un falso negativo? {int(z.FN)} fatalidades registradas fueron clasificadas herido por el seleccionado; son frecuencias reconstruidas, no expedientes.
- ¿Por qué no usar estos puntajes en clínica? No hay microdatos, calibración externa ni validación prospectiva.
- ¿Por qué no hay split temporal? La tabla demográfica no contiene fechas individuales.
- ¿CV garantiza generalización? No. Repite perfiles y además se utiliza para optimizar; GroupKFold es sensibilidad condicionada y tampoco es validación externa.
- ¿Qué significa exp(beta)? Odds ratio regularizado del modelo ponderado; no causa, razón de riesgos o prueba de significancia.
- ¿Qué hace el script de inferencia? Valida categorías, carga el pipeline desde disco y devuelve clase/puntuación académica no calibrada.

## Evidencia que deben poder explicar los tres integrantes
{errores}

{brecha}

{sensibilidad}

## Revisión personal antes de presentar
Revisar todas las decisiones e interpretaciones; incorporar legajos; verificar fecha del campus y apellidos; actualizar los Word cuando se aporten los históricos; ensayar por qué asociación, predicción y causalidad son distintas. La exposición oficial es de 15 minutos más 5 de preguntas, con participación de los tres y 12 a 18 diapositivas. Esta revisión no crea una presentación ni acredita el dominio oral.

{ia}
'''
    if args.guia_local:
        local = DOCS / 'local'
        local.mkdir(parents=True, exist_ok=True)
        (local / 'GUIA_DEFENSA_FASE3.md').write_text(guia, encoding='utf-8')
    print('Informes regenerados sin imágenes o tablas auxiliares. Páginas planificadas:', esperadas)


if __name__ == '__main__':
    main()
