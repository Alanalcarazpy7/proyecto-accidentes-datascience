"""Genera tres notebooks explicados y los ejecuta con el kernel Python local."""
import argparse
import json
import os
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from common import OUT, ROOT


SETUP="""from pathlib import Path
import sys
import json
import pandas as pd
from IPython.display import display, Image, Markdown
ROOT = next(p for p in [Path.cwd(), Path.cwd().parent] if (p / 'protocolo.json').exists())
sys.path.insert(0, str(ROOT / 'src'))
from common import OUT, PROTOCOL
from data_prep import main as preparar
if not (ROOT / 'data/processed/serie_mensual.csv').exists():
    _ = preparar()
pd.set_option('display.max_columns', 15)
pd.set_option('display.max_colwidth', 100)
display(Markdown('**Protocolo temporal:** desarrollo 2016–2022; calibración 2023; prueba 2024.'))
"""


def md(text):return nbf.v4.new_markdown_cell(text)
def code(text):return nbf.v4.new_code_cell(text)


def generate():
    (ROOT/'notebooks').mkdir(parents=True,exist_ok=True)
    (OUT/'html').mkdir(parents=True,exist_ok=True)
    intro='Material de apoyo elaborado con asistencia de IA. El grupo debe revisar y asumir las decisiones metodológicas e interpretar los resultados antes de entregar. No se fabrican observaciones individuales.'
    cells=[md('# Fase 1 — Preparación y análisis exploratorio\n\n'+intro),code(SETUP),
           md('## Pregunta y unidad\n\n¿Con qué precisión podemos pronosticar doce cantidades mensuales de siniestros registrados por la Caminera en Central e Interior, frente a referencias sencillas? Una fila es un mes, no una víctima. La fecha representa el primer día del período mensual.'),
           md('## Reconstrucción desde originales\n\nLa función siguiente lee los siete XLSX, verifica sus hashes, controla componentes y totales, conserva versiones y produce el CSV. La implementación auditable está en `src/data_prep.py`; no utiliza tablas modificadas a mano.'),
           code("_ = preparar()\nauditoria = json.loads((OUT / 'auditoria_datos.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([auditoria]).T.rename(columns={0:'Resultado'}))"),
           code("serie = pd.read_csv(ROOT / 'data/processed/serie_mensual.csv', parse_dates=['fecha'])\nassert serie['fecha'].is_unique and len(serie) == 108\ndisplay(serie.head())\ndisplay(pd.read_csv(OUT / 'tables/bitacora_limpieza.csv'))"),
           md('## Diccionarios y calidad\n\nLos guiones solo se convierten en ceros en los componentes validados. No hay objetivos imputados. Se conserva la procedencia por celda y no se eliminan extremos legítimos.'),
           code("display(pd.read_csv(OUT / 'tables/diccionario_original.csv'))\ndisplay(pd.read_csv(OUT / 'tables/diccionario_final.csv'))"),
           md('## Exploración de desarrollo\n\nSe excluyen 2023 y 2024 de la exploración. Las medias anteriores destinadas a modelado están desplazadas; las medias móviles contemporáneas de un gráfico descriptivo no se convierten en predictores del mismo mes.'),
           code("from phase1 import main as explorar\nresultado = explorar()\ndisplay(pd.read_csv(OUT / 'tables/descriptivos_desarrollo.csv'))\ndisplay(pd.read_csv(OUT / 'tables/resumen_por_mes_desarrollo.csv'))")]
    f1=json.loads((OUT/'fase1_resultados.json').read_text(encoding='utf-8'))
    for name,text in f1['interpretaciones'].items():
        cells.extend([code(f"display(Image(filename=str(OUT / 'figures/{name}')))"),md(text)])
    cells.extend([md('## Tablas bivariadas y concentraciones\n\nLas tablas de contingencia describen conteos de siniestros por semestre y tipo. No se unen artificialmente cuadros para asignar características a personas.'),
                  code("display(pd.read_csv(OUT / 'tables/contingencia_semestre_tipo_absoluta.csv'))\ndisplay(pd.read_csv(OUT / 'tables/contingencia_semestre_tipo_por_fila.csv'))\ndisplay(pd.read_csv(OUT / 'tables/contingencia_semestre_tipo_por_columna.csv'))\ndisplay(pd.read_csv(OUT / 'tables/frecuencias_tipos_desarrollo.csv'))"),
                  md('## Conclusión y cuatro hipótesis\n\nLa serie permite una comparación temporal, pero el número de períodos es pequeño y la cobertura no está validada externamente. Se contrastarán alineación mensual (H1), diferencia entre semestres (H2), tendencia anual (H3) y asociación condicional con el rezago uno (H4). No se exige que todas resulten significativas. Los resultados no describen riesgo por viaje ni causalidad.')])
    notebooks=[('Fase_1_Preparacion_EDA.ipynb',cells)]
    cells=[md('# Fase 2 — Inferencia temporal\n\n'+intro),code(SETUP),
           md('## Hipótesis y decisiones previas\n\nSe usan solo 84 meses de desarrollo. Cuatro contrastes, alfa 0,05 y Bonferroni; se incluyen comparación de medidas apareadas múltiples, comparación de dos medidas apareadas, correlación y regresión robusta. `protocolo.json` se fijó antes de ejecutar modelos. Los supuestos temporales no se sustituyen por una prueba de normalidad.'),
           code("display(PROTOCOL['hipotesis'])\nfrom phase2 import main as inferir\nresultado = inferir()"),
           md('## Verificación de supuestos\n\nShapiro-Wilk, Q-Q y Levene son diagnósticos. Wilcoxon no exige homogeneidad de varianzas. Los bloques anuales y HAC aproximan la dependencia; no garantizan estabilidad ni exogeneidad.'),
           code("display(pd.read_csv(OUT / 'tables/supuestos_fase2.csv'))\ndisplay(Image(filename=str(OUT / 'figures/f2_01_supuestos_qq.png')))"),
           md('## Resultados de cuatro contrastes\n\nLos IC del 95% son marginales, no simultáneos. Las decisiones de rechazo usan los valores p Bonferroni. Los grados de libertad paramétricos no se inventan para Wilcoxon o referencias circulares.'),
           code("contrastes = pd.read_csv(OUT / 'tables/contrastes_fase2.csv')\ndisplay(contrastes[['id','prueba','estadistico','gl','p','p_bonferroni','efecto','ic_bajo','ic_alto','decision']])"),
           md('H1 y H2 no aportan evidencia concluyente de calendario o diferencia semestral. H3 tiene solo siete referencias circulares: su baja resolución impide alcanzar el umbral corregido. No rechazar no equivale a aceptar ausencia de efecto. H4 sí presenta asociación condicional con el mes anterior bajo los supuestos del modelo; no demuestra capacidad de pronóstico anual.'),
           code("display(Image(filename=str(OUT / 'figures/f2_02_semestres.png')))\ndisplay(pd.read_csv(OUT / 'tables/diferencias_pareadas_semestres.csv'))"),
           md('## Bootstrap de pares y bloques\n\nSe remuestrean años con sus semestres emparejados para el efecto medio. El IC clásico t y el bootstrap estiman esa misma diferencia media; el contraste Wilcoxon se refiere a un centro de distribución simétrica y debe distinguirse de ese estimando.'),
           code("display(resultado['comparacion_ic_media_semestres'])\ndisplay(Image(filename=str(OUT / 'figures/f2_03_bootstrap.png')))"),
           code("display(pd.read_csv(OUT / 'tables/regresion_inferencial_HAC.csv'))\ndisplay(pd.read_csv(OUT / 'tables/sensibilidad_HAC.csv'))\ndisplay(resultado['regresion'])\ndisplay(Image(filename=str(OUT / 'figures/f2_04_residuos.png')))"),
           md('## Conclusión y paso a modelado\n\nLa asociación con el rezago uno justifica evaluarlo, junto con otras representaciones históricas, sin garantizar su utilidad. El calendario se mantiene como control predefinido y se evalúa por pronóstico. No se usan pruebas para buscar retrospectivamente una combinación significativa. Faltan medidas de exposición y cambios institucionales; ninguna conclusión es causal.')]
    notebooks.append(('Fase_2_Inferencia.ipynb',cells))
    cells=[md('# Fase 3 — Aprendizaje, pronóstico y evaluación\n\n'+intro),code(SETUP),
           md('## Diseño experimental y grilla\n\nDos referencias y cuatro familias aprendidas: Ridge, Random Forest, SVR y ETS. Las configuraciones se comparan en cuatro cortes anuales 2019–2022. Cada corte pronostica doce meses desde un único origen. La búsqueda no incluye prueba ni calibración.'),
           code("from models import specifications, FEATURES\ndisplay(pd.DataFrame(specifications()))\ndisplay(FEATURES)\nfrom phase3 import main as modelar\nresultado = modelar()"),
           md('En una reproducción con resultados idénticos se reutiliza el cálculo registrado. Desde una carpeta limpia, la misma llamada reconstruye la búsqueda y evaluación. El archivo `seleccion_congelada_antes_prueba.json` registra el criterio y los parámetros previos a evaluar 2024.'),
           code("display(pd.read_csv(OUT / 'tables/mejores_por_familia_CV.csv'))\ndisplay(json.loads((OUT / 'seleccion_congelada_antes_prueba.json').read_text(encoding='utf-8')))"),
           md('## Qué aprendió cada modelo\n\nSe informa ajuste, validación y prueba. El ajuste usa un paso con antecedentes reales; validación y prueba son doce pasos. Random Forest ajusta más el entrenamiento, pero generaliza peor. SVR fue elegido por validación, aunque Ridge obtenga después un MAE de prueba ligeramente menor.'),
           code("comparacion = pd.read_csv(OUT / 'tables/comparacion_train_CV_test.csv')\ndisplay(comparacion)\ndisplay(Image(filename=str(OUT / 'figures/f3_01_comparacion.png')))\ndisplay(Image(filename=str(OUT / 'figures/f3_04_cortes.png')))") ,
           md('## Prueba final de 2024\n\nMAE, RMSE, MAPE y R² se calculan sin redondear las predicciones. MAPE no es un porcentaje de exactitud. R² negativo se comunica explícitamente: la mejora frente a las referencias operativas no equivale a explicar bien las fluctuaciones de 2024.'),
           code("display(pd.read_csv(OUT / 'tables/metricas_prueba_2024.csv'))\ndisplay(Image(filename=str(OUT / 'figures/f3_02_prueba.png')))\ndisplay(pd.read_csv(OUT / 'tables/cinco_errores_mayores_2024.csv'))"),
           md('Las predicciones SVR de prueba son casi planas (aproximadamente 132–135 siniestros/mes), mientras los valores reales varían entre 126 y 174. La generalización lograda es principalmente una estimación del nivel; no anticipa los picos.'),
           code("display(Image(filename=str(OUT / 'figures/f3_03_residuos.png')))\ndisplay(Image(filename=str(OUT / 'figures/f3_07_horizonte.png')))") ,
           md('## Interpretación sin usar prueba para seleccionar\n\nLa perturbación de entradas se realiza en validación y ejecuta la recursión completa. Cambios pequeños o negativos no prueban una influencia causal. La baja sensibilidad del SVR es coherente con su fuerte regularización y perfil casi constante.'),
           code("display(pd.read_csv(OUT / 'tables/importancia_perturbacion_CV.csv'))\ndisplay(pd.read_csv(OUT / 'tables/coeficientes_Ridge.csv'))\ndisplay(pd.read_csv(OUT / 'tables/importancia_RF.csv'))\ndisplay(Image(filename=str(OUT / 'figures/f3_05_importancia.png')))") ,
           md('## Bandas y proyección con corte declarado\n\nEl radio empírico se obtiene con errores de 2023 tras fijar el modelo. La dependencia temporal impide garantizar cobertura del 90%. El total anual no recibe un intervalo formal basado en un único bloque de calibración. La proyección de 2025 usa corte diciembre 2024; no se etiqueta como pronóstico actual de 2027.'),
           code("display(resultado['calibracion'])\ndisplay(pd.read_csv(OUT / 'tables/pronostico_2025_corte_2024.csv'))\ndisplay(Image(filename=str(OUT / 'figures/f3_06_proyeccion.png')))") ,
           md('## Modelo guardado e inferencia reproducible\n\nSe conservan por separado el modelo evaluado en 2024 y el reajustado con todos los datos. El ejemplo siguiente reproduce la proyección guardada. El script `src/inference.py` también acepta un CSV mensual nuevo validado, manteniendo la especificación elegida.'),
           code("import joblib\nfrom models import forecast\nartefacto = joblib.load(OUT / 'models/modelo_pronostico.joblib')\ndisplay(forecast(artefacto['model'], 12).rename('prediccion').to_frame())\nprint('Origen:', artefacto['origen'])\nprint('Selección por validación:', artefacto['selected_spec'])"),
           md('## Conclusión\n\nSVR reduce errores frente a las dos referencias en 2024, pero el R² negativo y el perfil casi plano limitan su utilidad. No se modifica al ganador tras consultar prueba. Para mejorar o pronosticar 2027 se necesitan datos comparables recientes, nueva validación y factores externos realmente disponibles al emitir el pronóstico. El grupo debe revisar estas decisiones e interpretaciones según la consigna.')]
    notebooks.append(('Fase_3_Modelado.ipynb',cells))
    for name,cells in notebooks:
        notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}})
        nbf.write(notebook,ROOT/'notebooks'/name)
    return [name for name,_ in notebooks]


def execute(names):
    for name in names:
        path=ROOT/'notebooks'/name;notebook=nbf.read(path,as_version=4)
        client=NotebookClient(notebook,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
        client.execute();nbf.write(notebook,path)
        exporter=HTMLExporter();exporter.exclude_input=False
        body,_=exporter.from_notebook_node(notebook)
        (OUT/'html'/path.with_suffix('.html').name).write_text(body,encoding='utf-8')
        print('Notebook ejecutado y HTML:',name,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--solo-generar',action='store_true');args=parser.parse_args()
    names=generate()
    if not args.solo_generar:execute(names)
