"""Ejecuta en kernel nuevo y exporta HTML sin necesitar kernels instalados al usuario."""
import json
import os
import argparse
import subprocess
import tempfile
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]


def sincronizar_markdown(nb, resultados):
    """Materializa la interpretación verificada en una celda Markdown real."""
    s = resultados['solapamiento']
    sexos = resultados['tablas']['errores_sexo']
    cm = resultados['tablas']['matrices']
    nombre = resultados['metadatos']['modelo']
    c = cm.loc[nombre]
    contexto = resultados['contexto']
    interpretaciones = {
        '### Interpretación territorial H1': contexto['interpretacion_h1'],
        '### Interpretación de las fuentes H3': contexto['interpretacion_h3'],
        '### H4 y edad desconocida: alcance del antecedente': contexto['interpretacion_edad'],
        '### Respuesta integrada a la pregunta original': contexto['conclusion_integral']}
    for celda in nb.cells:
        if celda.cell_type == 'markdown':
            for titulo, texto in interpretaciones.items():
                if celda.source.startswith(titulo):
                    celda.source = titulo + '\n' + texto + '\n'
            if celda.source.startswith('### Interpretación de las métricas y la línea base'):
                t = resultados['tablas']['metricas_test']; cv = resultados['tablas']['validacion']
                b = resultados['tablas']['brechas']; ganador = t.loc[nombre]; base = t.loc['Línea Base (Dummy)']
                celda.source = f'''### Interpretación de las métricas y la línea base
Dummy obtiene accuracy {base['Accuracy']:.4f}, pero recall fallecidos {base['Recall (Fallecido)']:.4f} y F1 macro {base['F1-Macro']:.4f}: predecir siempre herido oculta todas las fatalidades. El seleccionado por CV es {nombre}, con F1 macro CV {cv.loc[nombre, 'F1-Macro (Validación CV)']:.4f}. En la misma reserva obtiene F1 macro {ganador['F1-Macro']:.4f} (diferencia frente a Dummy {ganador['F1-Macro']-base['F1-Macro']:+.4f}), recall {ganador['Recall (Fallecido)']:.4f}, precisión {ganador['Precision (Fallecido)']:.4f} y AUC {ganador['ROC-AUC']:.4f}. Otro candidato puede tener AUC mayor sin cambiar el criterio de selección previamente fijado.

El F1 macro train del seleccionado es {b.loc[nombre, 'F1-Macro (Train)']:.4f} y la brecha train-test es {b.loc[nombre, 'Brecha Absoluta']:+.4f}. La tabla CV informa además train y validación por pliegue; el desvío no es un intervalo poblacional. La brecha pequeña puede reflejar perfiles compartidos y no garantiza ausencia de sobreajuste a la distribución agregada.

Precisión divide los verdaderos positivos por las predicciones positivas; recall divide por los fallecidos reales; F1 combina ambas y F1 macro pondera igual las dos clases. AUC mide ordenamiento, no calibración ni riesgo individual. Las matrices y curvas siguientes permiten evaluar los costos de error que una accuracy aislada ocultaría.
'''
        if celda.cell_type == 'markdown' and celda.source.startswith('### Interpretación de fallos'):
            celda.source = f'''### Interpretación de fallos: conteos y solapamiento verificados
El seleccionado produce **TN={int(c.TN)}, TP={int(c.TP)}, FP={int(c.FP)} y FN={int(c.FN)}** sobre 1.099 filas expandidas. TN/TP son aciertos; FP clasifica una lesión como fatal y FN omite una fatalidad registrada. El FN es prioritario para el objetivo académico, sin convertirlo en un costo clínico ni ajustar umbrales después de mirar test.

El modelo omite **{s['mujeres']} de {int(sexos.loc['Mujer', 'fallecidos'])} fatalidades entre mujeres** (recall {sexos.loc['Mujer', 'recall_fallecidos']:.4f}); en hombres el recall es {sexos.loc['Hombre', 'recall_fallecidos']:.4f}. También omite las **{s['edades_0_29']} fatalidades de edades de 0 a 29 años**. Los grupos **se superponen**: {s['interseccion']} omisiones son mujeres de esas edades. Su unión es {s['mujeres']} + {s['edades_0_29']} - {s['interseccion']} = **{s['union']}**, no su suma directa; los **{s['restantes']} FN restantes** son hombres con edad ignorada. La tabla de descomposición del notebook contiene categorías mutuamente excluyentes y deja la identidad comprobada.

Las mismas combinaciones de sexo y edad reciben la misma predicción: el árbol clasifica herido a todos los perfiles femeninos, jóvenes y de edad ignorada. En los perfiles masculinos de 30 años o más predice fallecido, generando falsas alarmas entre quienes están etiquetados herido; no puede distinguir circunstancias dentro del perfil. Las tasas globales de error y las tasas FN tienen denominadores diferentes. Una tasa global baja puede coexistir con omisión total de fallecidos.

Las filas reconstruyen frecuencias, no historias clínicas identificables. No se conocen velocidad, protección, lesión inicial, tipo de choque ni atención para explicar mecanismos individuales. La ponderación global de clases no garantiza recall equilibrado entre subgrupos. Este patrón impide recomendar aplicaciones individuales y no permite inferir causalidad. La interpretación acotada queda pendiente de revisión por el grupo.

Esta celda se actualiza automáticamente desde las salidas verificadas al ejecutar `src/ejecutar_fase3.py`; no contiene métricas elegidas para mejorar el resultado.
'''
    return nb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--documentos', action='store_true', help='Regenerar Word y PDF desde el notebook ejecutado.')
    parser.add_argument('--verificar', action='store_true', help='Ejecutar las pruebas completas sin escribir logs o capturas.')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from src.complementos_fase3 import leer_resultados, leer_figuras
    destino = ROOT / 'output/fase3'
    destino.mkdir(parents=True, exist_ok=True)
    nbpath = ROOT / 'notebooks/Fase3_Accidentes_AUDITADA.ipynb'
    nb = nbformat.read(nbpath, as_version=4)
    auxiliares_antes = {p.resolve() for carpeta in ['data', 'notebooks', 'src', 'output', 'docs']
                        for p in (ROOT / carpeta).rglob('*') if p.suffix.lower() in {'.png', '.csv', '.json'}}
    with tempfile.TemporaryDirectory(prefix='accidentes_fase3_') as runtime:
        env = dict(os.environ, JUPYTER_RUNTIME_DIR=str(Path(runtime) / 'jupyter'),
                   MPLCONFIGDIR=str(Path(runtime) / 'matplotlib'), IPYTHONDIR=str(Path(runtime) / 'ipython'),
                   PYTHONIOENCODING='utf-8')
        km = KernelManager(kernel_name='python3')
        km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
        cliente = NotebookClient(nb, km=km, timeout=900, resources={'metadata': {'path': str(ROOT)}})
        try:
            print('Ejecutando Fase 3 en kernel nuevo...', flush=True)
            cliente.execute(cwd=str(ROOT), env=env)
        finally:
            if km.has_kernel:
                km.shutdown_kernel(now=True)
    resultados = leer_resultados(notebook=nb)
    sincronizar_markdown(nb, resultados)
    nbformat.write(nb, nbpath)
    figuras = leer_figuras()
    html, _ = HTMLExporter().from_notebook_node(nb)
    (destino / 'Fase3_Accidentes_AUDITADA.html').write_text(html, encoding='utf-8')
    assert len(figuras) == 11 and html.count('data:image/png;base64,') >= 11
    auxiliares_despues = {p.resolve() for carpeta in ['data', 'notebooks', 'src', 'output', 'docs']
                          for p in (ROOT / carpeta).rglob('*') if p.suffix.lower() in {'.png', '.csv', '.json'}}
    assert auxiliares_antes == auxiliares_despues, 'Aparecieron PNG, CSV o JSON inesperados.'
    n_codigo = sum(c.cell_type == 'code' for c in nb.cells)
    print(f'Notebook y HTML: {n_codigo} celdas de código ejecutadas, 11 figuras embebidas, ningún PNG/CSV/JSON generado.', flush=True)
    if args.documentos:
        subprocess.run([sys.executable, str(ROOT / 'src/generar_documentos.py'), '--pdf'], cwd=ROOT, check=True)
    if args.verificar:
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
