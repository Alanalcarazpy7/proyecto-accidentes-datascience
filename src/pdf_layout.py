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

