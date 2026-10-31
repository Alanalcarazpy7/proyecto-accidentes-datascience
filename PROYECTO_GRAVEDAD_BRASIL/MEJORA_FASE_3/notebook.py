"""Genera y ejecuta un notebook corto del complemento."""
import os
import json
from pathlib import Path
import nbformat as nb
from nbclient import NotebookClient
from nbconvert import HTMLExporter

HERE=Path(__file__).resolve().parent;OUT=HERE/'output'
(HERE/'tmp/ipython').mkdir(parents=True,exist_ok=True)
(HERE/'tmp/jupyter').mkdir(parents=True,exist_ok=True)
os.environ['IPYTHONDIR']=str(HERE/'tmp/ipython')
os.environ['JUPYTER_RUNTIME_DIR']=str(HERE/'tmp/jupyter')


def main():
    md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
    cells=[md('# Mejora acotada de la fase 3 — PRF Brasil\n\nOcho configuraciones, 24 ajustes CV y una nueva prueba cronológica. Se conserva el experimento anterior. Material de apoyo con IA que el grupo debe verificar y comprender.'),
        code("from pathlib import Path\nimport sys,json\nimport pandas as pd\nfrom IPython.display import display,Image\nHERE=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'mejorar.py').exists())\nsys.path.insert(0,str(HERE))\nOUT=HERE/'output'\npd.set_option('display.max_columns',16)\ndisplay(json.loads((HERE/'protocolo.json').read_text(encoding='utf8')))"),
        md('## Preparación y contexto vehicular\n\nSe incluyen todos los vehículos identificados del accidente antes de seleccionar víctimas; se deduplican por claves reales y se resta el vehículo propio. Así se evita construir contexto únicamente con lesionados. Marca es un prefijo aproximado, y trazados compuestos se separan en indicadores. No se usan conteos de víctimas o gravedad como predictores.'),
        code("from mejorar import main as ejecutar\nejecutar()\ndisplay(pd.read_csv(OUT/'auditoria_nuevas_variables_2017_2025.csv'))\ndisplay(json.loads((OUT/'diccionario_bloques.json').read_text(encoding='utf8')))"),
        md('Los datos originales, modelos y métricas del primer experimento se verifican por hash y no se modifican. Si las salidas existen, se reutilizan los resultados registrados; desde cero se ejecuta la búsqueda y se congela la selección antes de abrir 2026. Reproducir resultados ya vistos no constituye una nueva prueba independiente.'),
        md('## Búsqueda temporal acotada\n\nMismos cortes de 2021, 2022 y 2023. La regla elige mayor AP media con mejora en al menos dos cortes respecto de la referencia. La grilla no se amplía según la prueba.'),
        code("display(pd.read_csv(OUT/'validacion_temporal.csv'))\ndisplay(pd.read_csv(OUT/'ranking_CV.csv'))\ndisplay(Image(filename=str(OUT/'figures/01_busqueda_CV.png')))"),
        md('## Congelamiento y evaluación\n\nAmbos modelos usan desarrollo 2017–2023, calibración 2024 H1 y umbral 2024 H2. 2025 es comparación retrospectiva. 2026 se leyó después de congelar modelos/umbrales; se informa el período publicado, no el año completo.'),
        code("display(json.loads((OUT/'congelamiento.json').read_text(encoding='utf8')))\ndisplay(json.loads((OUT/'auditoria_2026.json').read_text(encoding='utf8')))\nmetricas=pd.read_csv(OUT/'metricas_evaluacion.csv')\ndisplay(metricas[metricas.regla.eq('F1_validacion')])\ndisplay(pd.read_csv(OUT/'comparacion_completa.csv'))"),
        code("display(Image(filename=str(OUT/'figures/02_comparacion_2026.png')))\ndisplay(Image(filename=str(OUT/'figures/03_curvas_2026.png')))"),
        md('AUC y AP miden ordenamiento; AP depende de la prevalencia y no es exactitud. La comparación se hace sobre idénticas víctimas. Precisión y recall dependen del umbral fijado con 2024. Una ganancia en AUC no implica ausencia de falsas alarmas o detección perfecta.'),
        code("display(Image(filename=str(OUT/'figures/04_confusion_2026.png')))\ndisplay(metricas[(metricas.particion.eq('2026_prueba_nueva'))])\ndisplay(pd.read_csv(OUT/'intervalos_mejora_2026.csv'))"),
        md('## Incertidumbre y límites\n\nLos intervalos usan 300 remuestras pareadas de accidentes completos. No corrigen todos los sesgos ni garantizan estabilidad posterior. Las características se observan en un siniestro ya ocurrido; la tarea no es anticipar quién se accidentará ni tomar decisiones clínicas. La nueva utilidad predictiva no prueba causalidad. Las hipótesis originales de fase 2 se conservan y las nuevas decisiones de preparación se documentan para integrar el proyecto.'),
        code("display(json.loads((OUT/'verificacion.json').read_text(encoding='utf8')))"),
    ]
    book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}})
    path=OUT/'Mejora_Fase_3.ipynb';nb.write(book,path)
    print('Ejecutando notebook de mejora',flush=True)
    NotebookClient(book,timeout=1200,kernel_name='python3',resources={'metadata':{'path':str(HERE)}},allow_errors=False).execute()
    nb.write(book,path)
    html,_=HTMLExporter().from_notebook_node(book);(OUT/'Mejora_Fase_3.html').write_text(html,encoding='utf8')
    print('Notebook y HTML ejecutados sin errores',flush=True)


if __name__=='__main__':main()
