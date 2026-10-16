"""Tablas y figuras complementarias; funciones llamadas por el notebook existente."""
from pathlib import Path
import json
import base64
from io import StringIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (confusion_matrix, roc_curve, precision_recall_curve,
                             f1_score, roc_auc_score)
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from sklearn.base import clone
from sklearn.model_selection import GroupKFold
from IPython.display import display, Markdown
import nbformat

MIME_RESULTADOS = 'application/vnd.accidentes.fase3+json'
ROOT = Path(__file__).resolve().parents[1]


def publicar_resultados(ns):
    """Guarda las tablas en las salidas del ipynb; no crea archivos auxiliares."""
    tablas = {'metricas_test': ns['df_resultados_test'], 'validacion': ns['df_reporte_cv'],
              'brechas': ns['df_brechas'], 'coeficientes': ns['df_coef'],
              'metricas_train': ns['metricas_train'], 'metricas_cv': pd.DataFrame(ns['cv_metricas']),
              'vehicular': ns['tabla_vehicular'], 'sensibilidad_ganador': ns['df_sensibilidad'],
              **ns['tablas_contexto'], **ns['tablas_extra'], **{'grilla_' + k: v[['params', 'mean_train_f1_macro', 'mean_test_f1_macro', 'std_test_f1_macro', 'rank_test_f1_macro']].assign(params=lambda d: d.params.astype(str)) for k, v in ns['grillas_cv'].items()}}
    evidencia = {'tablas': {k: json.loads(v.to_json(orient='table', double_precision=15, force_ascii=False))
                           for k, v in tablas.items()}, 'seleccion': ns['seleccion_cerrada'],
                 'metadatos': ns['metadatos'], 'versiones': ns['versiones'],
                 'solapamiento': ns['solapamiento_FN'], 'equivalencia': ns['equivalencia_frecuencias'],
                 'conclusiones': ns['conclusion'], 'procedencia': ns['auditoria_fuente'],
                 'contexto': ns['auditoria_contexto']}
    display({MIME_RESULTADOS: evidencia, 'text/plain':
             'Resultados estructurados embebidos: las tablas, metadatos y conclusiones anteriores permiten regenerar los informes sin archivos intermedios.'}, raw=True)


def leer_resultados(root=ROOT, notebook=None):
    """Lee exclusivamente el notebook ejecutado, sin reentrenar ni consultar CSV de Fase 3."""
    nb = notebook if notebook is not None else nbformat.read(root / 'notebooks/Fase3_Accidentes_AUDITADA.ipynb', as_version=4)
    datos = [o.data[MIME_RESULTADOS] for c in nb.cells if c.cell_type == 'code'
             for o in c.outputs if o.output_type in ['display_data', 'execute_result'] and MIME_RESULTADOS in o.data]
    if len(datos) != 1:
        raise ValueError('Ejecutar primero el notebook: falta su bloque único de resultados.')
    r = dict(datos[0])
    r['tablas'] = {k: pd.read_json(StringIO(json.dumps(v)), orient='table') for k, v in r['tablas'].items()}
    return r


def leer_figuras(root=ROOT):
    """Extrae imágenes PNG embebidas como bytes; nunca las escribe a disco."""
    nb = nbformat.read(root / 'notebooks/Fase3_Accidentes_AUDITADA.ipynb', as_version=4)
    figuras = {}
    for c in nb.cells:
        if c.cell_type != 'code':
            continue
        claves = c.metadata.get('figuras_fase3', [])
        imagenes = [o.data['image/png'] for o in c.outputs
                    if o.output_type in ['display_data', 'execute_result'] and 'image/png' in o.data]
        if claves:
            if len(claves) != len(imagenes):
                raise ValueError(f'Imágenes incompletas en {claves}: ejecutar el notebook completo.')
            figuras.update({k: base64.b64decode(v) for k, v in zip(claves, imagenes)})
    if set(figuras) != {f'F3-{i:02d}' for i in range(1, 12)}:
        raise ValueError('Faltan figuras embebidas de Fase 3.')
    return figuras


def preparar_contexto(root=ROOT):
    """Audita tablas agregadas H1/H3 y la edad sin expandir ni unir sus universos."""
    import hashlib

    def original(prefijo):
        p = next((root / 'data').glob(prefijo + '*.csv'))
        hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        return pd.read_csv(p, sep=';', dtype=str, encoding='utf-8-sig')

    def numero(valor):
        # En las celdas de conteos de estas tablas, '-' indica ausencia de casos.
        s = str(valor).strip()
        return 0 if s == '-' else int(s.replace('.', ''))

    hashes = {}
    zonas = pd.read_csv(root / 'output/victimas_zona_resumen.csv').set_index('zona')
    zonas = zonas.loc[['Asunción', 'Central', 'Interior'], ['heridos', 'fallecidos', 'total_victimas']].copy()
    raw_z = original('12.2.6.')
    z_total = raw_z.iloc[0]
    for zona, col in [('Asunción', 'ASUNCION'), ('Central', 'ZONA CENTRAL'), ('Interior', 'INTERIOR')]:
        esperado = [numero(z_total['HERIDOS - ' + col]), numero(z_total['MUERTOS - ' + col]),
                    numero(z_total['TOTAL - ' + col])]
        if zonas.loc[zona].tolist() != esperado:
            raise ValueError('El resumen territorial no coincide con 12.2.6: ' + zona)
    assert (zonas.heridos + zonas.fallecidos == zonas.total_victimas).all()
    zonas['tasa_fallecidos_pct'] = 100 * zonas.fallecidos / zonas.total_victimas
    h1 = pd.DataFrame([zonas.loc[['Asunción', 'Central']].iloc[:, :3].sum(), zonas.loc['Interior'].iloc[:3]],
                      index=pd.Index(['Metropolitana', 'Interior'], name='grupo')).astype(int)
    h1['tasa_fallecidos_pct'] = 100 * h1.fallecidos / h1.total_victimas

    raw_t, raw_m = original('12.2.5.'), original('12.2.10.')
    anual_t = raw_t.iloc[0]
    posiciones = raw_m.index[raw_m.iloc[:, 0].str.strip().eq('2021')]
    assert len(posiciones) == 1
    pos = posiciones[0]
    anual_m = raw_m.loc[pos]
    meses_t, meses_m = raw_t.iloc[1:].reset_index(drop=True), raw_m.iloc[pos+1:pos+13].reset_index(drop=True)
    assert len(meses_t) == len(meses_m) == 12
    assert meses_t.iloc[:, 0].str.strip().tolist() == meses_m.iloc[:, 0].str.strip().tolist()
    filas = []
    for i in range(12):
        h, f = [numero(meses_t.loc[i, c]) for c in ['HERIDOS - TOTAL', 'MUERTOS - TOTAL']]
        hm, fm = [numero(meses_m.loc[i, c]) for c in ['HERIDOS', 'MUERTOS']]
        assert h + f == numero(meses_t.loc[i, 'TOTAL - TOTAL'])
        assert hm + fm == numero(meses_m.loc[i, 'TOTAL'])
        assert h >= hm and f >= fm
        # 12.2.5 coincide numéricamente con 12.2.6 sin Asunción, también por mes.
        for campo, valor in [('HERIDOS', h), ('MUERTOS', f)]:
            z = raw_z.iloc[i+1]
            assert valor == numero(z[campo + ' - TOTAL']) - numero(z[campo + ' - ASUNCION'])
        filas.append(dict(mes=meses_t.iloc[i, 0].strip(), heridos_12_2_5=h, fallecidos_12_2_5=f,
                          heridos_12_2_10=hm, fallecidos_12_2_10=fm,
                          heridos_resta=h-hm, fallecidos_resta=f-fm))
    mensual = pd.DataFrame(filas)
    th, tf = numero(anual_t['HERIDOS - TOTAL']), numero(anual_t['MUERTOS - TOTAL'])
    mh, mf = numero(anual_m['HERIDOS']), numero(anual_m['MUERTOS'])
    assert mensual[['heridos_12_2_5', 'fallecidos_12_2_5', 'heridos_12_2_10', 'fallecidos_12_2_10']].sum().tolist() == [th, tf, mh, mf]
    vehicular = pd.DataFrame([
        {'grupo': '12.2.10: siniestros con motociclistas', 'heridos': mh, 'fallecidos': mf},
        {'grupo': '12.2.5: total de su cobertura', 'heridos': th, 'fallecidos': tf},
        {'grupo': 'Resta histórica (cobertura no demostrada)', 'heridos': th-mh, 'fallecidos': tf-mf}])
    vehicular['fraccion_fallecidos'] = vehicular.fallecidos / (vehicular.heridos + vehicular.fallecidos)
    # Se comprueba la procedencia del CSV anterior, sin acreditar sus etiquetas.
    anterior = pd.read_csv(root / 'output/victimas_vehiculo_limpio.csv')
    conteos = pd.crosstab(anterior.tipo_usuario, anterior.es_fallecido).reindex(
        index=['Motociclista', 'Otro Vehiculo'], columns=[0, 1])
    if conteos.isna().any().any() or conteos.to_numpy().tolist() != [[mh, mf], [th-mh, tf-mf]]:
        raise ValueError('El CSV vehicular no reproduce los conteos y la resta histórica.')
    assert len(anterior) == th + tf
    assert anterior.es_motociclista.eq(anterior.tipo_usuario.eq('Motociclista').astype(int)).all()
    assert anterior.es_fallecido.eq(anterior.gravedad.eq('Fallecido').astype(int)).all()
    conteos.columns = ['heridos', 'fallecidos']
    conteos['total'] = conteos.sum(axis=1)
    conteos['origen'] = ['Conteos de 12.2.10; rol de víctima no acreditado',
                         'Resta 12.2.5 menos 12.2.10; categoría no acreditada']

    demo = pd.read_csv(root / 'output/victimas_individual_limpio.csv')
    ignorada = demo.grupo_edad.eq('Ignorado')
    mayor = demo.grupo_edad.eq('De 60 anos y mas')
    masks = [('Menor de 60, edad conocida', ~ignorada & ~mayor), ('60 años o más', mayor), ('Edad desconocida', ignorada)]
    edad = pd.DataFrame([{'grupo': nombre, 'victimas': int(mask.sum()),
                         'heridos': int(demo.loc[mask, 'es_fallecido'].eq(0).sum()),
                         'fallecidos': int(demo.loc[mask, 'es_fallecido'].sum())} for nombre, mask in masks]).set_index('grupo')
    assert edad.victimas.tolist() == [4832, 308, 353]
    assert demo.loc[ignorada, 'edad_orden'].eq(-1).all() and demo.loc[ignorada, 'es_adulto_mayor'].eq(0).all()
    assert demo.loc[~ignorada, 'edad_orden'].ge(0).all()
    hist = json.loads((root / 'output/fase2/resultados_fase2_consolidados.json').read_text(encoding='utf-8'))
    antecedentes = pd.DataFrame(hist['hipotesis']).set_index('hipótesis')
    integrado = pd.DataFrame([
        ['H1', 'Zona', '12.2.6', 'Tasas y contraste histórico territorial', 'Cobertura y agrupación; no vínculo individual'],
        ['H2', 'Sexo', '12.2.1', 'Asociación histórica y predictor demográfico', 'Señal limitada; no causa ni riesgo individual'],
        ['H3', 'Motocicletas', '12.2.5 / 12.2.10', 'Descripción y contraste histórico condicionado', 'Rol de víctima y subconjunto no acreditados'],
        ['H4', 'Edad', '12.2.1', 'Categoría nominal en modelo; antecedente ordinal', 'Histórico incluyó -1; desconocidos separados']
    ], columns=['hipotesis', 'factor', 'fuente', 'evidencia', 'limite']).set_index('hipotesis')
    tablas = {'territorio': zonas, 'territorio_h1': h1, 'vehicular_mensual': mensual,
              'vehicular_procedencia': conteos, 'edad_auditoria': edad,
              'antecedentes_historicos': antecedentes, 'hipotesis_integradas': integrado}
    auditoria = {'sha256_originales': hashes, 'periodo': 2021, 'meses_verificados': 12,
                 'csv_vehicular_reconstruido': True, 'categorias_vehiculares_acreditadas': False,
                 'universo_vehicular_comparable_acreditado': False,
                 'fuente_pdf': 'https://www.ine.gov.py/Publicaciones/Biblioteca/documento/240/Anuario%20Estadistico%202021.pdf',
                 'paginas_fuente': [307, 311],
                 'fuente_territorial_pdf': 'Patrulla Caminera, MOPC y Policía Nacional (12.2.6)',
                 'nota': 'Las igualdades aritméticas no validan una clasificación por vehículo de la víctima.'}
    diferencia = h1.loc['Interior', 'tasa_fallecidos_pct'] - h1.loc['Metropolitana', 'tasa_fallecidos_pct']
    auditoria['interpretacion_h1'] = (
        f'Las fracciones de fallecidos entre víctimas registradas son Asunción {zonas.loc["Asunción", "tasa_fallecidos_pct"]:.2f} %, '
        f'Central {zonas.loc["Central", "tasa_fallecidos_pct"]:.2f} % e Interior {zonas.loc["Interior", "tasa_fallecidos_pct"]:.2f} %. '
        f'Metropolitana agrupa Asunción y Central: 108/643 = {h1.loc["Metropolitana", "tasa_fallecidos_pct"]:.2f} %; '
        f'Interior la supera en {diferencia:.2f} puntos porcentuales. H1 de Fase 2 informó '
        f'{antecedentes.loc["H1", "estadístico"]}, p crudo {antecedentes.loc["H1", "p_valor_crudo"]:.6f} '
        f'y p Bonferroni {antecedentes.loc["H1", "p_valor_ajustado_bonferroni"]:.6f}; '
        f'{antecedentes.loc["H1", "tamaño_del_efecto"]}. El efecto es pequeño y el p ajustado queda cerca de 0,05. '
        'La decisión corresponde a esa agrupación y familia de cuatro contrastes, no a todas las comparaciones entre zonas. '
        'Mostrar tres tasas revela la heterogeneidad que la dicotomía oculta; no se buscan nuevos p-valores. '
        'La cobertura institucional, el registro, la exposición y la atención pueden influir. Son proporciones entre víctimas, '
        'no riesgo poblacional de accidente ni un efecto causal de residir en una zona. Tres agregados no justifican un '
        'predictor individual generalizable; no se expanden ni se enlazan con los perfiles demográficos.')
    auditoria['interpretacion_h3'] = (
        f'12.2.10 documenta {mh+mf} víctimas de siniestros protagonizados por motociclistas: {mh} heridos y {mf} fallecidos '
        f'({100*mf/(mh+mf):.2f} %). 12.2.5 registra {th+tf} víctimas: {th} heridos y {tf} fallecidos '
        f'({100*tf/(th+tf):.2f} %) en Central e Interior. Se selecciona 2021 en ambas y se verifican los doce meses. '
        f'La resta histórica da {th-mh} heridos y {tf-mf} fallecidos; es la procedencia numérica del CSV vehicular, '
        'no una validación de sus etiquetas. Aunque ambos cuadros citan a Patrulla Caminera y las restas mensuales son '
        'no negativas, no se acredita que cada víctima viajara en moto ni que sean subconjuntos de cobertura idéntica. '
        'Las barras representan fuentes posiblemente superpuestas y no deben sumarse. La serie mensual describe esa '
        'cobertura, sin demostrar estacionalidad ni causas. H3 histórico informó '
        f'{antecedentes.loc["H3", "tamaño_del_efecto"]} y p Bonferroni '
        f'{antecedentes.loc["H3", "p_valor_ajustado_bonferroni"]:.4g}; se conserva como contraste condicionado. '
        'Ni RR, OR ni significación acreditan mayor riesgo individual de motociclistas si las categorías no están validadas. '
        'No se entrena un segundo predictor ni se unen estas filas expandidas con la base demográfica.')
    auditoria['interpretacion_edad'] = (
        'H4: 353 víctimas de edad ignorada (292 heridas y 61 fallecidas) se conservan como categoría nominal independiente. '
        'edad_orden = -1 significa edad desconocida, no inferior a la de los niños. es_adulto_mayor = 0 en esos registros '
        'no acredita edad menor de 60 años. Los grupos separados son 4.832 menores de 60 con edad conocida, 308 de 60 años '
        'o más y 353 desconocidos. El modelo usa únicamente sexo y grupo_edad. El contraste ordinal histórico de Fase 2 '
        'eliminó nulos pero conservó -1; sus resultados no validan una comparación entre mayores y menores de 60. '
        'No se recalcula aquí: un nuevo análisis ordinal debe excluir los desconocidos del orden y reportarlos aparte.')
    auditoria['conclusion_integral'] = (
        'H1 aporta diferencias territoriales descriptivas y un contraste histórico de efecto pequeño, condicionado por '
        'agrupación y cobertura. H2 aporta una asociación por sexo y H4 patrones por categorías de edad, incorporadas como '
        'los únicos predictores del experimento demográfico; el antecedente ordinal de H4 conserva la limitación de -1. '
        'H3 aporta conteos de siniestros con motociclistas y un contraste anterior condicionado a categorías no acreditadas. '
        'Se responde parcialmente la pregunta original: existe señal demográfica retrospectiva limitada y evidencia '
        'territorial separada; no se acredita un riesgo individual por vehículo ni el efecto conjunto de los cuatro factores. '
        'No se predice ocurrencia de siniestros, no se vinculan artificialmente registros y no se afirma causalidad.')
    return tablas, vehicular, auditoria


def mostrar_complementos(ns):
    modelos = {'Línea Base (Dummy)': ns['dummy_baseline'], **ns['modelos_optimizados']}
    xt, yt = ns['X_test_d'], ns['y_test_d']
    ganador = ns['nombre_mejor_modelo']
    elegido = modelos[ganador]
    tablas = {}
    def mostrar(fig, nombre):
        fig.tight_layout()
        plt.show()
        plt.close(fig)
        interpretaciones = {
            'F3-01': 'Las curvas comparan los mismos 1.099 registros expandidos. AUC y Precision-Recall describen discriminación interna; la línea PR corresponde a la prevalencia de esa reserva. La tabla de métricas permite comprobar las diferencias sin atribuir superioridad externa.',
            'F3-02': 'Dummy no identifica ninguna fatalidad. Cada matriz permite contrastar omisiones y falsas alarmas con denominadores idénticos; 0 = herido y 1 = fallecido. La diagonal contiene aciertos y las otras celdas errores.',
            'F3-03': 'El árbol se elige por CV, aunque otro candidato pueda tener AUC de prueba mayor. La mejora de F1 macro frente a Dummy no implica mejor calibración ni una regla clínica.',
            'F3-04': 'La tasa de error divide por todas las filas del grupo; la tasa FN divide solo por sus fallecidos. En particular, el seleccionado no detecta fatalidades entre mujeres de esta reserva y omite las de varios grupos jóvenes. Una tasa global pequeña puede coexistir con omisión total de la clase minoritaria.',
            'F3-05': 'Gini agrega la reducción de impureza de los indicadores de cada variable. La permutación mide caída de F1 macro al desordenar la columna completa; sus barras muestran variación entre permutaciones. No representan causalidad ni intervalos poblacionales.',
            'F3-06': 'La distancia a la diagonal revela discrepancias entre puntuaciones y frecuencia observada. Brier debe compararse con la base, incluso si el modelo mejora F1. No se ajusta calibración en test y no se informa riesgo individual real.',
            'F3-07': 'Las brechas se cuantifican en las tablas. Su tamaño pequeño está condicionado por perfiles repetidos y por la selección dentro de CV; no acredita generalización externa.'}
        display(Markdown('**Interpretación:** ' + interpretaciones[nombre]))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    cms = []
    for nombre, modelo in modelos.items():
        pred, prob = modelo.predict(xt), modelo.predict_proba(xt)[:, 1]
        fpr, tpr, _ = roc_curve(yt, prob)
        pr, re, _ = precision_recall_curve(yt, prob)
        axes[0].plot(fpr, tpr, label=f'{nombre} ({roc_auc_score(yt, prob):.3f})')
        axes[1].step(re, pr, where='post', label=nombre)
        tn, fp, fn, tp = confusion_matrix(yt, pred, labels=[0, 1]).ravel()
        cms.append(dict(Modelo=nombre, TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp)))
    axes[0].plot([0, 1], [0, 1], '--', color='grey')
    axes[0].set(xlabel='Tasa de falsos positivos', ylabel='Recall fallecidos', title='Figura F3-01A. Curvas ROC (misma prueba)')
    axes[1].axhline(np.mean(yt), ls='--', color='grey', label='Prevalencia de prueba')
    axes[1].set(xlabel='Recall fallecidos', ylabel='Precisión fallecidos', title='Figura F3-01B. Curvas Precision-Recall')
    for ax in axes:
        ax.legend(fontsize=7)
    mostrar(fig, 'F3-01')
    tablas['matrices'] = pd.DataFrame(cms).set_index('Modelo')

    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    for ax, (nombre, modelo) in zip(axes.flat, modelos.items()):
        cm = confusion_matrix(yt, modelo.predict(xt), labels=[0, 1])
        ax.imshow(cm, cmap='Blues')
        for (i, j), val in np.ndenumerate(cm):
            ax.text(j, i, str(val), ha='center', va='center', color='white' if val > cm.max() / 2 else 'black')
        ax.set(xticks=[0, 1], yticks=[0, 1], xlabel='Predicho (0 herido; 1 fallecido)', ylabel='Real', title=nombre)
    axes.flat[-1].axis('off')
    fig.suptitle('Figura F3-02. Matrices de confusión en 1.099 filas expandidas')
    mostrar(fig, 'F3-02')

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ns['df_resultados_test'][['F1-Macro', 'Recall (Fallecido)', 'ROC-AUC']].plot.bar(ax=ax)
    ax.set(title='Figura F3-03. Comparación de métricas de prueba', ylabel='Puntuación (0 a 1)', xlabel='Modelo', ylim=(0, 1))
    ax.tick_params(axis='x', rotation=12)
    mostrar(fig, 'F3-03')

    errores = xt.copy()
    errores['real'], errores['predicho'] = yt, elegido.predict(xt)
    errores['puntaje'] = elegido.predict_proba(xt)[:, 1]
    for k, cond in {'FN': (errores.real == 1) & (errores.predicho == 0),
                    'FP': (errores.real == 0) & (errores.predicho == 1),
                    'TP': (errores.real == 1) & (errores.predicho == 1),
                    'TN': (errores.real == 0) & (errores.predicho == 0)}.items():
        errores[k] = cond.astype(int)
    errores['error'] = (errores.real != errores.predicho).astype(int)
    errores['residuo_absoluto'] = abs(errores.real - errores.puntaje)
    ns['predicciones_prueba'] = errores
    fn = errores.FN.eq(1)
    mujer = errores.sexo.eq('Mujer')
    joven = errores.grupo_edad.isin(['De 0 a 13 anos', 'De 14 a 17 anos', 'De 18 a 29 anos'])
    ignorada = errores.grupo_edad.eq('Ignorado')
    solapamiento = {'FN_total': int(fn.sum()), 'mujeres': int((fn & mujer).sum()),
        'edades_0_29': int((fn & joven).sum()), 'interseccion': int((fn & mujer & joven).sum()),
        'union': int((fn & (mujer | joven)).sum()), 'restantes': int((fn & ~(mujer | joven)).sum())}
    assert solapamiento['union'] == solapamiento['mujeres'] + solapamiento['edades_0_29'] - solapamiento['interseccion']
    ns['solapamiento_FN'] = solapamiento
    desglose = []
    for sexo in ['Hombre', 'Mujer']:
        for tramo, mask in [('0-29 años', joven), ('30 años o más', ~joven & ~ignorada), ('Edad ignorada', ignorada)]:
            desglose.append({'Sexo': sexo, 'Tramo': tramo, 'FN': int((fn & errores.sexo.eq(sexo) & mask).sum())})
    tablas['descomposicion_FN'] = pd.DataFrame(desglose)
    assert tablas['descomposicion_FN'].FN.sum() == fn.sum()
    display(Markdown(f"**Solapamiento de omisiones:** mujeres={solapamiento['mujeres']}; edades 0-29={solapamiento['edades_0_29']}; intersección={solapamiento['interseccion']}. La unión contiene {solapamiento['union']} filas, no la suma directa de ambos grupos. Restan {solapamiento['restantes']} FN de hombres con edad ignorada. Son frecuencias reconstruidas, no expedientes individuales."))
    for nombre, columnas in [('perfil', ['sexo', 'grupo_edad']), ('sexo', ['sexo']), ('edad', ['grupo_edad'])]:
        t = errores.groupby(columnas, observed=True).agg(n=('real', 'size'), fallecidos=('real', 'sum'),
                    FN=('FN', 'sum'), FP=('FP', 'sum'), TP=('TP', 'sum'), TN=('TN', 'sum'),
                    errores=('error', 'sum'), residuo_medio=('residuo_absoluto', 'mean'))
        t['tasa_error'] = t.errores / t.n
        t['recall_fallecidos'] = t.TP / t.fallecidos.replace(0, np.nan)
        t['tasa_FN'] = t.FN / t.fallecidos.replace(0, np.nan)
        tablas[f'errores_{nombre}'] = t
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    tablas['errores_edad'][['tasa_error', 'tasa_FN']].rename(columns={'tasa_error': 'Error global', 'tasa_FN': 'Omisión de fallecidos'}).plot.barh(ax=axes[0])
    tablas['errores_sexo'][['tasa_error', 'tasa_FN']].rename(columns={'tasa_error': 'Error global', 'tasa_FN': 'Omisión de fallecidos'}).plot.bar(ax=axes[1], rot=0)
    axes[0].set_ylabel('Grupo de edad')
    for ax in axes:
        ax.set(xlabel='Fracción (0 a 1)' if ax == axes[0] else 'Sexo', xlim=(0, 1) if ax == axes[0] else None)
    axes[0].set_title('F3-04A. Error y omisiones por edad')
    axes[1].set(title='F3-04B. Error y omisiones por sexo', ylabel='Fracción (0 a 1)', ylim=(0, 1))
    mostrar(fig, 'F3-04')

    gini = []
    for nombre in ['Árbol de Decisión', 'Random Forest']:
        model = modelos[nombre]
        enc = model.named_steps['prep'].named_transformers_['cat']
        labels = enc.get_feature_names_out(['sexo', 'grupo_edad'])
        for label, val in zip(labels, model.named_steps['clf'].feature_importances_):
            gini.append({'Modelo': nombre, 'variable': 'sexo' if label.startswith('sexo_') else 'grupo_edad',
                         'indicador': label, 'importancia': float(val)})
    tablas['gini_indicadores'] = pd.DataFrame(gini)
    tablas['gini_variables'] = pd.DataFrame(gini).groupby(['Modelo', 'variable']).importancia.sum().unstack()
    perm = permutation_importance(elegido, xt, yt, scoring='f1_macro', n_repeats=30, random_state=42, n_jobs=1)
    tablas['permutacion'] = pd.DataFrame({'variable': xt.columns, 'media': perm.importances_mean, 'desvio': perm.importances_std})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    tablas['gini_variables'].plot.bar(ax=axes[0], rot=10)
    axes[0].set(title='F3-05A. Importancia Gini agregada', ylabel='Reducción de impureza normalizada')
    axes[1].bar(tablas['permutacion'].variable, tablas['permutacion'].media, yerr=tablas['permutacion'].desvio)
    axes[1].set(title='F3-05B. Permutación del seleccionado', ylabel='Caída de F1 macro (media ± desvío)')
    mostrar(fig, 'F3-05')

    calibracion = []
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].plot([0, 1], [0, 1], '--', color='grey', label='Calibración ideal')
    for nombre, modelo in modelos.items():
        prob = modelo.predict_proba(xt)[:, 1]
        frac, media = calibration_curve(yt, prob, n_bins=5, strategy='uniform')
        axes[0].plot(media, frac, 'o-', label=nombre)
        for x, y in zip(media, frac):
            calibracion.append({'Modelo': nombre, 'puntaje_medio': x, 'fraccion_fallecidos': y})
    axes[0].set(title='F3-06A. Diagnóstico de calibración', xlabel='Puntuación media', ylabel='Fracción observada de fallecidos')
    axes[0].legend(fontsize=7)
    ns['df_resultados_test'][['Brier']].plot.bar(ax=axes[1], legend=False, rot=15)
    axes[1].set(title='F3-06B. Brier (menor es mejor)', ylabel='Error cuadrático de puntuación')
    mostrar(fig, 'F3-06')
    tablas['calibracion'] = pd.DataFrame(calibracion)

    brechas = ns['df_brechas'].copy()
    brechas['F1-Macro (CV)'] = ns['df_reporte_cv']['F1-Macro (Validación CV)']
    tablas['comparacion_etapas'] = brechas
    fig, ax = plt.subplots(figsize=(10, 4))
    brechas[['F1-Macro (Train)', 'F1-Macro (CV)', 'F1-Macro (Test)']].plot.bar(ax=ax, rot=12)
    ax.set(title='Figura F3-07. Entrenamiento, validación y prueba', ylabel='F1 macro (0 a 1)', ylim=(0, .8))
    mostrar(fig, 'F3-07')

    # Mismos hiperparámetros ya fijados; sensibilidad de todos los modelos, sin retuning.
    grupos = ns['X_train_d'].astype(str).agg(' | '.join, axis=1)
    sens = []
    for fold, (tr, va) in enumerate(GroupKFold(4).split(ns['X_train_d'], ns['y_train_d'], grupos), 1):
        assert not set(grupos.iloc[tr]) & set(grupos.iloc[va])
        for nombre, model in modelos.items():
            m = clone(model).fit(ns['X_train_d'].iloc[tr], ns['y_train_d'][tr])
            xv, yv = ns['X_train_d'].iloc[va], ns['y_train_d'][va]
            sens.append({'Modelo': nombre, 'pliegue': fold, 'F1_macro': f1_score(yv, m.predict(xv), average='macro'),
                         'AUC_ROC': roc_auc_score(yv, m.predict_proba(xv)[:, 1]),
                         'n_validacion': len(va), 'perfiles_validacion': grupos.iloc[va].nunique()})
    tablas['sensibilidad_todos'] = pd.DataFrame(sens)
    # Equivalencia exacta de log-verosimilitud expandida frente a frecuencias ponderadas.
    train = ns['X_train_d'].copy()
    train['y'] = ns['y_train_d']
    agregado = train.groupby(['sexo', 'grupo_edad', 'y']).size().rename('frecuencia').reset_index()
    lr = clone(modelos['Regresión Logística'])
    lr.set_params(clf__class_weight=None)
    n = len(train)
    class_n = np.bincount(ns['y_train_d'])
    pesos = agregado.frecuencia.to_numpy() * n / (2 * class_n[agregado.y.to_numpy()])
    lr.fit(agregado[['sexo', 'grupo_edad']], agregado.y, clf__sample_weight=pesos)
    diferencia = float(np.max(abs(lr.predict_proba(xt) - modelos['Regresión Logística'].predict_proba(xt))))
    assert diferencia < .002, diferencia
    ns['equivalencia_frecuencias'] = {'celdas_train': len(agregado),
        'max_diferencia_puntuacion': diferencia, 'tolerancia_numerica': .002,
        'interpretacion': 'La expansión no aporta información adicional a los conteos.'}
    return tablas
