"""Presentacion breve de resultados guardados, sin reentrenar ni elegir modelos."""
from pathlib import Path
import json
import csv
import sys

HERE=Path(__file__).resolve().parent;OUT=HERE/'output';BASE=HERE.parent


def data():
    r=json.loads((OUT/'resultados.json').read_text(encoding='utf8'))
    f=json.loads((OUT/'congelamiento.json').read_text(encoding='utf8'))
    return r,f


def graphs():
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import roc_curve,precision_recall_curve,confusion_matrix
    r,f=data();sel=r['seleccionado'];ref=r['referencia']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':170})
    colors=['#7796a8','#176c84']
    def save(name):
        plt.tight_layout();plt.savefig(OUT/'figures'/name,bbox_inches='tight');plt.close()
    cv=pd.read_csv(OUT/'ranking_CV.csv').sort_values('AP_media')
    fig,ax=plt.subplots(figsize=(8.4,4));ax.barh(cv.modelo,cv.AP_media,color=[colors[0] if n==ref else colors[1] for n in cv.modelo])
    ax.set(xlabel='Average precision media de fallecidos',title='Selección en tres cortes temporales anteriores a prueba')
    save('01_busqueda_CV.png')
    m=pd.read_csv(OUT/'metricas_evaluacion.csv');new=m[m.particion.eq('2026_prueba_nueva')&m.regla.eq('F1_validacion')].set_index('modelo')
    fig,ax=plt.subplots(figsize=(8.2,3.8));cols=['ROC_AUC','AP','F1_macro','precision','recall'];x=np.arange(len(cols))
    for i,n in enumerate([ref,sel]):ax.bar(x+(i-.5)*.34,new.loc[n,cols].to_numpy(float),width=.34,label=['Referencia 24 variables','Candidato seleccionado'][i],color=colors[i])
    ax.set(xticks=x,xticklabels=['AUC ROC','AP','F1 macro','Precisión','Recall'],ylim=(0,1),ylabel='Puntuación',title='Mismas víctimas de 2026: referencia y candidato congelados');ax.legend(fontsize=8)
    save('02_comparacion_2026.png')
    p=pd.read_csv(OUT/'predicciones_2026.csv.gz',float_precision='round_trip');y=p.fallecido.to_numpy()
    fig,axes=plt.subplots(1,2,figsize=(9,3.6))
    for i,n in enumerate([ref,sel]):
        fpr,tpr,_=roc_curve(y,p[n]);prec,rec,_=precision_recall_curve(y,p[n])
        axes[0].plot(fpr,tpr,color=colors[i],label=['Referencia','Candidato'][i]);axes[1].plot(rec,prec,color=colors[i],label=['Referencia','Candidato'][i])
    axes[0].plot([0,1],[0,1],color='#999',linestyle='--');axes[1].axhline(y.mean(),color='#999',linestyle='--')
    axes[0].set(xlabel='Falsos positivos / heridos',ylabel='Recall fallecidos',title='Discriminación ROC');axes[1].set(xlabel='Recall fallecidos',ylabel='Precisión fallecidos',title='Precisión-recall en prueba nueva')
    for ax in axes:ax.legend(fontsize=8)
    save('03_curvas_2026.png')
    fig,axes=plt.subplots(1,2,figsize=(9,3.6))
    for i,n in enumerate([ref,sel]):
        t=next(s['umbral'] for s in f['modelos'] if s['nombre']==n)
        cm=confusion_matrix(y,p[n].to_numpy()>=t,labels=[0,1])
        sns.heatmap(cm,annot=True,fmt='d',cmap='Blues',cbar=False,ax=axes[i],xticklabels=['Herida','Fallecida'],yticklabels=['Herida','Fallecida'])
        axes[i].set(xlabel='Predicción',ylabel='Registro real',title=['Referencia','Candidato seleccionado'][i])
    save('04_confusion_2026.png')
    print('Cuatro figuras guardadas')


def documents():
    import pandas as pd
    r,f=data();m=pd.DataFrame(r['metricas']);main=m[m.regla.eq('F1_validacion')]
    a=r['auditoria_prueba'];sel=r['seleccionado'];ref=r['referencia']
    test=main[main.particion.eq('2026_prueba_nueva')].set_index('modelo')
    def count(v):return f'{int(v):,}'.replace(',','.')
    rows=''.join(f'<tr><td>{"Referencia" if x.modelo==ref else "Candidato"}</td><td>{"2025 retrospectivo" if x.particion.startswith("2025") else "2026 prueba nueva"}</td><td>{x.ROC_AUC:.3f}</td><td>{x.AP:.3f}</td><td>{x.F1_macro:.3f}</td><td>{x.precision:.1%}</td><td>{x.recall:.1%}</td></tr>' for x in main.itertuples())
    html=f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mejora acotada de fase 3 — Brasil</title><style>body{{background:#eef3f5;color:#20323f;font:17px/1.6 system-ui;margin:0}}main{{max-width:1050px;margin:30px auto;background:white;padding:30px}}h1,h2{{color:#21496d;line-height:1.2}}table{{border-collapse:collapse;width:100%;font-size:15px}}th,td{{padding:9px;border-bottom:1px solid #ccd7dd;text-align:left}}th{{background:#21496d;color:white}}img{{max-width:100%;height:auto}}a{{color:#176c84}}.note{{padding:16px;background:#fff6e9;border-left:4px solid #b57c30}}</style><main><p>Proyecto Integrador · Alan Alcaraz, Leandro Ferreira y Jorge Rios · 31/10/2026</p><h1>Segunda versión: más contexto del accidente</h1><p>Ronda limitada a ocho configuraciones y tres cortes temporales. Se conservó el experimento anterior y se seleccionó <strong>{sel}</strong> antes de abrir la nueva prueba de 2026.</p><div class="note">La nueva prueba contiene <strong>{count(a['victimas'])} víctimas</strong>, entre {a['fecha_min_victimas']} y {a['fecha_max_victimas']}. Es el período publicado, no todo 2026. Ambos modelos utilizan idénticas víctimas y los mismos años de entrenamiento/calibración.</div><h2>Comparación de resultados</h2><table><tr><th>Modelo</th><th>Evaluación</th><th>AUC</th><th>AP</th><th>F1 macro</th><th>Precisión</th><th>Recall</th></tr>{rows}</table><p>AUC y AP resumen ordenamiento; precisión y recall dependen del umbral elegido con 2024. La comparación de 2025 es retrospectiva porque sus resultados anteriores ya se conocían.</p><img src="output/figures/02_comparacion_2026.png" alt="Comparación en prueba nueva"><h2>Qué se agregó</h2><p>Cantidad de vehículos, composición de otros vehículos identificados, marca aproximada e indicadores de trazado; se compararon ajustes de complejidad y regularización. El contexto usa la exportación completa, incluidos ilesos y vehículos sin persona, deduplicada por claves reales. No incorpora conteos de heridos o muertos.</p><img src="output/figures/04_confusion_2026.png" alt="Matrices de confusión"><h2>Archivos para revisar</h2><ul><li><a href="output/INFORME_MEJORA_FASE_3.pdf">Informe breve de la mejora</a></li><li><a href="output/Mejora_Fase_3.html">Notebook ejecutado en HTML</a></li><li><a href="output/metricas_evaluacion.csv">Métricas de los tres umbrales</a></li><li><a href="output/intervalos_mejora_2026.csv">Intervalos de las diferencias por accidente</a></li><li><a href="output/auditoria_2026.json">Cobertura y auditoría de la prueba nueva</a></li><li><a href="README.md">Reproducción y alcance</a></li><li><a href="../ABRIR_RESULTADOS.html">Proyecto original conservado</a></li></ul><p class="note">Material de apoyo con asistencia de IA. El grupo debe comprender y adoptar las decisiones y conclusiones. La predicción caracteriza siniestros observados con lesionados; no es riesgo previo de accidentarse ni un modelo clínico validado.</p></main></html>'''
    html=html.replace('Cantidad de vehículos, composición de otros vehículos identificados, marca aproximada e indicadores de trazado; se compararon ajustes de complejidad y regularización.', 'El ganador utiliza 31 características: las 24 previas más seis cantidades de contexto vehicular y la familia del otro vehículo. Marca aproximada y trazado descompuesto se probaron en otras variantes; no quedaron en el ganador. También se compararon ajustes de complejidad y regularización.')
    (HERE/'ABRIR_MEJORA.html').write_text(html,encoding='utf8')
    readme=f'''# Mejora acotada de la fase 3 — PRF Brasil

Abrir `ABRIR_MEJORA.html`. Este complemento conserva el proyecto original y documenta una segunda versión, seleccionada antes de leer la nueva prueba de 2026. No se amplió la búsqueda después de ver los resultados.

## Experimento

- Ocho configuraciones LightGBM, 24 ajustes CV (2021, 2022, 2023).
- Base de 24 predictores; contexto vehicular; enriquecimiento con trazado y marca aproximada. Cantidades exactas de campos en `output/diccionario_bloques.json`.
- El contexto se forma con TODOS los vehículos identificados del archivo de personas, incluidos ilesos y registros sin persona. Se deduplica `(id,id_veiculo>0)` y se resta el propio al contar otros vehículos. No identifica necesariamente parejas de colisión en accidentes múltiples.
- Ambos modelos se entrenan en 2017–2023; calibración 2024 H1; umbral 2024 H2. Misma población para comparar; las mejoras no se deben a entrenar uno con más años.
- Candidato elegido: `{sel}`. Criterio: AP media superior a referencia y mejora en al menos dos cortes, sin seleccionar con 2025/2026.
- 2025 es comparación retrospectiva; 2026 es nueva prueba cronológica, leída después del congelamiento. Período real: {a['fecha_min_victimas']} a {a['fecha_max_victimas']}; {count(a['victimas'])} víctimas, {count(a['fallecidos'])} fallecidas. No es un año completo ni un seguimiento de mortalidad a 30 días.
- 300 bootstrap pareados por accidentes completos, respetando víctimas del mismo evento. La incertidumbre no incluye todos los sesgos de cobertura o cambios temporales.

Los originales de 2026 proceden de los enlaces del portal oficial PRF y se guardan con URL y SHA-256 en `manifiesto_2026.json`. Fueron descargados como ZIP opacos antes de la selección y abiertos después del congelamiento. No se presentó ningún pedido institucional ni se enviaron datos a terceros.

## Reproducir

Este directorio se ubica dentro de `PROYECTO_GRAVEDAD_BRASIL` y utiliza sus dependencias y módulos de `src`. No instalar herramientas nuevas para esta ronda. Desde ese proyecto:

```powershell
python MEJORA_FASE_3/descargar_2026.py
python MEJORA_FASE_3/mejorar.py
python MEJORA_FASE_3/presentar.py
python MEJORA_FASE_3/notebook.py
python MEJORA_FASE_3/inferencia.py --entrada MEJORA_FASE_3/data/ejemplo_inferencia.csv --salida MEJORA_FASE_3/output/ejemplo_predicciones.csv
```

`mejorar.py` reutiliza resultados existentes y verifica hashes; no vuelve a seleccionar con la prueba. El notebook está ejecutado y muestra la auditoría, la búsqueda y las métricas calculadas. Una ejecución desde cero requiere los originales 2017–2025 y 2026, o descargar sus cortes verificables. Repetir retrospectivamente un experimento no convierte un período ya visto en una prueba ciega nueva.

La entrada de inferencia usa características YA preparadas y códigos compatibles. `familia_otro_vehiculo` y conteos requieren el conjunto completo de vehículos del siniestro; no pueden rellenarse desde una sola víctima aislada ni usarse antes de que se conozca el evento.

## Relación con las tres fases

Fase 1: el complemento añade auditoría y documentación del contexto vehicular sin fabricar participantes ni modificar el objetivo. Fase 2: se mantienen las hipótesis y límites originales; la ganancia predictiva no demuestra un efecto causal de estas características. Fase 3: se añade esta comparación y el nuevo modelo serializado como segunda versión. El informe original y su ZIP quedan intactos. Para una entrega consolidada deben incorporarse estas decisiones a la narración, sin confundir 2025 retrospectivo con la prueba nueva.

Las decisiones están en `protocolo.json`, la grilla en `output/grilla_fijada.json`, y el congelamiento con hashes de modelos y fecha UTC en `output/congelamiento.json`. Los resultados y predicciones están en `output/`. Los scripts no inventan integrantes, legajos o aprobaciones docentes. Material de apoyo con IA que el grupo debe revisar y comprender.
'''
    (HERE/'README.md').write_text(readme,encoding='utf8')


def pdf():
    sys.path.insert(0,str(BASE/'src'))
    import pdf_layout as L
    from reportlab.platypus import SimpleDocTemplate,PageBreak,Paragraph,Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    L.OUT=OUT;W=L.WIDTH
    r,f=data();sel=r['seleccionado'];ref=r['referencia'];a=r['auditoria_prueba']
    def p(t,small=False):return L.p(str(t).replace('–','-').replace('—','-'),small)
    def read(name):
        with (OUT/name).open(encoding='utf-8-sig',newline='') as file:return list(csv.DictReader(file))
    def val(x,n=3):return L.fmt(x,n)
    def pct(x):return val(float(x)*100,2)+' %'
    def img(name,scale=.9):return L.image(name,width=W*scale)
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Vera',7);canvas.drawString(1.6*cm,.8*cm,'PRF Brasil | Mejora acotada de fase 3 | 31/10/2026');canvas.drawRightString(A4[0]-1.6*cm,.8*cm,f'Página {doc.page}');canvas.restoreState()
    main=[x for x in r['metricas'] if x['regla']=='F1_validacion']
    current=next(x for x in main if x['particion']=='2026_prueba_nueva' and x['modelo']==sel)
    old=next(x for x in main if x['particion']=='2026_prueba_nueva' and x['modelo']==ref)
    ci=r['intervalos_delta']
    story=[p('PROYECTO INTEGRADOR - COMPLEMENTO DE LA FASE 3',True),L.heading('¿Mejoró el modelo al incorporar contexto del accidente?'),p('Alan Alcaraz · Leandro Ferreira · Jorge Rios | Legajos pendientes | 31/10/2026',True),
        p(f"Se ejecutó una ronda limitada a ocho configuraciones y tres cortes temporales. El candidato seleccionado fue {sel}. La selección se hizo con AP de validación antes de leer la nueva prueba de 2026; el proyecto original se conserva."),
        L.sub('Comparación con las mismas víctimas'),
        L.table(['Evaluación / modelo','AUC','AP','F1 macro','Precisión','Recall'],[[('2025 retrospectivo' if x['particion'].startswith('2025') else '2026 nuevo')+' / '+('Referencia' if x['modelo']==ref else 'Candidato'),val(x['ROC_AUC']),val(x['AP']),val(x['F1_macro']),pct(x['precision']),pct(x['recall'])] for x in main],[W*.35,W*.12,W*.12,W*.13,W*.14,W*.14]),
        p(f"La nueva prueba cubre {a['fecha_min_victimas']} a {a['fecha_max_victimas']}: {a['victimas']:,} víctimas, {a['fallecidos']:,} fallecidas y {a['accidentes']:,} accidentes con víctimas elegibles. Es el corte publicado, no todo 2026."),
        img('02_comparacion_2026.png'),
        p('AP no es porcentaje de aciertos. AUC y AP evalúan ordenamiento; precisión y recall corresponden al umbral elegido previamente. La comparación de 2025 es retrospectiva porque sus resultados ya se conocían.',True),
        PageBreak(),L.heading('Cambios y selección sin usar la prueba'),
        p('El ganador usa 31 características: las 24 previas más siete de contexto vehicular. Todos los vehículos identificados, incluidos ilesos y filas sin persona, se deduplican por (id,id_veiculo positivo). Se descuenta el propio para contar otros. La familia de un único otro vehículo es un contexto, no prueba de contacto directo. Marca aproximada y trazado descompuesto se probaron en otras variantes; no quedaron en el ganador. No se usan gravedad ni conteos de muertos/heridos.'),
        L.table(['Configuración','AP CV','AUC CV','Cortes mejores'],[[x['modelo'],val(x['AP_media']),val(x['AUC_media']),x['cortes_supera_referencia']+' / 3'] for x in read('ranking_CV.csv')],[W*.52,W*.16,W*.16,W*.16]),
        p('Referencia y candidato se entrenaron con 2017-2023, se calibraron con enero-junio 2024 y fijaron umbral con julio-diciembre 2024. No se dio más historia a uno que al otro. Cada codificador se aprendió dentro de su entrenamiento. La grilla y los hashes se guardaron antes de abrir los datos de 2026.'),
        img('03_curvas_2026.png'),
        PageBreak(),L.heading('Errores y desbalance: qué cambia realmente'),img('04_confusion_2026.png'),
        p(f"Al umbral principal el candidato detecta {current['TP']:,} de {current['fallecidos']:,} fallecidos; omite {current['FN']:,} y genera {current['FP']:,} falsas alarmas. La referencia detecta {old['TP']:,}, omite {old['FN']:,} y genera {old['FP']:,} falsas alarmas."),
        L.table(['Regla del candidato','Umbral','Precisión','Recall','F1 fallecido'],[[{'F1_validacion':'Equilibrio F1 elegido','umbral_05':'Umbral 0,50','recall80_validacion':'Recall 80% en validación'}[x['regla']],val(x['umbral'],4),pct(x['precision']),pct(x['recall']),val(x['F1_fallecido'])] for x in r['metricas'] if x['modelo']==sel and x['particion']=='2026_prueba_nueva'],[W*.38,W*.15,W*.16,W*.16,W*.15]),
        p('Las tres reglas se fijaron con 2024. El punto de recall 80% puede lograr otra detección en 2026. Bajar el umbral intercambia omisiones y falsas alarmas; no representa por sí solo mayor aprendizaje. La prevalencia de prueba se conserva, sin fabricar fallecidos ni balancear el examen.'),
        PageBreak(),L.heading('Incertidumbre, alcance y uso en el proyecto'),
        L.table(['Diferencia candidato - referencia','IC 95% inferior','IC 95% superior'],[[x['metrica'],val(x['IC95_bajo'],4),val(x['IC95_alto'],4)] for x in ci],[W*.5,W*.25,W*.25]),
        p('Se hicieron 300 remuestras pareadas de accidentes completos de 2026. Los intervalos reflejan variación bajo ese remuestreo, no todos los sesgos de cobertura o dependencia geográfica/temporal. La interpretación del cambio debe considerar magnitud, intervalos y errores, además de una métrica aislada.'),
        p('Fase 1: se añade auditoría del contexto y se conserva la unidad de víctima. Fase 2: se mantienen las hipótesis originales, sin convertir utilidad predictiva en causalidad. Fase 3: se incorpora esta segunda versión, el modelo serializado, el notebook ejecutado y la comparación con prueba posterior. Las versiones anteriores no se sobrescriben.'),
        p('El modelo usa características de un siniestro observado, no información disponible antes de accidentarse. No incluye velocidad de impacto, casco/cinturón ni seguimiento clínico completo. No está validado para uso médico ni extrapolación a Paraguay. El corte de 2026 puede tener subregistro y revisiones posteriores.'),
        L.sub('Trazabilidad y reproducción'),p('Los CSV con métricas, auditorías, grilla, congelamiento, intervalos, fuentes y SHA-256 acompañan el informe en MEJORA_FASE_3. README explica la reproducción y la inferencia. No se enviaron solicitudes institucionales ni se publicaron datos. Uso académico con asistencia de IA: el equipo debe verificar y comprender código y conclusiones antes de presentar.'),
        p('Fuente oficial: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf',True)]
    path=OUT/'INFORME_MEJORA_FASE_3.pdf'
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=1.5*cm,bottomMargin=1.6*cm,title='Mejora acotada de fase 3 - PRF Brasil',author='Material de apoyo con asistencia de IA').build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)


if __name__=='__main__':
    if '--pdf' in sys.argv:pdf()
    else:graphs();documents()
