"""Tres notebooks explicados y ejecutados; una unica opcion final."""
from pathlib import Path
import os,json
import argparse
import nbformat as nb
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from common import ROOT,OUT
from textos import F1_TEXTOS,F3_TEXTOS

SETUP='''from pathlib import Path
import sys,json
import pandas as pd
from IPython.display import display,Image
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'protocolo.json').exists())
sys.path.insert(0,str(ROOT/'src'))
from common import OUT,RAW,load_data
if not (RAW/'pessoas_2017.zip').exists() or not (RAW/'pessoas_2026.zip').exists():
    from descargar_fuentes import main as descargar
    descargar()
pd.set_option('display.max_columns',16)
pd.set_option('display.max_colwidth',90)
def tabla(name):return pd.read_csv(OUT/'tables'/name)
'''


def main(actualizar_textos=False):
    for d in [ROOT/'tmp/ipython',ROOT/'tmp/jupyter',ROOT/'notebooks',OUT/'html']:d.mkdir(parents=True,exist_ok=True)
    os.environ['IPYTHONDIR']=str(ROOT/'tmp/ipython');os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'tmp/jupyter')
    md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
    intro='Usamos herramientas de IA como apoyo. El grupo debe revisar y comprender los resultados. Cada fila representa a una persona en un accidente registrado; no representa todos sus viajes ni permite seguir su identidad a lo largo de los años.'
    c=[md('# Fase 1 — Preparación y exploración\n\n'+intro),code(SETUP),
       md('## Problema, alcance y objetivos\n\nQueremos estudiar qué características se relacionan con la gravedad de las víctimas de PRF Brasil en 2017-2025 y qué tan bien permiten distinguir heridos y fallecidos en un período posterior. Para eso unimos y limpiamos los datos, hacemos gráficos, contrastamos cuatro hipótesis y comparamos modelos. La evaluación posterior corresponde a enero-septiembre de 2026.'),
       md('## Preparación desde los archivos originales\n\nComprobamos las huellas SHA-256 para usar los mismos archivos. Unimos cada víctima con su accidente mediante identificadores reales. Para contar los otros vehículos usamos todos los vehículos identificados del accidente, incluidos los de personas ilesas. Un vehículo con varios ocupantes se cuenta una sola vez.'),
       code("from preparar import prepare,original_dictionary\nd=prepare(force=True)\n_ = original_dictionary()\nassert len(d)==821689 and d.pesid.is_unique\ndisplay(d.head())\ndisplay(tabla('auditoria_preparacion_por_anio.csv'))\ndisplay(tabla('particiones.csv'))"),
       md('El período principal 2017-2025 tiene 754.098 víctimas y el corte 2026 agrega 67.591. El archivo limpio reúne 821.689 participaciones. Los gráficos y las pruebas estadísticas usan solamente 2017-2023. Los resultados posteriores ya son conocidos: ejecutar de nuevo no crea otra prueba independiente.'),
       code("display(tabla('bitacora_limpieza.csv'))\ndisplay(tabla('diccionario_original.csv'))\ndisplay(tabla('diccionario_final.csv'))"),
       md('Conservamos las víctimas aunque falte algún dato. Una edad cero o imposible pasa a faltante, sin inventar una edad. Las categorías desconocidas se mantienen. Los algoritmos que requieren completar números aprenden ese reemplazo solo con entrenamiento; LightGBM admite números faltantes.'),
       code("from fase1 import main as explorar\ninterpretaciones=explorar()\ndisplay(tabla('descriptivos_desarrollo.csv'))\ndisplay(tabla('concentracion_categorias.csv'))\ndisplay(tabla('correlacion_spearman.csv'))\ndisplay(tabla('contingencia_sexo_fila.csv'))")]
    f1={'interpretaciones':F1_TEXTOS}
    for name,text in f1['interpretaciones'].items():c += [code(f"display(Image(filename=str(OUT/'figures/{name}')))"),md(text)]
    c += [md('## Conclusión de la fase 1\n\nHay muchos más heridos que fallecidos y diferencias por edad, vehículo, lugar y horario. Esas observaciones llevan a las cuatro hipótesis de la fase 2. La unión permite estudiar varias características reales de una misma víctima, pero una asociación no demuestra una causa ni garantiza que ayude a predecir.')]
    books=[('Fase_1_Preparacion_EDA',c)]
    c=[md('# Fase 2 — Inferencia estadística\n\n'+intro),code(SETUP),
       md('## Continuidad y decisiones\n\nUsamos cuatro pruebas y fijamos significancia de 0,05. Aplicamos Holm para reducir diferencias encontradas solo por repetir pruebas. Para H1-H3 elegimos una víctima al azar de cada accidente; así no tratamos a varios pasajeros como casos completamente independientes. H4 usa todas las víctimas con las variables necesarias y ajusta la incertidumbre por accidente.'),
       code("display(json.loads((ROOT/'protocolo.json').read_text(encoding='utf8'))['inferencia'])\nfrom fase2 import main as inferir\nf2=inferir()\ndisplay(tabla('supuestos_fase2.csv'))\ndisplay(tabla('contrastes_fase2.csv'))"),
       md('H1 usa chi cuadrado para estudiar sexo y gravedad. H2 usa Mann-Whitney para comparar las distribuciones de edad. H3 compara proporciones entre motos y otros vehículos. H4 usa regresión logística para estudiar la noche considerando otras características. Las tablas muestran H0, H1, cantidades de casos, efectos, intervalos y valores p. Un p guardado como cero significa que es demasiado pequeño para representarse, no exactamente cero.'),
       code("display(Image(filename=str(OUT/'figures/f2_01_normalidad.png')))\ndisplay(f2['bootstrap'])\ndisplay(Image(filename=str(OUT/'figures/f2_02_bootstrap.png')))\ndisplay(tabla('regresion_logistica_inferencial.csv'))"),
       md('Las cuatro pruebas rechazan H0 después de la corrección, pero no todas las diferencias son grandes. La proporción de fallecidos entre las víctimas de moto es algo menor que en otros vehículos; eso no demuestra que la moto sea más segura por viaje. La noche mantiene una asociación al considerar las variables disponibles. OR 1,85 no es un multiplicador directo de la probabilidad. Pueden faltar variables importantes.')]
    books += [('Fase_2_Inferencia',c)]
    c=[md('# Fase 3 — Modelo final y evaluación\n\n'+intro),code(SETUP),
       md('## Comparación de modelos\n\nPrimero comparamos regresión logística, árbol, Naive Bayes, LightGBM y una referencia que siempre responde herido, usando 24 características. Después añadimos contexto de los vehículos y probamos ocho configuraciones de LightGBM. El ganador final tiene 31 características. Las tablas iniciales muestran cómo llegamos a esa elección; no son otros proyectos para entregar.'),
       code("display(json.loads((ROOT/'protocolo.json').read_text(encoding='utf8')))\nfrom modelado import main as modelar\nresultado=modelar()\ndisplay(pd.read_csv(OUT/'modelado/inicial/ranking_CV.csv'))\ninicial=pd.read_csv(OUT/'modelado/inicial/metricas_prueba_2025.csv')\ndisplay(inicial[inicial.regla.eq('F1_validacion')])\ndisplay(pd.read_csv(OUT/'modelado/final/ranking_CV.csv'))"),
       md('Esta ejecución muestra los resultados de entrenamiento guardados; no vuelve a elegir con 2026. Para recalcular los ajustes se usa `src/reproducir.py --reentrenar`. Entrenamos con 2017-2023, ajustamos los porcentajes de riesgo con 2024 H1 y elegimos el punto de decisión con 2024 H2. La selección del modelo usa AP de validación temporal, no la prueba final.'),
       code("display(json.loads((ROOT/'data/metodologia/congelamiento_final_original.json').read_text(encoding='utf8')))\ndisplay(pd.read_csv(OUT/'modelado/final/comparacion_completa.csv'))\ndisplay(pd.read_csv(OUT/'modelado/final/metricas_evaluacion.csv'))"),
       md('Los resultados de 2025 ya se conocían cuando mejoramos el modelo, por eso su comparación final es retrospectiva. El corte original de enero-septiembre de 2026 se abrió después de fijar el modelo final y sus decisiones. Ambos modelos se comparan sobre las mismas víctimas. No usamos como entradas identificadores, gravedad ni cantidades de muertos o heridos.'),
       code("from graficos import main as analizar\ninterpretaciones=analizar()\ndisplay(tabla('importancia_modelo_final.csv'))")]
    g=F3_TEXTOS
    for name,text in g.items():c += [code(f"display(Image(filename=str(OUT/'figures/{name}')))"),md(text)]
    c += [code("display(tabla('errores_por_grupo_modelo_final.csv'))\ndisplay(tabla('errores_mayor_confianza_modelo_final.csv').drop(columns=['id','pesid']))\ndisplay(pd.read_csv(OUT/'modelado/final/intervalos_mejora_2026.csv'))"),
       md('## Conclusión de la fase 3\n\nEl modelo final obtiene AUC 0,845 y F1 macro 0,675 en 2026, frente a 0,799 y 0,647 de la referencia. Encuentra 132 fallecidos más y genera 717 falsas alarmas menos. Todavía clasifica como heridos a 2.657 fallecidos. Bajar el punto de decisión encuentra más fallecidos, pero aumenta las falsas alarmas. Este es un ejercicio académico con accidentes ya registrados, no una herramienta médica ni una predicción de quién tendrá un accidente.')]
    books += [('Fase_3_Modelado',c)]
    for name,cells in books:
        book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}})
        path=ROOT/'notebooks'/f'{name}.ipynb'
        if actualizar_textos:
            previous=nb.read(path,as_version=4)
            old_code=[c for c in previous.cells if c.cell_type=='code']
            new_code=[c for c in book.cells if c.cell_type=='code']
            if [c.source for c in old_code]!=[c.source for c in new_code]:
                raise ValueError('Cambio de codigo: ejecutar normalmente para recalcular '+name)
            for new,old in zip(new_code,old_code):
                new.outputs=old.outputs
                new.execution_count=old.execution_count
                new.metadata=old.metadata
            nb.write(book,path)
            html,_=HTMLExporter().from_notebook_node(book)
            (OUT/'html'/f'{name}.html').write_text(html,encoding='utf8')
            print('Textos actualizados; codigo y resultados conservados:',name,flush=True)
            continue
        nb.write(book,path)
        print('Ejecutando',name,flush=True)
        NotebookClient(book,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}},allow_errors=False).execute()
        nb.write(book,path);html,_=HTMLExporter().from_notebook_node(book);(OUT/'html'/f'{name}.html').write_text(html,encoding='utf8')
        print('Notebook y HTML verificados',name,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actualizar-textos',action='store_true',help='Conserva resultados solo si no cambio ninguna celda de codigo')
    main(parser.parse_args().actualizar_textos)
