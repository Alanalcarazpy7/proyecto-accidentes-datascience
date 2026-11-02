"""Crea un resumen visual de cuatro paginas a partir de resultados guardados.

No entrena modelos ni cambia la entrega principal. Requiere evidencia.json
en output/resumen_fase3, cotejada con el repositorio anterior.
"""
from pathlib import Path
import csv
import json
import html
import argparse
import hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader
import pdf_layout  # Registra las fuentes Vera incluidas en reportlab.

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/resumen_fase3'
FIG=OUT/'figuras'
NAVY='#18364A'; TEAL='#087F8C'; ORANGE='#C97028'; PALE='#EEF5F6'; GRAY='#60717C'
PAGE_W,PAGE_H=A4
LEFT=42; WIDTH=PAGE_W-84


def num(x):
    return f'{int(x):,}'.replace(',','.')


def dec(x,n=3):
    return f'{float(x):.{n}f}'.replace('.',',')


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def charts(final,ref):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    FIG.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    x=np.arange(2);w=.29
    fig,ax=plt.subplots(figsize=(7.2,2.25))
    for offset,row,label,color in [(-w/2,ref,'Referencia: 24 variables','#91A5AF'),(w/2,final,'Final: 31 variables',TEAL)]:
        values=[row['ROC_AUC'],row['F1_macro']]
        bars=ax.bar(x+offset,values,width=w,color=color,label=label)
        for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,v+.025,dec(v),ha='center',fontsize=11,fontweight='bold')
    ax.set(xticks=x,xticklabels=['AUC','F1 macro'],ylim=(0,1),ylabel='Puntuación (0 a 1)')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,1.28),ncol=2,frameon=False,fontsize=10)
    ax.set_axisbelow(True);ax.yaxis.grid(True,alpha=.15)
    fig.savefig(FIG/'comparacion_brasil.png',dpi=190,bbox_inches='tight');plt.close(fig)
    totals=[final['fallecidos'],final['n']-final['fallecidos']]
    right=np.array([final['TP'],final['TN']])/totals*100
    wrong=100-right
    fig,ax=plt.subplots(figsize=(7.2,2.05))
    y=[1,0]
    ax.barh(y,right,color=TEAL,height=.5,label='Clasificación correcta')
    ax.barh(y,wrong,left=right,color=ORANGE,height=.5,label='Clasificación equivocada')
    for pos,a,b in zip(y,right,wrong):
        ax.text(a/2,pos,dec(a,1)+' %',ha='center',va='center',color='white',fontweight='bold',fontsize=10)
        ax.text(a+b/2,pos,dec(b,1)+' %',ha='center',va='center',color='white',fontsize=7 if b<10 else 9)
    ax.set(yticks=y,yticklabels=['Fallecidos ('+num(totals[0])+')','Heridos ('+num(totals[1])+')'],xlim=(0,100),xlabel='Porcentaje dentro de cada grupo')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,1.32),ncol=2,frameon=False,fontsize=10)
    fig.savefig(FIG/'errores_brasil.png',dpi=190,bbox_inches='tight');plt.close(fig)
    importance=read_csv(ROOT/'output/tables/importancia_modelo_final.csv')[:5]
    labels={'tipo_acidente':'Tipo de choque','tipo_veiculo':'Tipo de vehículo','otros_pesados':'Otros vehículos pesados',
            'municipio':'Municipio','n_vehiculos_declarados':'Cantidad de vehículos'}
    values=[float(r['caida_AP_media']) for r in importance]
    fig,ax=plt.subplots(figsize=(7.2,1.8))
    ax.barh(range(5),values,color=TEAL,height=.65)
    ax.set(yticks=range(5),yticklabels=[labels.get(r['variable'],r['variable']) for r in importance],xlabel='Caída de AP al mezclar esa información')
    ax.invert_yaxis();ax.set_xlim(0,max(values)*1.23)
    for i,v in enumerate(values):ax.text(v+.003,i,dec(v),va='center',fontsize=9)
    fig.savefig(FIG/'importancia_brasil.png',dpi=190,bbox_inches='tight');plt.close(fig)


def paragraph(c,text,x,top,w,size=10,leading=None,color=NAVY,maxh=None):
    style=ParagraphStyle('local',fontName='Vera',fontSize=size,leading=leading or size*1.38,textColor=colors.HexColor(color))
    p=Paragraph(text,style);_,height=p.wrap(w,1000)
    if maxh is not None:assert height<=maxh+.1,(text[:90],height,maxh)
    p.drawOn(c,x,top-height)
    return top-height


def rect(c,x,top,w,h,color=PALE):
    c.setFillColor(colors.HexColor(color));c.roundRect(x,top-h,w,h,9,stroke=0,fill=1)


def page(c,index,title):
    c.setFillColor(colors.HexColor(TEAL));c.rect(0,PAGE_H-13,PAGE_W,13,fill=1,stroke=0)
    paragraph(c,'PROYECTO INTEGRADOR | FASE 3 | BRASIL',LEFT,814,WIDTH,8.2,color=GRAY)
    paragraph(c,title,LEFT,789,WIDTH,23,leading=28,maxh=58)
    c.setStrokeColor(colors.HexColor('#D6E0E5'));c.line(LEFT,39,PAGE_W-LEFT,39)
    paragraph(c,'Alan Alcaraz · Leandro Ferreira · Jorge Rios | 02/11/2026',LEFT,29,WIDTH-55,7.2,color=GRAY)
    paragraph(c,f'{index} / 4',PAGE_W-80,29,40,7.5,color=GRAY)


def picture(c,name,top,height):
    image=ImageReader(str(FIG/name));iw,ih=image.getSize();width=min(WIDTH,height*iw/ih)
    c.drawImage(image,LEFT+(WIDTH-width)/2,top-height,width=width,height=height,mask='auto')


def table(c,headers,rows,top,widths):
    style=ParagraphStyle('cell',fontName='Vera',fontSize=9,leading=12,textColor=colors.HexColor(NAVY))
    white=ParagraphStyle('head',parent=style,fontName='Vera-Bold',textColor=colors.white)
    cells=[[Paragraph(html.escape(x),white) for x in headers]]
    cells += [[Paragraph(x,style) for x in row] for row in rows]
    obj=Table(cells,colWidths=widths,hAlign='LEFT')
    obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('VALIGN',(0,0),(-1,-1),'TOP'),
                            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor(PALE)]),
                            ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
                            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    _,h=obj.wrap(WIDTH,700);obj.drawOn(c,LEFT,top-h)
    return top-h


def main(sin_graficos=False):
    data=json.loads((OUT/'evidencia.json').read_text(encoding='utf8'))
    for name,expected in data['fuentes_actuales'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Fuente actual modificada: '+name
    old_root=Path(data['origen_anterior'])
    if old_root.exists():
        for name,expected in data['fuentes_originales'].items():
            assert hashlib.sha256((old_root/name).read_bytes()).hexdigest()==expected,'Fuente anterior modificada: '+name
    old=data['original']
    final=next(r for r in data['brasil_2026'] if r['modelo']=='Contexto_regularizado_natural')
    ref=next(r for r in data['brasil_2026'] if r['modelo']=='Referencia_24_original')
    assert (final['TP'],final['FP'],final['FN'],final['TN'])==(1953,3277,2657,59704)
    if not sin_graficos:charts(final,ref)
    target=OUT/'Resumen_Fase_3_Continuidad_Paraguay_Brasil.pdf'
    c=canvas.Canvas(str(target),pagesize=A4)
    c.setTitle('Fase 3: mejores datos para continuar el estudio de gravedad')
    c.setAuthor('Alan Alcaraz, Leandro Ferreira y Jorge Rios')

    page(c,1,'Mejores datos para continuar<br/>el estudio de gravedad')
    paragraph(c,'Mantuvimos el tema: accidentes de tránsito y gravedad de las víctimas. Para poder avanzar con la predicción, mejoramos la información y adaptamos el alcance.',LEFT,714,WIDTH,11,maxh=50)
    rect(c,LEFT,655,WIDTH,78)
    paragraph(c,'<b>La tarea que conservamos</b><br/>Distinguir entre víctimas heridas y fallecidas a partir de las características de la persona, el vehículo y el accidente.',LEFT+15,641,WIDTH-30,11,maxh=61)
    gap=15;cw=(WIDTH-gap)/2
    for x,title,big,body in [
        (LEFT,'ANTES | PARAGUAY 2021','5.493 filas; 16 perfiles','Eran frecuencias oficiales expandidas por sexo y grupo de edad. No teníamos identificadores para relacionar correctamente todas las tablas por víctima.'),
        (LEFT+cw+gap,'AHORA | BRASIL - PRF','31 características','754.098 participaciones reales en 2017-2025, más 67.591 para evaluar 2026. Podemos relacionar a las personas con su accidente y vehículo.')]:
        rect(c,x,558,cw,150)
        paragraph(c,title,x+13,545,cw-26,9,color=TEAL)
        paragraph(c,'<b>'+big+'</b>',x+13,519,cw-26,14,maxh=40)
        paragraph(c,body,x+13,476,cw-26,10,maxh=65)
    bottom=table(c,['Qué mantuvimos','Qué tuvimos que adaptar'],[
        ['Gravedad: herido o fallecido.','País, población y años disponibles.'],
        ['Estudiar sexo, edad y vehículo.','Algunas hipótesis y sus grupos de comparación.'],
        ['Preparar datos, contrastar y modelar.','Uniones reales y evaluación por períodos posteriores.'],
    ],385,[WIDTH*.47,WIDTH*.53])
    rect(c,LEFT,bottom-18,WIDTH,85,'#FFF1E4')
    paragraph(c,'<b>Continuidad no significa que sea exactamente el mismo estudio.</b><br/>Brasil no responde por Paraguay 2021 ni confirma automáticamente sus hipótesis. Conservamos el problema central, pero cambiamos el alcance para trabajar con mejores datos.',LEFT+14,bottom-31,WIDTH-28,10.5,maxh=70)
    paragraph(c,'Los conteos anteriores eran reales. La limitación era su nivel de detalle: expandir cantidades no crea nuevas observaciones individuales.',LEFT,132,WIDTH,9,color=GRAY,maxh=45)
    c.showPage()

    page(c,2,'Cómo preparamos y evaluamos')
    paragraph(c,'Unimos las tablas con el identificador real del accidente. Revisamos duplicados, edades imposibles y faltantes. No inventamos personas ni mezclamos víctimas entre períodos.',LEFT,748,WIDTH,10.5,maxh=48)
    cards=[('PERSONA','Edad, sexo y rol: conductor, pasajero o peatón.'),('VEHÍCULO Y ACCIDENTE','Tipo y antigüedad, otros vehículos, choque, clima y vía.'),('TIEMPO Y UBICACIÓN','Horario, día, mes, ruta, municipio y coordenadas.')]
    for i,(title,body) in enumerate(cards):
        x=LEFT+i*(WIDTH+12)/3;w=(WIDTH-24)/3
        rect(c,x,684,w,86)
        paragraph(c,title,x+10,673,w-20,8.3,color=TEAL)
        paragraph(c,body,x+10,649,w-20,9.5,maxh=49)
    paragraph(c,'<b>Cada período tiene una función</b>',LEFT,578,WIDTH,12)
    steps=[('2017-2023','573.747 víctimas','Aprender las relaciones de los datos.'),
           ('2024 | enero-junio','43.522 víctimas','Calibrar: ajustar los porcentajes de riesgo.'),
           ('2024 | julio-diciembre','47.236 víctimas','Elegir desde qué riesgo clasificar como fallecido.'),
           ('2025','89.593 víctimas','Comparación retrospectiva: sus resultados ya eran conocidos.'),
           ('2026 | enero-sept.','67.591 víctimas','Evaluación posterior del modelo que ya habíamos elegido.')]
    for i,(period,n,reason) in enumerate(steps):
        top=549-i*49
        c.setFillColor(colors.HexColor(TEAL));c.circle(LEFT+5,top-10,4,fill=1,stroke=0)
        paragraph(c,'<b>'+period+'</b><br/>'+n,LEFT+18,top,145,9,leading=12,maxh=42)
        paragraph(c,reason,LEFT+174,top,WIDTH-174,10,maxh=41)
    rect(c,LEFT,287,WIDTH,91)
    paragraph(c,'<b>Modelos probados</b>',LEFT+14,274,WIDTH-28,11)
    paragraph(c,'Regresión logística, árbol, Naive Bayes, LightGBM y una referencia que siempre responde herido. Probamos configuraciones con años anteriores y elegimos LightGBM con 31 entradas.',LEFT+14,252,WIDTH-28,10,maxh=50)
    paragraph(c,'<b>El desbalance sigue presente</b>',LEFT,177,WIDTH,11)
    pos=38619/573747
    c.setFillColor(colors.HexColor(TEAL));c.rect(LEFT,137,WIDTH*(1-pos),16,fill=1,stroke=0)
    c.setFillColor(colors.HexColor(ORANGE));c.rect(LEFT+WIDTH*(1-pos),137,WIDTH*pos,16,fill=1,stroke=0)
    paragraph(c,'Desarrollo: 535.128 heridos y 38.619 fallecidos (aproximadamente 93 % / 7 %).',LEFT,126,WIDTH,9,maxh=30)
    paragraph(c,'Consideramos pesos para los fallecidos; el ganador conservó la proporción natural. No elegimos solo por aciertos totales ni usamos muertos/heridos como entradas. La causa del accidente no integra el modelo final.',LEFT,91,WIDTH,9,maxh=45)
    c.showPage()

    page(c,3,'Qué logró el modelo final')
    paragraph(c,'LightGBM de 31 variables | Mismas 67.591 víctimas de enero-septiembre de 2026.',LEFT,748,WIDTH,10.5,maxh=30)
    scores=[('AUC',dec(final['ROC_AUC']),'Ordenar los casos por riesgo'),('F1 MACRO',dec(final['F1_macro']),'Evaluar ambos grupos por igual'),('DETECCIÓN',dec(final['recall']*100,1)+' %','Fallecidos que logra identificar')]
    for i,(label,value,meaning) in enumerate(scores):
        x=LEFT+i*(WIDTH+12)/3;w=(WIDTH-24)/3
        rect(c,x,711,w,87)
        paragraph(c,label,x+11,700,w-22,9,color=TEAL)
        paragraph(c,'<b>'+value+'</b>',x+11,680,w-22,27,leading=30)
        paragraph(c,meaning,x+11,643,w-22,8,maxh=22)
    paragraph(c,'<b>Comparación dentro de Brasil</b>',LEFT,607,WIDTH,11)
    picture(c,'comparacion_brasil.png',584,165)
    paragraph(c,'La referencia de 24 variables y la versión final usan la misma fuente, población y períodos. La versión final mejora variables y configuración: detecta 132 fallecidos más y produce 717 falsas alarmas menos.',LEFT,409,WIDTH,10,maxh=45)
    paragraph(c,'<b>Qué acierta y dónde se equivoca</b>',LEFT,346,WIDTH,11)
    picture(c,'errores_brasil.png',323,143)
    rect(c,LEFT,164,WIDTH,64,'#FFF1E4')
    paragraph(c,'<b>1.953 fallecidos identificados; 2.657 no detectados.</b><br/>Además, marca erróneamente como fallecidos a 3.277 heridos. Todavía hay errores importantes.',LEFT+13,151,WIDTH-26,10.5,maxh=49)
    paragraph(c,'AUC 0,845 no significa 84,5 % de aciertos. Las métricas del proyecto anterior (AUC 0,581 y F1 macro 0,530) proceden de otra población y otra prueba: no son una comparación controlada entre países.',LEFT,85,WIDTH,9,maxh=41)
    c.showPage()

    page(c,4,'Qué aprendimos y qué cambió')
    paragraph(c,'<b>Qué información ayudó más al modelo</b>',LEFT,747,WIDTH,11)
    picture(c,'importancia_brasil.png',724,143)
    paragraph(c,'Medimos cuánto empeora el modelo al mezclar cada variable en 10.000 casos de validación. Una caída mayor indica más utilidad predictiva; no demuestra una causa.',LEFT,571,WIDTH,9.5,maxh=40)
    paragraph(c,'<b>Continuidad de las hipótesis originales</b>',LEFT,518,WIDTH,11)
    bottom=table(c,['Proyecto original','Adaptación en Brasil'],[
        ['H1: Interior / Asunción-Central','Ese contraste no se repitió. Se usa ubicación, pero no son las mismas zonas.'],
        ['H2: sexo','Nueva H1: asociación entre sexo y gravedad.'],
        ['H3: mayor gravedad en motos','Nueva H3: cambiaron grupos y contraste; no confirma la dirección original.'],
        ['H4: edad y adultos mayores','Nueva H2: distribución de edad. No se repitió la prueba específica de 60 años o más.'],
        ['Horario como contexto','Nueva H4: noche considerando otras variables. Es una incorporación.'],
    ],496,[WIDTH*.39,WIDTH*.61])
    assert bottom>255,bottom
    top=bottom-18
    rect(c,LEFT,top,WIDTH,87)
    paragraph(c,'<b>Conclusión y límites</b><br/>Continuamos el estudio de gravedad con mejores registros y una evaluación temporal. El rendimiento es útil para el trabajo académico, pero todavía omite muchos fallecidos. Faltan velocidad de impacto, casco/cinturón y seguimiento clínico; no está validado para atención médica ni para Paraguay.',LEFT+13,top-12,WIDTH-26,10,maxh=73)
    paragraph(c,'Fuentes: notebook Fase3_Accidentes_AUDITADA y resultados históricos de Paraguay; particiones.csv, metricas_evaluacion.csv, contrastes_fase2.csv e importancia_modelo_final.csv de Brasil. Los gráficos reproducen esas cifras, sin entrenar otro modelo.',LEFT,152,WIDTH,8.2,color=GRAY,maxh=48)
    paragraph(c,'La comparación completa de las tres fases y la precisión de grupos/versiones están en COMPARACION_PROYECTOS.md, junto a este PDF. Se declara apoyo de IA en análisis, redacción y diseño; el grupo debe revisar y comprender el material.',LEFT,94,WIDTH,8.2,color=GRAY,maxh=39)
    c.save()
    print(target)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-graficos',action='store_true',help='Reutiliza los graficos ya generados')
    main(parser.parse_args().sin_graficos)
