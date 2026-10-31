"""Indice offline y paquete final acumulativo con codigo y resultados."""
import html
import json
import zipfile
from pathlib import Path

from common import ROOT,OUT,sha256,save_json


def main():
    results=json.loads((OUT/'fase3_resultados.json').read_text(encoding='utf-8'))
    table_rows=''.join('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in [
        row['familia'],f"{row['MAE_train']:.2f}",f"{row['MAE_CV']:.2f}",
        f"{row['MAE_test']:.2f}",f"{row['R2']:.3f}"] )+'</tr>' for row in results['comparacion'])
    index='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Resultados del proyecto de siniestros</title><style>
body{font:17px/1.55 system-ui,sans-serif;color:#20323f;background:#f4f6f8;margin:0}
main{max-width:1020px;margin:35px auto;background:white;padding:35px;border-radius:10px}
h1,h2{color:#21496d;line-height:1.25}a{color:#175985}table{width:100%;border-collapse:collapse;font-size:15px}
th,td{padding:10px;text-align:left;border-bottom:1px solid #dbe2e8}th{background:#21496d;color:white}
.note{padding:15px 20px;border-left:4px solid #ba7730;background:#fff8ec}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}
.card{padding:15px;border:1px solid #dbe2e8;border-radius:6px}img{max-width:100%;height:auto}.small{font-size:14px;color:#526674}
</style><main><p class="small">Proyecto integrador · 31 de octubre de 2026</p>
<h1>Pronóstico mensual de siniestros en Paraguay</h1>
<p>Tres fases calculadas con 108 meses de datos publicados por el INE, con fuente Patrulla Caminera. Alan Alcaraz, Leandro Ferreira y Jorge Rios.</p>
<div class="note"><strong>Resultado principal:</strong> SVR fue elegido por validación temporal. En 2024 obtuvo MAE 10,87 y RMSE 15,32 siniestros por mes; su R² fue −0,477. Mejora las referencias operativas, pero sus predicciones casi planas no anticipan bien los picos.</div>
<h2>Leer las tres fases</h2><div class="grid">
<section class="card"><h3>Fase 1</h3><p>Fuentes, auditoría, limpieza, diccionarios y diez gráficos interpretados.</p><a href="output/reports/Fase_1_Preparacion_y_EDA.pdf">Informe PDF · 16 páginas</a><br><a href="output/html/Fase_1_Preparacion_EDA.html">Notebook ejecutado en HTML</a></section>
<section class="card"><h3>Fase 2</h3><p>Cuatro contrastes, supuestos, intervalos, bootstrap y corrección múltiple.</p><a href="output/reports/Fase_2_Inferencia.pdf">Informe PDF · 10 páginas</a><br><a href="output/html/Fase_2_Inferencia.html">Notebook ejecutado en HTML</a></section>
<section class="card"><h3>Fase 3</h3><p>Modelos de cuatro familias, referencias y evaluación temporal.</p><a href="output/reports/Fase_3_Modelado_y_Evaluacion.pdf">Informe PDF · 15 páginas</a><br><a href="output/html/Fase_3_Modelado.html">Notebook ejecutado en HTML</a></section></div>
<h2>Cómo le fue al aprender y pronosticar</h2><p>MAE: accidentes de error medio por mes; menor es mejor. El ajuste de entrenamiento es a un paso con antecedentes reales; validación y prueba son a doce pasos. Las columnas no representan exactamente el mismo escenario.</p>
<table><thead><tr><th>Familia</th><th>MAE ajuste</th><th>MAE validación</th><th>MAE prueba</th><th>R² prueba</th></tr></thead><tbody>TABLE_ROWS</tbody></table>
<p>Random Forest ajusta mejor el entrenamiento y generaliza peor. Ridge consigue un error de prueba ligeramente menor que SVR, pero no se cambia la elección después de observar prueba.</p>
<img src="output/figures/f3_02_prueba.png" alt="Predicciones de 2024 comparadas con los conteos reales y la referencia estacional">
<h2>Material adicional</h2><ul>
<li><a href="output/reports/Comprension_del_problema.pdf">Comprensión del problema · 3 páginas</a></li>
<li><a href="output/reports/Informe_Integrador.pdf">Informe integrador · 21 páginas</a></li>
<li><a href="GUIA_PARA_ENTENDER_FASE_3.md">Guía para entender la Fase 3</a></li>
<li><a href="data/processed/serie_mensual.csv">CSV mensual limpio con trazabilidad</a></li>
<li><a href="output/tables/comparacion_train_CV_test.csv">Tabla de comparación de modelos</a></li>
<li><a href="output/verificacion_final.json">Comprobaciones de integridad y ejecución</a></li>
<li><a href="README.md">Reproducción, estructura y fuentes</a></li></ul>
<h2>Alcance de la proyección</h2><p>La evaluación es retrospectiva sobre 2024. La proyección posterior al último dato corresponde a 2025 con corte diciembre de 2024; no es un pronóstico actualizado de 2027. La banda empírica es orientativa y no garantiza cobertura futura.</p>
<p class="small">Asistencia de IA declarada en los informes. La consigna reserva al grupo la revisión y adopción de decisiones metodológicas e interpretación. Faltan los legajos. No se enviaron archivos a terceros.</p></main></html>'''.replace('TABLE_ROWS',table_rows)
    (ROOT/'ABRIR_RESULTADOS.html').write_text(index,encoding='utf-8')
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/'Fase3_DataScience_Alcaraz-Ferreira-Rios.zip'
    include=[]
    for file in sorted(ROOT.rglob('*')):
        relative=file.relative_to(ROOT)
        if not file.is_file() or any(part in {'.git','__pycache__','.ipynb_checkpoints','qa','dist'} for part in relative.parts):continue
        if file.suffix=='.zip':continue
        include.append((file,relative))
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file,relative in include:archive.write(file,arcname=str(Path(ROOT.name)/relative))
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:raise ValueError('Archivo ZIP corrupto.')
        names=archive.namelist()
        for required in ['README.md','data/processed/serie_mensual.csv','output/reports/Fase_3_Modelado_y_Evaluacion.pdf','notebooks/Fase_3_Modelado.ipynb','output/models/modelo_pronostico.joblib']:
            if not any(name.replace('\\','/').endswith(required) for name in names):raise ValueError(f'Falta {required}')
    save_json('paquete_final.json',dict(archivo=str(target.relative_to(ROOT)),archivos=len(include),
               bytes=target.stat().st_size,sha256=sha256(target),contenido='Tres fases acumulativas, originales, codigo, notebooks, HTML, informes y modelos; excluye QA y metadatos .git'))
    print('Paquete verificado:',target,'archivos:',len(include),'MB:',round(target.stat().st_size/1024**2,2))


if __name__=='__main__':main()
