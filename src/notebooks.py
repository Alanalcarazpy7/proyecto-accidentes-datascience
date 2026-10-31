"""Tres notebooks explicados y ejecutados; una unica opcion final."""
from pathlib import Path
import os,json
import nbformat as nb
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from common import ROOT,OUT

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


def main():
    for d in [ROOT/'tmp/ipython',ROOT/'tmp/jupyter',ROOT/'notebooks',OUT/'html']:d.mkdir(parents=True,exist_ok=True)
    os.environ['IPYTHONDIR']=str(ROOT/'tmp/ipython');os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'tmp/jupyter')
    md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
    intro='Material de apoyo con IA que el grupo debe verificar y comprender. Una fila es una participación real en un accidente; no identidad civil longitudinal ni riesgo por viaje. No se fabrican personas o causalidad.'
    c=[md('# Fase 1 — Preparación y exploración\n\n'+intro),code(SETUP),
       md('## Problema, alcance y objetivos\n\nSe estudian características asociadas con fallecimiento frente a lesión no fatal en siniestros registrados por PRF Brasil, 2017–2025, con validación posterior enero–septiembre 2026. El objetivo general es analizar asociaciones y medir clasificación fuera del entrenamiento. Los objetivos específicos son auditar fuentes/uniones, preparar registros, explorar patrones, contrastar cuatro hipótesis y evaluar modelos con desbalance.'),
       md('## Reconstrucción desde originales\n\nSe verifican SHA-256, claves y cardinalidades. El contexto se forma con todos los vehículos identificados antes de seleccionar víctimas; se incluyen ilesos y filas sin persona. Se deduplica por (id,id_veiculo positivo), sin sumar conteos de muertos/heridos como entradas.'),
       code("from preparar import prepare,original_dictionary\nd=prepare(force=True)\n_ = original_dictionary()\nassert len(d)==821689 and d.pesid.is_unique\ndisplay(d.head())\ndisplay(tabla('auditoria_preparacion_por_anio.csv'))\ndisplay(tabla('particiones.csv'))"),
       md('El dataset principal 2017–2025 tiene 754.098 víctimas; la validación 2026 incorpora 67.591. El archivo consolidado contiene 821.689 participaciones. La exploración e inferencia usan exclusivamente 2017–2023. El corte posterior ya fue evaluado en el experimento registrado: reconstruirlo ahora no crea otra prueba ciega.'),
       code("display(tabla('bitacora_limpieza.csv'))\ndisplay(tabla('diccionario_original.csv'))\ndisplay(tabla('diccionario_final.csv'))"),
       md('Edad cero ambigua y valores imposibles se convierten a ausencia conservando la víctima. Las categorías desconocidas permanecen; imputación y codificación se aprenden dentro de cada entrenamiento. El mecanismo de ausencia no se supone completamente aleatorio.'),
       code("from fase1 import main as explorar\ninterpretaciones=explorar()\ndisplay(tabla('descriptivos_desarrollo.csv'))\ndisplay(tabla('concentracion_categorias.csv'))\ndisplay(tabla('correlacion_spearman.csv'))\ndisplay(tabla('contingencia_sexo_fila.csv'))")]
    f1=json.loads((OUT/'fase1_resultados.json').read_text(encoding='utf8'))
    for name,text in f1['interpretaciones'].items():c += [code(f"display(Image(filename=str(OUT/'figures/{name}')))"),md(text)]
    c += [md('## Conclusión y puente\n\nDesbalance marcado, superposición de edades, diferencias por tipo/entorno y cambios temporales orientan H1 sexo, H2 edad, H3 usuario de moto y H4 nocturnidad ajustada. Se dispone de más información real por víctima y accidente. El contexto vehicular es una revisión iterativa de preparación para la fase predictiva; su utilidad no implica un efecto causal.')]
    books=[('Fase_1_Preparacion_EDA',c)]
    c=[md('# Fase 2 — Inferencia estadística\n\n'+intro),code(SETUP),
       md('## Continuidad y supuestos\n\nSe declaran cuatro contrastes bilaterales, alfa 0,05 y corrección Holm. Las pruebas clásicas seleccionan una víctima aleatoria por accidente sin usar desenlace para elegirla; representan accidentes ponderados por igual. H4 usa todas las víctimas con covariables completas y SE agrupados por accidente. Las ausencias pueden seleccionar casos.'),
       code("display(json.loads((ROOT/'protocolo.json').read_text(encoding='utf8'))['inferencia'])\nfrom fase2 import main as inferir\nf2=inferir()\ndisplay(tabla('supuestos_fase2.csv'))\ndisplay(tabla('contrastes_fase2.csv'))"),
       md('H1: asociación sexo/desenlace, chi cuadrado. H2: distribución de edad, Mann-Whitney. H3: diferencia de proporciones moto/otros en conductores y pasajeros. H4: coeficiente de noche ajustado en GLM binomial. Las hipótesis formales, estadísticos, efectos e IC están en la tabla. p guardado como cero indica subdesbordamiento numérico, no probabilidad exactamente cero.'),
       code("display(Image(filename=str(OUT/'figures/f2_01_normalidad.png')))\ndisplay(f2['bootstrap'])\ndisplay(Image(filename=str(OUT/'figures/f2_02_bootstrap.png')))\ndisplay(tabla('regresion_logistica_inferencial.csv'))"),
       md('Los cuatro contrastes rechazan H0 con Holm, con magnitudes distintas. La diferencia negativa de letalidad de moto en esta población condicionada a lesión registrada no demuestra menor riesgo por viaje. Nocturnidad conserva OR ajustado próximo a 1,85. Los IC son marginales; faltan exposición y confusores. Las variables se llevan a predicción por plausibilidad y disponibilidad, no solo por valores p. No se interpretan las nuevas variables de contexto como causas sin otro diseño.')]
    books += [('Fase_2_Inferencia',c)]
    c=[md('# Fase 3 — Modelo final y evaluación\n\n'+intro),code(SETUP),
       md('## Diseño registrado y comparación obligatoria\n\nPrimero se compararon varias familias con 24 entradas: logística, árbol, Bayes y LightGBM más Dummy; 13 configuraciones y 39 ajustes CV. Luego se mejoró preparación/contexto y se compararon ocho LightGBM en tres cortes. El resultado final es un único modelo serializado con 31 características. Las comparaciones permanecen como evidencia exigida por la cátedra.'),
       code("display(json.loads((ROOT/'protocolo.json').read_text(encoding='utf8')))\nfrom modelado import main as modelar\nresultado=modelar()\ndisplay(pd.read_csv(OUT/'modelado/inicial/ranking_CV.csv'))\ninicial=pd.read_csv(OUT/'modelado/inicial/metricas_prueba_2025.csv')\ndisplay(inicial[inicial.regla.eq('F1_validacion')])\ndisplay(pd.read_csv(OUT/'modelado/final/ranking_CV.csv'))"),
       md('La llamada reutiliza los resultados reales registrados; no vuelve a elegir con 2026. `src/reproducir.py --reentrenar` permite reconstruir los ajustes, que seguirán siendo retrospectivos. Desarrollo 2017–2023; calibración 2024 H1; umbral 2024 H2. La selección final por AP mejoró la referencia en tres cortes. Los congelamientos originales se conservan como evidencia histórica.'),
       code("display(json.loads((ROOT/'data/metodologia/congelamiento_final_original.json').read_text(encoding='utf8')))\ndisplay(pd.read_csv(OUT/'modelado/final/comparacion_completa.csv'))\ndisplay(pd.read_csv(OUT/'modelado/final/metricas_evaluacion.csv'))"),
       md('2025 es retrospectivo porque ya se conocían sus resultados al mejorar. El corte 2026 fue abierto después del congelamiento original; cubre enero–septiembre, no el año entero. Ambos modelos se ajustaron con los mismos períodos y se comparan sobre idénticas víctimas. Se conserva prevalencia natural y se excluyen IDs, desenlace, gravedad y conteos de víctimas de las entradas.'),
       code("from graficos import main as analizar\ninterpretaciones=analizar()\ndisplay(tabla('importancia_modelo_final.csv'))")]
    g=json.loads((OUT/'interpretaciones_fase3.json').read_text(encoding='utf8'))
    for name,text in g.items():c += [code(f"display(Image(filename=str(OUT/'figures/{name}')))"),md(text)]
    c += [code("display(tabla('errores_por_grupo_modelo_final.csv'))\ndisplay(tabla('errores_mayor_confianza_modelo_final.csv').drop(columns=['id','pesid']))\ndisplay(pd.read_csv(OUT/'modelado/final/intervalos_mejora_2026.csv'))"),
       md('## Conclusión\n\nEn 2026 AUC pasa de 0,799 a 0,845 y F1 macro de 0,647 a 0,675. El ganador detecta 132 fallecidos más y produce 717 falsas alarmas menos que la referencia. Todavía omite 2.657 fallecidos y genera 3.277 falsas alarmas. El umbral alto recall sacrifica precisión; la decisión práctica depende de costos no definidos. Las características se conocen después del siniestro, no se predice quién se accidentará. Uso académico; no causalidad ni validación clínica o para Paraguay.')]
    books += [('Fase_3_Modelado',c)]
    for name,cells in books:
        book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}})
        path=ROOT/'notebooks'/f'{name}.ipynb';nb.write(book,path)
        print('Ejecutando',name,flush=True)
        NotebookClient(book,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}},allow_errors=False).execute()
        nb.write(book,path);html,_=HTMLExporter().from_notebook_node(book);(OUT/'html'/f'{name}.html').write_text(html,encoding='utf8')
        print('Notebook y HTML verificados',name,flush=True)


if __name__=='__main__':main()
