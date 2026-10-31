"""Notebooks ejecutados, HTML de resultados y documentacion reproducible."""
import importlib.metadata
import json
import os
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter
import pandas as pd
from common import ROOT, OUT, load_data

SETUP='''from pathlib import Path
import sys, json
import pandas as pd
from IPython.display import display, Image, Markdown
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'protocolo.json').exists())
sys.path.insert(0, str(ROOT / 'src'))
from common import OUT, DATA, load_data
from preparar import prepare
if not (DATA / 'victimas_modelado.joblib').exists():
    from common import RAW
    if not (RAW / 'pessoas_2017.zip').exists():
        from descargar_fuentes import main as descargar
        descargar()
    prepare()
pd.set_option('display.max_columns', 16)
pd.set_option('display.max_colwidth', 90)
def tabla(nombre):
    return pd.read_csv(OUT / 'tables' / nombre)
'''


def md(x):return nbf.v4.new_markdown_cell(x)
def code(x):return nbf.v4.new_code_cell(x)


def notebooks():
    os.environ['IPYTHONDIR']=str(ROOT/'tmp/ipython')
    os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'tmp/jupyter')
    intro='Material de apoyo con asistencia de IA. El grupo debe revisar y comprender el código y adoptar sus decisiones e interpretaciones. No se fabrican personas ni se afirma causalidad. La unidad es una participación de víctima lesionada registrada por PRF, no el riesgo por viaje.'
    f1=json.loads((OUT/'fase1_resultados.json').read_text(encoding='utf8'))
    c=[md('# Fase 1 — Preparación y exploración\n\n'+intro),code(SETUP),md('## Pregunta y objetivos\n\n¿Qué características personales, vehiculares y del siniestro se asocian con el fallecimiento registrado frente a lesiones no fatales en víctimas de carreteras federales de Brasil, 2017–2025? Se busca construir una tabla auditable, explorar patrones, contrastar hipótesis y evaluar clasificación en un año posterior.'),
       md('## Reconstrucción desde originales\n\nSe verifican hashes, seleccionan desenlaces conocidos y claves positivas, y se une por ID real con validación muchos a uno. La llamada siguiente reconstruye los datos desde los 18 ZIP; no depende de una edición manual. El desenlace nunca se imputa.'),
       code("d = prepare(force=True)\nassert len(d) == 754098 and d.pesid.is_unique\ndisplay(d.head())\ndisplay(tabla('auditoria_union_y_clases.csv'))\ndisplay(tabla('particiones.csv'))"),
       md('## Limpieza, diccionario y faltantes\n\nEdad cero ambigua y valores imposibles pasan a ausencia sin eliminar víctimas. Las medianas y categorías se aprenden en cada entrenamiento. Faltantes no se presuponen aleatorios. Los códigos de persona cero del archivo original no se cuentan como personas identificadas.'),
       code("display(tabla('bitacora_limpieza.csv'))\ndisplay(tabla('diccionario_final.csv'))"),
       md('## Exploración exclusiva de 2017–2023\n\n2024 se reserva para calibración y umbral; 2025 para prueba. El perfilado original había revisado cantidades y cobertura de esos años, sin usarlos para buscar modelos.'),
       code("from fase1 import main as explorar\n_ = explorar()\ndisplay(tabla('descriptivos_desarrollo.csv'))\ndisplay(tabla('concentracion_categorias.csv'))\ndisplay(tabla('correlacion_spearman.csv'))\ndisplay(tabla('contingencia_sexo_fila.csv'))")]
    for name,text in f1['interpretaciones'].items():c += [code(f"display(Image(filename=str(OUT / 'figures/{name}')))"),md(text)]
    c += [md('## Conclusión y puente\n\nSe observa desbalance, superposición de edades, cambios temporales y diferencias por vehículo y horario. Las claves permiten analizar esas características conjuntamente. Se contrastarán cuatro hipótesis: sexo, edad, usuario de moto y nocturnidad ajustada. Los registros no incluyen exposición ni seguimiento completo; asociación no demuestra causalidad y la predicción debe evaluarse aparte.')]
    all_books=[('Fase_1_Preparacion_EDA',c)]
    c=[md('# Fase 2 — Inferencia estadística\n\n'+intro),code(SETUP),md('## Correcciones y protocolo\n\nSe reemplazan filas expandidas por fichas reales, se consideran víctimas del mismo accidente y se conservan faltantes sin inventar edades. Se declaran cuatro contrastes bilaterales, alfa 0,05, Holm y tres familias clásicas más GLM. Las pruebas clásicas seleccionan una víctima aleatoria por accidente: sus resultados ponderan accidentes, no todas las víctimas por igual.'),
       code("protocolo = json.loads((ROOT / 'protocolo.json').read_text(encoding='utf8'))\ndisplay(protocolo['inferencia'])\nfrom fase2 import main as inferir\nf2 = inferir()\ndisplay(tabla('supuestos_fase2.csv'))"),
       md('## Hipótesis, efectos e intervalos\n\nH1 evalúa asociación sexo/desenlace; H2 diferencia de distribuciones de edad; H3 diferencia de letalidad moto/otros entre conductores y pasajeros; H4 nocturnidad ajustada mediante GLM binomial y SE por accidente. H0 y H1 formales se muestran en la tabla. p guardado como cero indica subdesbordamiento numérico, no probabilidad exactamente cero.'),
       code("display(tabla('contrastes_fase2.csv'))\ndisplay(Image(filename=str(OUT / 'figures/f2_01_normalidad.png')))"),
       md('Shapiro y Q-Q señalan distribución de edad no normal; se usa Mann-Whitney, que no equivale en general a comparar únicamente medianas. H1 verifica frecuencias esperadas; H3 suficientes éxitos y fracasos; el GLM verifica rango y convergencia. La independencia entre accidentes sigue siendo una aproximación.'),
       code("display(f2['bootstrap'])\ndisplay(Image(filename=str(OUT / 'figures/f2_02_bootstrap.png')))\ndisplay(tabla('regresion_logistica_inferencial.csv'))"),
       md('## Interpretación\n\nLos cuatro contrastes rechazan H0 con Holm, con efectos de magnitudes diferentes. La pequeña diferencia negativa para moto se refiere a víctimas ya lesionadas registradas y NO demuestra menor riesgo por viaje. Nocturnidad conserva OR ajustado próximo a 1,85, sin demostrar causa. Los IC son marginales; faltan exposición y confusores, y hay selección por registro y covariables completas. Se conservan variables plausibles para predicción sin seleccionarlas solo por valores p.')]
    all_books += [('Fase_2_Inferencia',c)]
    c=[md('# Fase 3 — Clasificación y evaluación con desbalance\n\n'+intro),code(SETUP),
       md('## Experimento fijado antes de prueba\n\nDesarrollo 2017–2023; tres cortes temporales CV; calibración 2024 H1; umbral 2024 H2; prueba 2025. No se usan IDs, gravedad del accidente, indicadores de muertos/heridos ni atribución posterior de causa como predictores. La selección usa AP media, no la exactitud de prueba.'),
       code("display(json.loads((ROOT / 'protocolo.json').read_text(encoding='utf8')))\nfrom modelado import specs, fit_and_freeze, evaluate_once\ndisplay(pd.DataFrame(specs()))\nfrozen = fit_and_freeze()\nf3 = evaluate_once()\ndisplay(frozen)"),
       md('Los modelos fueron entrenados realmente. Cuando el registro congelado existe se reutiliza el resultado documentado; no se vuelve a seleccionar ni reajustar con 2025. Desde fuentes y sin resultados guardados, estas funciones reconstruyen la búsqueda y la evaluación con el mismo protocolo. La corrección técnica de categorías está documentada y ocurrió antes de prueba.'),
       code("display(tabla('ranking_CV.csv'))\ndisplay(tabla('validacion_temporal_todas.csv'))\ndisplay(tabla('metricas_train_validacion.csv'))"),
       md('## Prueba final y desbalance\n\nLa prueba mantiene prevalencia natural: 83.550 heridos y 6.043 fallecidos. Se comparan pesos y variantes sin pesos solo en entrenamiento; se calibra por separado y se fijan tres umbrales antes de prueba. No se utiliza SMOTE ni se inventan fallecidos.'),
       code("display(tabla('metricas_prueba_2025.csv'))\ndisplay(tabla('intervalos_prueba_bootstrap.csv'))")]
    texts=json.loads((OUT/'interpretaciones_fase3.json').read_text(encoding='utf8'))
    for name,text in texts.items():c += [code(f"display(Image(filename=str(OUT / 'figures/{name}')))"),md(text)]
    c += [md('## Errores y comparación honesta'),code("display(tabla('errores_por_grupo.csv'))\ndisplay(tabla('errores_mayor_confianza.csv').drop(columns=['id','pesid']))\ndisplay(f3['modelo_anterior'])"),
          md('El aporte de variables se demuestra con mayor claridad al comparar dentro del mismo Brasil: AUC 0,619 con sexo/edad frente a 0,806 con 24 características. Frente a Paraguay anterior (AUC 0,581; F1 macro 0,530), no hay poblaciones ni prevalencias equivalentes. El recall principal actual, 40,58%, es menor que 45,41% anterior: no mejoraron todos los indicadores. Cambiar el umbral aumenta detección a costa de falsas alarmas. No se elige una nueva configuración después de observar prueba.'),
          md('## Conclusión\n\nEl modelo aprende información adicional de tipo de siniestro, vehículo, localización, rol y entorno. Hay mejora real frente a referencias en el mismo año, aunque persisten errores importantes y optimismo de entrenamiento. Su uso es académico; no está validado para triaje, causalidad o Paraguay. Futuras modificaciones requieren otro experimento y un período verdaderamente nuevo para evaluar generalización.')]
    all_books += [('Fase_3_Modelado',c)]
    for name,cells in all_books:
        nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
        path=ROOT/'notebooks'/f'{name}.ipynb'
        nbf.write(nb,path)
        print('Ejecutando',name,flush=True)
        client=NotebookClient(nb,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}},allow_errors=False)
        client.execute()
        nbf.write(nb,path)
        html,_=HTMLExporter().from_notebook_node(nb)
        (OUT/'html'/f'{name}.html').write_text(html,encoding='utf8')
        print('Notebook y HTML listos',name,flush=True)


def documents():
    f3=json.loads((OUT/'fase3_resultados.json').read_text(encoding='utf8'))
    p=f3['prueba']
    readme='''# Clasificación de gravedad de víctimas — PRF Brasil

Abrir **ABRIR_RESULTADOS.html** para ver resultados, PDFs y notebooks. El modelo usa 24 características reales; distingue mejor que sexo/edad, pero sigue produciendo errores importantes. Los informes son material de apoyo con asistencia de IA que el grupo debe verificar y comprender antes de presentar.

## Datos y alcance

754.098 participaciones con desenlace conocido, 2017–2025; 703.273 heridas y 50.825 fallecidas. Las 632.713 ocurrencias originales se vinculan con personas mediante `id`. No se fabrican individuos ni se confunden filas sin `pesid` válido con personas reales. No hay identidad civil longitudinal. Brasil significa carreteras federales cubiertas por PRF, no toda circulación vial ni Paraguay.

El directorio vecino `INVESTIGACION_DATASETS/fuentes_brasil` contiene los originales descargados. Si no existe, se usan `data/raw` y el descargador incluido. Procedencia, URL y SHA-256 en `data/manifiesto_origenes.json`; diccionarios oficiales y perfil completo en las fuentes y `data/perfil_original_prf.json`.

Fuentes oficiales: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf y https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes . Los datos se presentan como abiertos reutilizables por PRF. No se enviaron solicitudes institucionales ni archivos a terceros.

## Reproducir

Python 3.13 recomendado, dependencias declaradas en `requirements.txt`; se usaron semilla 42 y seis hilos para LightGBM. Desde esta carpeta:

```powershell
python -m pip install -r requirements.txt
python src/descargar_fuentes.py
python src/preparar.py
python src/run_all.py
python src/entregables.py
python src/informes_pdf.py
python src/verificar.py
```

No hace falta descargar de nuevo si los originales están presentes. `run_all.py` conserva la selección y los resultados de prueba existentes. Para reproducir desde cero, usar una copia nueva sin salidas/modelos generados, manteniendo el protocolo: eso reproduce un experimento retrospectivo, no convierte 2025 en una nueva prueba ciega. Un cambio de decisión después de ver 2025 exige otra evaluación futura independiente.

Los notebooks están ejecutados y también pueden abrirse por separado. El primero reconstruye desde originales. Los PDF se generan desde tablas congeladas sin reentrenar. La versión de reportlab puede estar en un entorno distinto del de ML; no cambia las métricas. La ejecución local puede tardar varios minutos y requiere varios GB de RAM; solo la descarga necesita internet. Si PRF cambia un archivo, el hash falla deliberadamente y exige documentar otra versión.

## Inferencia

```powershell
python src/inferencia.py --entrada data/ejemplo_inferencia.csv --salida output/ejemplo_predicciones.csv
```

La entrada es una tabla con las 24 características YA preparadas según `src/preparar.py`, sin objetivo; no el CSV PRF bruto. Mantener unidades y códigos. El script conserva claves opcionales, aplica codificación, calibración y umbral guardados. No se utiliza para decidir atención médica.

## Estructura y archivos

- `data/processed/victimas_limpias.parquet`: dataset limpio portable; `victimas_limpias.csv.gz` es la versión CSV disponible localmente; el cache joblib acelera lecturas.
- `notebooks/`: tres notebooks; `output/html/`: sus versiones ejecutadas.
- `output/reports/`: comprensión, tres fases e integrador.
- `output/tables/`: auditoría, bitácora, diccionario, contrastes, CV, métricas y errores.
- `models/modelo_seleccionado.joblib`: pipeline final con calibrador y umbral.
- `protocolo.json` y `output/seleccion_congelada_antes_prueba.json`: decisiones anteriores a prueba.
- `contexto/correccion_antes_de_prueba.txt`: corrección técnica; los diagnósticos preliminares no son resultados finales.

El paquete excluye los originales (>25 MB), caches y CSV limpio duplicado; incluye Parquet y los scripts para reconstruirlos. El modelo se seleccionó por AP de CV, no por la mayor métrica de 2025. Los intervalos de prueba remuestrean accidentes completos, manteniendo juntas sus víctimas.

## Pendientes del grupo

Completar legajos; revisar cambio de país y dataset según lo acordado con la profesora; comprender y adoptar decisiones e interpretaciones; declarar el uso de IA; generar sus propias contribuciones e historial Git. No se inventa aprobación docente ni autoría de los integrantes. Esta carpeta no fue publicada ni compartida externamente.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf8')
    deps=['pandas','numpy','scipy','scikit-learn','lightgbm','statsmodels','matplotlib','seaborn','joblib','pyarrow','nbformat','nbclient','nbconvert','ipykernel','pypdf']
    (ROOT/'requirements.txt').write_text('\n'.join(f'{m}=={importlib.metadata.version(m)}' for m in deps)+'\nreportlab==4.4.9\n',encoding='utf8')
    guide=f'''# Cómo interpretar la fase 3 y el desbalance

**Sí hay mejora en la discriminación con más información real.** En las mismas víctimas de Brasil de 2025, AUC pasa de 0,619 (sexo/edad) a {p['ROC_AUC']:.3f}; AP de 0,104 a {p['AP']:.3f}; F1 macro de 0,512 a {p['F1_macro']:.3f}. La mejora de AP tiene IC bootstrap por accidente aproximadamente 0,187–0,211. No es porcentaje de exactitud ni comparación causal entre países.

Una regla que responde siempre herido acierta 93,26% porque fallecidos son 6,74%. Detecta cero fallecidos. Por eso exactitud alta sola no sirve.

| Regla fijada antes de prueba | Detecta de cada 100 fallecidos | Acierta de cada 100 alertas de fallecimiento | Falsas alarmas en 2025 |
|---|---:|---:|---:|
| Siempre herido | 0 | 0 (ninguna alerta) | 0 |
| Umbral 0,50 | 7,40 | 58,05 | 323 |
| Umbral principal 0,1866 | 40,58 | 31,78 | 5.264 |
| Mayor detección, umbral 0,0415 | 81,98 | 13,51 | 31.721 |

**Qué hicimos:** entrenamiento con todos los casos reales; comparación de pesos sin tocar prueba; selección por AP temporal; calibración con 2024 H1 y prevalencia natural; umbral con 2024 H2; evaluación de todos los puntos congelados en 2025. No inventamos fallecidos, no duplicamos víctimas para inflar N ni balanceamos el examen. SMOTE no es necesario para tener un experimento válido y aquí no se utilizó.

**Precisión** responde cuántas alertas fueron correctas. **Recall** responde cuántos fallecidos reales fueron detectados. **F1 de fallecidos** combina ambas; **F1 macro** promedia las dos clases. **AP** resume el ordenamiento de casos en la curva precisión-recall y depende de la prevalencia. **AUC-ROC** mide discriminación. **Brier/calibración** examinan las probabilidades, sin prometer certeza individual.

El umbral principal detecta 2.452 de 6.043 fallecidos, omite 3.591 y clasifica erróneamente como fallecidos a 5.264 heridos. El punto de mayor detección omite 1.089 fallecidos. Decidir cuál conviene depende del costo de perder un caso frente al de una falsa alarma; no se ha definido una aplicación clínica ni una política institucional.

**Qué aprendió:** tipo de siniestro, vehículo, municipio, rol, ruralidad y edad aportan información. La importancia por permutación se midió en validación; no equivale a causalidad. AP de entrenamiento 0,395 frente a 0,298 en validación y 0,302 en prueba muestra optimismo en el ajuste: más filas no elimina el sobreajuste.

**Comparación anterior:** Paraguay tenía AUC 0,581, F1 macro 0,530, precisión 23,24% y recall 45,41%. Brasil mejora discriminación y precisión al punto principal, pero su recall principal es menor. Las poblaciones, prevalencias y divisiones son diferentes. La comparación controlada dentro de Brasil es la evidencia más clara del aporte de más variables.

**Frase defendible:** “El nuevo dataset permitió relacionar características reales y superar ampliamente al modelo de solo sexo y edad en el mismo año de prueba. No logramos una predicción perfecta; mostramos la sensibilidad del resultado al umbral, las falsas alarmas y los fallecidos no detectados”.
'''
    (ROOT/'GUIA_FASE_3_Y_DESBALANCE.md').write_text(guide,encoding='utf8')
    rows=pd.read_csv(OUT/'tables/metricas_prueba_2025.csv').query("regla == 'F1_validacion'")
    htmlrows=''.join(f'<tr><td>{r.familia}</td><td>{r.AP:.3f}</td><td>{r.ROC_AUC:.3f}</td><td>{r.precision:.1%}</td><td>{r.recall:.1%}</td><td>{r.F1_macro:.3f}</td></tr>' for r in rows.itertuples())
    html=f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gravedad de víctimas — Brasil</title><style>body{{font:17px/1.6 system-ui;background:#edf2f5;color:#20323f;margin:0}}main{{max-width:1050px;margin:30px auto;background:white;padding:32px}}h1,h2{{line-height:1.2;color:#21496d}}a{{color:#175985}}table{{border-collapse:collapse;width:100%;font-size:15px}}td,th{{padding:9px;border-bottom:1px solid #ccd8df;text-align:left}}th{{background:#21496d;color:white}}img{{width:100%;height:auto}}.note{{background:#fff4e8;border-left:4px solid #b76f2e;padding:16px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}}.card{{border:1px solid #ccd8df;padding:16px}}</style><main><p>Proyecto Integrador · 31/10/2026 · Alan Alcaraz, Leandro Ferreira y Jorge Rios</p><h1>Más información real mejora la clasificación, con límites importantes</h1><p>PRF Brasil, 2017–2025: 754.098 víctimas heridas o fallecidas. Se usaron 24 características y se reservaron 89.593 víctimas de 2025 para prueba.</p><div class="note"><strong>Resultado:</strong> AUC 0,806 y F1 macro 0,651, frente a 0,619 y 0,512 usando solo sexo y edad en el mismo Brasil. El modelo principal detecta 40,58% de los fallecidos, con precisión de 31,78%. El año de prueba no se usó para elegirlo.</div><h2>Las tres fases</h2><div class="grid">'''
    for n,title,file in [(1,'Preparación y exploración','Preparacion_EDA'),(2,'Inferencia','Inferencia'),(3,'Modelado','Modelado')]:
        pdf=['Fase_1_Preparacion_y_EDA.pdf','Fase_2_Inferencia.pdf','Fase_3_Modelado_y_Evaluacion.pdf'][n-1]
        html+=f'<div class="card"><h3>Fase {n}: {title}</h3><a href="output/reports/{pdf}">Informe PDF</a><br><a href="output/html/Fase_{n}_{file}.html">Notebook ejecutado en HTML</a></div>'
    html+=f'''</div><h2>Prueba final: fallecidos como clase positiva</h2><table><tr><th>Modelo</th><th>AP</th><th>AUC ROC</th><th>Precisión</th><th>Recall</th><th>F1 macro</th></tr>{htmlrows}</table><p>AP no es porcentaje de aciertos. Siempre herido alcanza 93,26% de exactitud y detecta cero fallecidos. Los umbrales se fijaron con validación de 2024; el punto de recall alto no es una política clínica aprobada.</p><img src="output/figures/f3_03_confusion.png" alt="Matriz de confusión en 2025"><h2>Qué hacer con el desbalance</h2><p>Comparamos pesos en entrenamiento, calibramos por separado y ajustamos el umbral conservando prevalencia real en prueba. El punto de mayor detección encuentra 81,98% de fallecidos, pero precisión baja a 13,51% y genera 31.721 falsas alarmas. No hay una única métrica que resuelva ese costo.</p><img src="output/figures/f3_07_umbrales.png" alt="Precisión y recall a distintos umbrales"><h2>Material para revisar y defender</h2><ul><li><a href="GUIA_FASE_3_Y_DESBALANCE.md">Guía sencilla de resultados y desbalance</a></li><li><a href="output/reports/Informe_Integrador.pdf">Informe integrador</a></li><li><a href="output/reports/Comprension_del_problema.pdf">Comprensión del problema</a></li><li><a href="data/processed/victimas_limpias.parquet">Dataset limpio en Parquet</a></li><li><a href="output/tables/metricas_prueba_2025.csv">Métricas de todos los modelos y umbrales</a></li><li><a href="README.md">Reproducción, fuentes y pendientes</a></li></ul><div class="note">El recall principal de Brasil (40,58%) es menor que el 45,41% del proyecto anterior de Paraguay: no mejoraron todos los indicadores. País, población y prevalencia cambian; la comparación de sexo/edad y modelo completo dentro de Brasil es más justa. Material de apoyo con IA que el equipo debe comprender, revisar y adoptar antes de entregar. Legajos pendientes.</div></main></html>'''
    (ROOT/'ABRIR_RESULTADOS.html').write_text(html,encoding='utf8')


if __name__=='__main__':
    documents()
    notebooks()
