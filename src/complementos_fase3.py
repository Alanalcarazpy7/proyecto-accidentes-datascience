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


def serializar_tabla(tabla):
    """Conserva el esquema pandas y la precisión de p-valores muy pequeños."""
    resultado = json.loads(tabla.to_json(orient='table', double_precision=15, force_ascii=False))
    # to_json redondea ciertos flotantes pequeños por posiciones decimales.
    # El encoder JSON estándar conserva la representación round-trip del float.
    for columna in tabla.columns:
        for fila, valor in zip(resultado['data'], tabla[columna].tolist()):
            if isinstance(valor, float) and np.isfinite(valor):
                fila[columna] = valor
    return resultado


def publicar_resultados(tablas, *, seleccion, metadatos, versiones, solapamiento,
                        equivalencia, conclusiones, procedencia, contexto):
    """Publica evidencia explícita; no lee ni modifica variables del notebook."""
    evidencia = {'tablas': {nombre: serializar_tabla(tabla) for nombre, tabla in tablas.items()},
                 'seleccion': seleccion, 'metadatos': metadatos, 'versiones': versiones,
                 'solapamiento': solapamiento, 'equivalencia': equivalencia,
                 'conclusiones': conclusiones, 'procedencia': procedencia, 'contexto': contexto}
    display({MIME_RESULTADOS: evidencia, 'text/plain':
             'Evidencia estructurada para comprobar resultados; las tablas de estudio se muestran en las secciones anteriores.'}, raw=True)


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


def preparar_contexto(root=ROOT, analisis=None):
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
    from src.auditoria_fase3 import auditar_h3
    tablas_h3, evidencia_h3 = auditar_h3(mensual, root)
    vehicular = pd.DataFrame([
        {'grupo': 'Motocicleta y motocarro (539)', 'heridos': mh, 'fallecidos': mf},
        {'grupo': '12.2.5: total de su cobertura', 'heridos': th, 'fallecidos': tf},
        {'grupo': 'Demás usuarios registrados (785)', 'heridos': th-mh, 'fallecidos': tf-mf}])
    vehicular['fraccion_fallecidos'] = vehicular.fallecidos / (vehicular.heridos + vehicular.fallecidos)
    # El CSV conserva las etiquetas históricas; los nombres científicos se
    # precisan en las tablas agregadas, sin reescribir Fases 1/2 o sus datos.
    path_anterior = root / 'output/victimas_vehiculo_limpio.csv'
    conteos = pd.DataFrame([[mh, mf], [th-mh, tf-mf]],
                           index=pd.Index(['Motociclista', 'Otro Vehiculo'], name='tipo_usuario'), columns=[0, 1])
    if path_anterior.exists():
        anterior = pd.read_csv(path_anterior)
        observado = pd.crosstab(anterior.tipo_usuario, anterior.es_fallecido).reindex(
            index=conteos.index, columns=[0, 1])
        pd.testing.assert_frame_equal(observado, conteos, check_names=False, check_dtype=False)
        assert len(anterior) == th + tf
        assert anterior.es_motociclista.eq(anterior.tipo_usuario.eq('Motociclista').astype(int)).all()
        assert anterior.es_fallecido.eq(anterior.gravedad.eq('Fallecido').astype(int)).all()
    if conteos.isna().any().any() or conteos.to_numpy().tolist() != [[mh, mf], [th-mh, tf-mf]]:
        raise ValueError('El CSV vehicular no reproduce los conteos y la resta histórica.')
    conteos.columns = ['heridos', 'fallecidos']
    conteos['total'] = conteos.sum(axis=1)
    conteos.index = pd.Index(['Motocicleta y motocarro','Demás usuarios registrados'],name='grupo')
    conteos['origen'] = ['INE 12.2.10 y DINATRAN pp.130/132/133/135: 534 moto + 5 motocarro',
                         'INE 12.2.5 menos subgrupo documentado; incluye peatones y ciclistas']

    demo = pd.read_csv(root / 'output/victimas_individual_limpio.csv')
    ignorada = demo.grupo_edad.eq('Ignorado')
    mayor = demo.grupo_edad.eq('De 60 anos y mas')
    masks = [('Menor de 60, edad conocida', ~ignorada & ~mayor), ('60 años o más', mayor), ('Edad desconocida', ignorada)]
    edad = pd.DataFrame([{'grupo': nombre, 'victimas': int(mask.sum()),
                         'heridos': int(demo.loc[mask, 'es_fallecido'].eq(0).sum()),
                         'fallecidos': int(demo.loc[mask, 'es_fallecido'].sum())} for nombre, mask in masks]).set_index('grupo')
    assert edad.victimas.tolist() == [4832, 308, 353]
    assert demo.loc[ignorada, ['edad_orden', 'es_adulto_mayor']].isna().all().all()
    assert demo.loc[~ignorada, 'edad_orden'].ge(0).all()
    hist = json.loads((root / 'output/fase2/resultados_fase2_consolidados.json').read_text(encoding='utf-8'))
    antecedentes = pd.DataFrame(hist['hipotesis']).set_index('hipótesis')
    integrado = pd.DataFrame([
        ['H1', 'Zona', '12.2.6', 'Tasas y contraste histórico territorial', 'Cobertura y agrupación; no vínculo individual'],
        ['H2', 'Sexo', '12.2.1', 'Asociación histórica y predictor demográfico', 'Señal limitada; no causa ni riesgo individual'],
        ['H3', 'Motocicletas', 'INE 12.2.5/12.2.10 y DINATRAN pp.130–136',
         'Asociación entre víctimas registradas; 539/785 y sensibilidad 534/785',
         '539 incluye 5 de motocarro; resto incluye peatones/ciclistas; sin enlace demográfico ni causalidad'],
        ['H4', 'Edad', '12.2.1', 'Ordinal corregido y contraste de 60 años; predictor nominal', 'Inferencia condicional a frecuencias; 353 desconocidos separados']
    ], columns=['hipotesis', 'factor', 'fuente', 'evidencia', 'limite']).set_index('hipotesis')
    tablas = {'territorio': zonas, 'territorio_h1': h1, 'vehicular_mensual': mensual,
              'vehicular_procedencia': conteos, 'edad_auditoria': edad,
              'antecedentes_historicos': antecedentes, 'hipotesis_integradas': integrado, **tablas_h3}
    auditoria = {'sha256_originales': hashes, 'periodo': 2021, 'meses_verificados': 12,
                 'csv_vehicular_reconstruido': path_anterior.exists(), 'categorias_vehiculares_acreditadas': True,
                 'universo_vehicular_comparable_acreditado': True,
                 'tipo_acreditacion_h3': 'Documental agregada; no enlace de identidades individuales',
                 'fuentes_h3': {k:v for k,v in evidencia_h3.items() if k != 'tablas'},
                 'sha256_referencia_h3': hashlib.sha256((root/'data/referencia_h3_dinatran_2021.json').read_bytes()).hexdigest(),
                 'fuente_pdf': 'https://www.ine.gov.py/Publicaciones/Biblioteca/documento/240/Anuario%20Estadistico%202021.pdf',
                 'paginas_fuente': [307, 311],
                 'fuente_territorial_pdf': 'Patrulla Caminera, MOPC y Policía Nacional (12.2.6)',
                 'nota': 'DINATRAN documenta los roles y permite precisar el grupo histórico; 539 no equivale a 539 usuarios de motocicleta pura.'}
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
        'no riesgo poblacional de accidente ni un efecto causal de residir en una zona. Las 36 celdas mensuales permiten '
        'evaluación binomial cronológica complementaria; no se expanden ni se enlazan con los perfiles demográficos.')
    principal, precisa = tablas_h3['h3_contrastes'].iloc[0], tablas_h3['h3_contrastes'].iloc[1]
    auditoria['interpretacion_h3'] = (
        'La revisión de DINATRAN 2021 pp.130/136, con roles identificados en pp.132/133/135, '
        'fortalece y precisa H3 de Fase 2. El grupo de 539 comprende 332 conductores heridos y 129 fallecidos, '
        '51 acompañantes heridos y 22 fallecidos de motocicleta, más 1 pasajero herido y 4 fallecidos de motocarro. '
        'El total general tiene 1.055 heridos y 269 fallecidos (1.324). Coinciden con INE 12.2.5/12.2.10 '
        'en los doce meses; cada rol del subgrupo es compatible con el general por mes y desenlace. '
        'Los títulos, roles y fuente institucional común respaldan la inclusión documental agregada, '
        'no una identificación individual por registro. INE sitúa la cobertura general en Central e Interior; '
        'no es el universo nacional de 5.493 víctimas. La resta da 671 heridos y 114 fallecidos: '
        'demás usuarios registrados, incluidos peatones y ciclistas, no solo ocupantes de otros vehículos. '
        f'La comparación histórica 155/539 frente a 114/785 arroja RR={principal.RR:.4f}, '
        f'IC 95%={principal.ic95_RR}; OR={principal.OR:.4f}, IC 95%={principal.ic95_OR}. '
        f'El Z unilateral histórico tiene p={principal.p_Z_unilateral:.6g}; '
        f'Fisher unilateral da p={principal.p_Fisher_unilateral:.6g} '
        f'(Bonferroni 6={principal.p_bonferroni_6:.6g}). '
        'La comparación estricta excluye los 5 de motocarro, sin trasladarlos al resto: '
        f'151/534 frente a 114/785 (N=1.319), RR={precisa.RR:.4f}, IC 95%={precisa.ic95_RR}; '
        f'OR={precisa.OR:.4f}, IC 95%={precisa.ic95_OR}; '
        f'p Fisher={precisa.p_Fisher_unilateral:.6g} (Bonferroni 6={precisa.p_bonferroni_6:.6g}). '
        'Las dos comparaciones sostienen mayor fracción de fallecidos dentro de la cobertura registrada, '
        'bajo independencia binomial no verificable por siniestro. No estiman riesgo poblacional, '
        'ocurrencia de accidentes ni un efecto causal ajustado. El motocarro tiene solo 5 víctimas y '
        'no se infiere un efecto separado. No se incorpora vehículo al Modelo A: faltan vínculos '
        'con sexo/edad de la tabla nacional. No se crea Modelo B ni se expanden estos conteos.')
    from src.auditoria_fase3 import complementos_auditados
    tablas.update(complementos_auditados(demo, root) if analisis is None else analisis)
    h4 = tablas['h4_ordinal'].loc['Corregido edad conocida']
    mayor60 = tablas['h4_mayores60'].iloc[0]
    auditoria['interpretacion_edad'] = (
        f"H4 corregida: solo 5.140 víctimas con edad conocida; 353 desconocidos se mantienen en el dataset nacional. "
        f"Mann-Whitney unilateral: U={h4.U:.1f}, p={h4.p:.6g}, r de Rosenthal={h4.r_rosenthal:.4f}; "
        f"r biserial={h4.r_biserial:.4f}, IC 95% bootstrap={h4.ic95_r_biserial}. "
        f"El antecedente conservó -1; se mantiene el ajuste previo de cuatro pruebas para cotejo y se añade el conjunto de seis. "
        f"Comparación separada de 60 o más frente a menores: RR={mayor60.RR:.4f}, "
        f"IC 95%={mayor60.ic95_RR}, p Fisher unilateral={mayor60.p:.6g}. "
        "Los dos indicadores de edad desconocida son NA, no cero ni -1. "
        "Los intervalos asumen muestreo independiente condicionado a las frecuencias; "
        "la fuente no permite verificar conglomeración por siniestro. Edad ordinal no es edad en años; "
        "Mann-Whitney contrasta ordenamiento de distribuciones y no solo medianas.")
    # Los ajustes previos no se sobrescriben. Las seis preguntas interpretadas
    # ahora se presentan juntas; incluye H3 sin motocarro como sensibilidad,
    # sin elegir entre pruebas según su p. El contraste histórico con -1 no
    # constituye una séptima pregunta científica.
    pvalores = [antecedentes.loc['H1','p_valor_crudo'],antecedentes.loc['H2','p_valor_crudo'],
                principal.p_Fisher_unilateral,h4.p,mayor60.p,precisa.p_Fisher_unilateral]
    tablas['multiplicidad_actual'] = pd.DataFrame({
        'contraste':['H1 territorial','H2 sexo','H3 histórica 539/785','H4 ordinal corregida',
                     'H4 adicional ≥60','H3 sensibilidad 534/785'],
        'p_crudo':pvalores,'p_bonferroni_6':[min(1.,6*p) for p in pvalores]})
    tablas['multiplicidad_actual']['rechazo_005'] = tablas['multiplicidad_actual'].p_bonferroni_6.lt(.05)
    auditoria['multiplicidad'] = (
        'Se preservan los p Bonferroni de cuatro pruebas del análisis previo como antecedentes. '
        'El ajuste conjunto conservador de seis incluye H1, H2, H3 histórica, H4 ordinal, ≥60 y H3 sin motocarro. '
        'H3 y H4 mantienen rechazo bajo sus supuestos; H1 pasa a p ajustado 0,069847 y no supera 0,05 '
        'en esta familia ampliada. No se elige el tamaño de familia para conservar significación.')
    auditoria['modelo_territorial'] = (
        '36 celdas mes por zona; GLM binomial por zona con conteos [fallecidos, heridos]. '
        'Base: tasa global estimada solo con meses anteriores. Cortes 1-6/7-8, 1-8/9-10 y 1-10/11-12. '
        'Sin selección por resultados ni predictor de mes; evaluación interna de 2021, sin validación externa. '
        'Los denominadores de validación se usan para puntuar tasas, no para ajustar. '
        'Dependencia por siniestro, cobertura institucional y variación anual no identificables. '
        'No supera consistentemente a la base en log-loss/Brier; se conserva como experimento, sin recomendar su uso predictivo.')
    auditoria['conclusion_integral'] = (
        'H1 aporta diferencias territoriales descriptivas y un contraste histórico de efecto pequeño, condicionado por '
        'agrupación y cobertura. H2 aporta una asociación por sexo y H4 patrones por categorías de edad, incorporadas como '
        'los únicos predictores del experimento demográfico; H4 se recalculó excluyendo desconocidos del contraste. '
        'H3 queda respaldada como asociación agregada por DINATRAN e INE: 539 incluye 5 víctimas de motocarro '
        'y 534 usuarios de motocicleta; la comparación estricta excluye motocarro. '
        'Se responde parcialmente la pregunta original: existe señal demográfica retrospectiva limitada y evidencia '
        'territorial y vehicular separadas; no se estima riesgo poblacional por exposición ni el efecto conjunto de los cuatro factores. '
        'No se predice ocurrencia de siniestros, no se vinculan artificialmente registros y no se afirma causalidad.')
    return tablas, vehicular, auditoria


def calcular_diagnosticos(modelos, ganador, x_train, y_train, x_test, y_test,
                          predicciones, reporte_cv, brechas):
    """Diagnósticos en reserva; sensibilidad y equivalencia ajustadas solo en train.

    predicciones contiene clases y puntajes ya calculados durante la evaluación.
    Devuelve tablas y evidencia; la presentación se decide en el notebook.
    """
    xt, yt = x_test, y_test
    elegido = modelos[ganador]
    tablas = {}
    cms = []
    for nombre, prediccion in predicciones.items():
        tn, fp, fn, tp = confusion_matrix(yt, prediccion['clase'], labels=[0, 1]).ravel()
        cms.append(dict(Modelo=nombre, TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp)))
    tablas['matrices'] = pd.DataFrame(cms).set_index('Modelo')
    errores = xt.copy()
    errores['real'], errores['predicho'] = yt, predicciones[ganador]['clase']
    errores['puntaje'] = predicciones[ganador]['puntaje']
    for k, cond in {'FN': (errores.real == 1) & (errores.predicho == 0),
                    'FP': (errores.real == 0) & (errores.predicho == 1),
                    'TP': (errores.real == 1) & (errores.predicho == 1),
                    'TN': (errores.real == 0) & (errores.predicho == 0)}.items():
        errores[k] = cond.astype(int)
    errores['error'] = (errores.real != errores.predicho).astype(int)
    errores['residuo_absoluto'] = abs(errores.real - errores.puntaje)
    fn = errores.FN.eq(1)
    mujer = errores.sexo.eq('Mujer')
    joven = errores.grupo_edad.isin(['De 0 a 13 anos', 'De 14 a 17 anos', 'De 18 a 29 anos'])
    ignorada = errores.grupo_edad.eq('Ignorado')
    solapamiento = {'FN_total': int(fn.sum()), 'mujeres': int((fn & mujer).sum()),
        'edades_0_29': int((fn & joven).sum()), 'interseccion': int((fn & mujer & joven).sum()),
        'union': int((fn & (mujer | joven)).sum()), 'restantes': int((fn & ~(mujer | joven)).sum())}
    assert solapamiento['union'] == solapamiento['mujeres'] + solapamiento['edades_0_29'] - solapamiento['interseccion']
    desglose = []
    for sexo in ['Hombre', 'Mujer']:
        for tramo, mask in [('0-29 años', joven), ('30 años o más', ~joven & ~ignorada), ('Edad ignorada', ignorada)]:
            desglose.append({'Sexo': sexo, 'Tramo': tramo, 'FN': int((fn & errores.sexo.eq(sexo) & mask).sum())})
    tablas['descomposicion_FN'] = pd.DataFrame(desglose)
    assert tablas['descomposicion_FN'].FN.sum() == fn.sum()
    for nombre, columnas in [('perfil', ['sexo', 'grupo_edad']), ('sexo', ['sexo']), ('edad', ['grupo_edad'])]:
        t = errores.groupby(columnas, observed=True).agg(n=('real', 'size'), fallecidos=('real', 'sum'),
                    FN=('FN', 'sum'), FP=('FP', 'sum'), TP=('TP', 'sum'), TN=('TN', 'sum'),
                    errores=('error', 'sum'), residuo_medio=('residuo_absoluto', 'mean'))
        t['tasa_error'] = t.errores / t.n
        t['recall_fallecidos'] = t.TP / t.fallecidos.replace(0, np.nan)
        t['tasa_FN'] = t.FN / t.fallecidos.replace(0, np.nan)
        tablas[f'errores_{nombre}'] = t
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
    calibracion = []
    for nombre, prediccion in predicciones.items():
        frac, media = calibration_curve(yt, prediccion['puntaje'], n_bins=5, strategy='uniform')
        for x, y in zip(media, frac):
            calibracion.append({'Modelo': nombre, 'puntaje_medio': x, 'fraccion_fallecidos': y})
    tablas['calibracion'] = pd.DataFrame(calibracion)
    comparacion = brechas.copy()
    comparacion['F1-Macro (CV)'] = reporte_cv['F1-Macro (Validación CV)']
    tablas['comparacion_etapas'] = comparacion
    # Mismos hiperparámetros ya fijados; sensibilidad de todos los modelos, sin retuning.
    grupos = x_train.astype(str).agg(' | '.join, axis=1)
    sens = []
    for fold, (tr, va) in enumerate(GroupKFold(4).split(x_train, y_train, grupos), 1):
        assert not set(grupos.iloc[tr]) & set(grupos.iloc[va])
        for nombre, model in modelos.items():
            m = clone(model).fit(x_train.iloc[tr], y_train[tr])
            xv, yv = x_train.iloc[va], y_train[va]
            sens.append({'Modelo': nombre, 'pliegue': fold, 'F1_macro': f1_score(yv, m.predict(xv), average='macro'),
                         'AUC_ROC': roc_auc_score(yv, m.predict_proba(xv)[:, 1]),
                         'n_validacion': len(va), 'perfiles_validacion': grupos.iloc[va].nunique()})
    tablas['sensibilidad_todos'] = pd.DataFrame(sens)
    # Equivalencia exacta de log-verosimilitud expandida frente a frecuencias ponderadas.
    train = x_train.copy()
    train['y'] = y_train
    agregado = train.groupby(['sexo', 'grupo_edad', 'y']).size().rename('frecuencia').reset_index()
    lr = clone(modelos['Regresión Logística'])
    lr.set_params(clf__class_weight=None)
    n = len(train)
    class_n = np.bincount(y_train)
    pesos = agregado.frecuencia.to_numpy() * n / (2 * class_n[agregado.y.to_numpy()])
    lr.fit(agregado[['sexo', 'grupo_edad']], agregado.y, clf__sample_weight=pesos)
    diferencia = float(np.max(abs(lr.predict_proba(xt) - modelos['Regresión Logística'].predict_proba(xt))))
    assert diferencia < .002, diferencia
    equivalencia = {'celdas_train': len(agregado),
        'max_diferencia_puntuacion': diferencia, 'tolerancia_numerica': .002,
        'interpretacion': 'La expansión no aporta información adicional a los conteos.'}
    return tablas, errores, solapamiento, equivalencia


def mostrar_complementos(figuras, tablas, predicciones, y_test, resultados_test):
    """Muestra solo las figuras solicitadas, reutilizando los diagnósticos."""
    yt = y_test
    def mostrar(fig, nombre):
        fig.tight_layout()
        plt.show()
        plt.close(fig)
        interpretaciones = {
            'F3-01': 'Las curvas comparan los mismos 1.099 registros expandidos. AUC y Precision-Recall describen discriminación interna; la línea PR corresponde a la prevalencia de esa reserva. La tabla de métricas permite comprobar las diferencias sin atribuir superioridad externa.',
            'F3-05': 'Dummy no identifica ninguna fatalidad. Cada matriz permite contrastar omisiones y falsas alarmas con denominadores idénticos; 0 = herido y 1 = fallecido. La diagonal contiene aciertos y las otras celdas errores.',
            'F3-02': 'El árbol se elige por CV, aunque otro candidato pueda tener AUC de prueba mayor. La mejora de F1 macro frente a Dummy no implica mejor calibración ni una regla clínica.',
            'F3-06': 'La tasa de error divide por todas las filas del grupo; la tasa FN divide solo por sus fallecidos. En particular, el seleccionado no detecta fatalidades entre mujeres de esta reserva y omite las de varios grupos jóvenes. Una tasa global pequeña puede coexistir con omisión total de la clase minoritaria.',
            'F3-08': 'Gini agrega la reducción de impureza de los indicadores de cada variable. La permutación mide caída de F1 macro al desordenar la columna completa; sus barras muestran variación entre permutaciones. No representan causalidad ni intervalos poblacionales.',
            'F3-09': 'La distancia a la diagonal revela discrepancias entre puntuaciones y frecuencia observada. Brier debe compararse con la base, incluso si el modelo mejora F1. No se ajusta calibración en test y no se informa riesgo individual real.',
            'F3-03': 'Las brechas se cuantifican en las tablas. Su tamaño pequeño está condicionado por perfiles repetidos y por la selección dentro de CV; no acredita generalización externa.'}
        display(Markdown('**Interpretación:** ' + interpretaciones[nombre]))
    for figura in figuras:
        if figura == 'F3-01':
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
            for nombre, prediccion in predicciones.items():
                prob = prediccion['puntaje']
                fpr, tpr, _ = roc_curve(yt, prob)
                pr, re, _ = precision_recall_curve(yt, prob)
                axes[0].plot(fpr, tpr, label=f'{nombre} ({roc_auc_score(yt, prob):.3f})')
                axes[1].step(re, pr, where='post', label=nombre)
            axes[0].plot([0, 1], [0, 1], '--', color='grey')
            axes[0].set(xlabel='Tasa de falsos positivos', ylabel='Recall fallecidos', title='Figura F3-01A. Curvas ROC (misma prueba)')
            axes[1].axhline(np.mean(yt), ls='--', color='grey', label='Prevalencia de prueba')
            axes[1].set(xlabel='Recall fallecidos', ylabel='Precisión fallecidos', title='Figura F3-01B. Curvas Precision-Recall')
            for ax in axes:
                ax.legend(fontsize=7)
            mostrar(fig, 'F3-01')
        elif figura == 'F3-05':
            fig, axes = plt.subplots(2, 3, figsize=(11, 6))
            for ax, nombre in zip(axes.flat, predicciones):
                cm = tablas['matrices'].loc[nombre, ['TN', 'FP', 'FN', 'TP']].to_numpy().reshape(2, 2)
                ax.imshow(cm, cmap='Blues')
                for (i, j), val in np.ndenumerate(cm):
                    ax.text(j, i, str(val), ha='center', va='center', color='white' if val > cm.max() / 2 else 'black')
                ax.set(xticks=[0, 1], yticks=[0, 1], xlabel='Predicho (0 herido; 1 fallecido)', ylabel='Real', title=nombre)
            axes.flat[-1].axis('off')
            fig.suptitle('Figura F3-05. Matrices de confusión en 1.099 filas expandidas')
            mostrar(fig, 'F3-05')
        elif figura == 'F3-02':
            fig, ax = plt.subplots(figsize=(10, 4.5))
            resultados_test[['F1-Macro', 'Recall (Fallecido)', 'ROC-AUC']].plot.bar(ax=ax)
            ax.set(title='Figura F3-02. Comparación de métricas de prueba', ylabel='Puntuación (0 a 1)', xlabel='Modelo', ylim=(0, 1))
            ax.tick_params(axis='x', rotation=12)
            mostrar(fig, 'F3-02')
        elif figura == 'F3-06':
            fig, axes = plt.subplots(1, 2, figsize=(11, 5))
            tablas['errores_edad'][['tasa_error', 'tasa_FN']].rename(columns={'tasa_error': 'Error global', 'tasa_FN': 'Omisión de fallecidos'}).plot.barh(ax=axes[0])
            tablas['errores_sexo'][['tasa_error', 'tasa_FN']].rename(columns={'tasa_error': 'Error global', 'tasa_FN': 'Omisión de fallecidos'}).plot.bar(ax=axes[1], rot=0)
            axes[0].set_ylabel('Grupo de edad')
            for ax in axes:
                ax.set(xlabel='Fracción (0 a 1)' if ax == axes[0] else 'Sexo', xlim=(0, 1) if ax == axes[0] else None)
            axes[0].set_title('F3-06A. Error y omisiones por edad')
            axes[1].set(title='F3-06B. Error y omisiones por sexo', ylabel='Fracción (0 a 1)', ylim=(0, 1))
            mostrar(fig, 'F3-06')
        elif figura == 'F3-08':
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            tablas['gini_variables'].plot.bar(ax=axes[0], rot=10)
            axes[0].set(title='F3-08A. Importancia Gini agregada', ylabel='Reducción de impureza normalizada')
            axes[1].bar(tablas['permutacion'].variable, tablas['permutacion'].media, yerr=tablas['permutacion'].desvio)
            axes[1].set(title='F3-08B. Permutación del seleccionado', ylabel='Caída de F1 macro (media ± desvío)')
            mostrar(fig, 'F3-08')
        elif figura == 'F3-09':
            fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
            axes[0].plot([0, 1], [0, 1], '--', color='grey', label='Calibración ideal')
            for nombre, prediccion in predicciones.items():
                prob = prediccion['puntaje']
                t = tablas['calibracion'].loc[tablas['calibracion'].Modelo.eq(nombre)]
                media, frac = t.puntaje_medio, t.fraccion_fallecidos
                axes[0].plot(media, frac, 'o-', label=nombre)
            axes[0].set(title='F3-09A. Diagnóstico de calibración', xlabel='Puntuación media', ylabel='Fracción observada de fallecidos')
            axes[0].legend(fontsize=7)
            resultados_test[['Brier']].plot.bar(ax=axes[1], legend=False, rot=15)
            axes[1].set(title='F3-09B. Brier (menor es mejor)', ylabel='Error cuadrático de puntuación')
            mostrar(fig, 'F3-09')
        elif figura == 'F3-03':
            fig, ax = plt.subplots(figsize=(10, 4))
            tablas['comparacion_etapas'][['F1-Macro (Train)', 'F1-Macro (CV)', 'F1-Macro (Test)']].plot.bar(ax=ax, rot=12)
            ax.set(title='Figura F3-03. Entrenamiento, validación y prueba', ylabel='F1 macro (0 a 1)', ylim=(0, .8))
            mostrar(fig, 'F3-03')
        else:
            raise ValueError('Figura no reconocida: ' + figura)
