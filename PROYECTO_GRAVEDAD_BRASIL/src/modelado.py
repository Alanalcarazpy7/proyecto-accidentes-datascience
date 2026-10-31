"""Busqueda temporal, calibracion, congelamiento y prueba final separada.

No se decide ni se cambia nada a partir de las metricas de 2025.
"""
import gc
import hashlib
import json
import time
import warnings
from functools import partial
import joblib
import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler, KBinsDiscretizer, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import CategoricalNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (average_precision_score, roc_auc_score, precision_score, recall_score,
                            f1_score, balanced_accuracy_score, accuracy_score, brier_score_loss,
                            log_loss, confusion_matrix, precision_recall_curve)
from lightgbm import LGBMClassifier
from common import ROOT, OUT, PROTOCOL, SEED, load_data, save_json, table, log
from preparar import NUM, CAT, FEATURES


def plus_one(x):
    return x + 1


def specs():
    return [
        dict(nombre='Logistica_natural_C1', familia='Logistica', tipo='lr', C=1.0, peso=None),
        dict(nombre='Logistica_balanceada_C1', familia='Logistica', tipo='lr', C=1.0, peso='balanced'),
        dict(nombre='Logistica_balanceada_C01', familia='Logistica', tipo='lr', C=0.1, peso='balanced'),
        dict(nombre='Bayes_alpha1', familia='Bayes', tipo='nb', alpha=1.0),
        dict(nombre='Bayes_alpha10', familia='Bayes', tipo='nb', alpha=10.0),
        dict(nombre='Arbol_profundidad6', familia='Arbol', tipo='tree', profundidad=6),
        dict(nombre='Arbol_profundidad10', familia='Arbol', tipo='tree', profundidad=10),
        *[dict(nombre=f'LightGBM_hojas{leaves}_peso{weight}', familia='LightGBM', tipo='lgbm', hojas=leaves, peso=weight)
          for leaves in [15, 31] for weight in ['natural', 'raiz']],
        dict(nombre='Logistica_solo_sexo_edad', familia='Logistica_sexo_edad', tipo='lr', C=1.0, peso=None, reducida=True),
        dict(nombre='LightGBM_solo_sexo_edad', familia='LightGBM_sexo_edad', tipo='lgbm', hojas=15, peso='natural', reducida=True),
    ]


def feature_list(spec):
    return ['idade', 'sexo'] if spec.get('reducida') else FEATURES


def make_model(spec, y):
    reduced = spec.get('reducida', False)
    num, cat = (['idade'], ['sexo']) if reduced else (NUM, CAT)
    if spec['tipo'] == 'lgbm':
        pre = ColumnTransformer([
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1, dtype=np.float32), cat),
            ('num', 'passthrough', num),
        ])
        ratio = float((y == 0).sum() / (y == 1).sum())
        model = LGBMClassifier(n_estimators=240, learning_rate=0.06, num_leaves=spec['hojas'],
                               min_child_samples=120, reg_lambda=8, colsample_bytree=0.9,
                               scale_pos_weight=1 if spec['peso'] == 'natural' else np.sqrt(ratio),
                               random_state=SEED, n_jobs=6, verbosity=-1, deterministic=True,
                               force_col_wise=True)
        return Pipeline([('prep', pre), ('modelo', model)])
    if spec['tipo'] == 'nb':
        # Cada variable numerica se convierte en seis intervalos aprendidos solo en train.
        # Las categorias futuras se codifican como 0 y las conocidas a partir de 1.
        pre = ColumnTransformer([
            ('num', Pipeline([('imputar', SimpleImputer(strategy='median')),
                              ('bins', KBinsDiscretizer(n_bins=6, encode='ordinal', strategy='quantile', subsample=200000, random_state=SEED, quantile_method='averaged_inverted_cdf'))]), num),
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), cat),
        ])
        return Pipeline([('prep', pre), ('positivos', FunctionTransformer(partial(np.add, 1))),
                         ('modelo', CategoricalNB(alpha=spec['alpha']))])
    pre = ColumnTransformer([
        ('num', Pipeline([('imputar', SimpleImputer(strategy='median', add_indicator=True)), ('escalar', StandardScaler())]), num),
        ('cat', OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=100, dtype=np.float32), cat),
    ], sparse_threshold=1.0)
    if spec['tipo'] == 'lr':
        model = LogisticRegression(C=spec['C'], class_weight=spec['peso'], solver='lbfgs', max_iter=400, random_state=SEED)
    else:
        model = DecisionTreeClassifier(max_depth=spec['profundidad'], min_samples_leaf=200, class_weight='balanced', random_state=SEED)
    return Pipeline([('prep', pre), ('modelo', model)])


def fit_model(model, spec, X, y):
    if spec['tipo'] == 'lgbm':
        categorical = list(range(1 if spec.get('reducida') else len(CAT)))
        model.fit(X, y, modelo__categorical_feature=categorical)
        assert model['modelo'].booster_.params.get('categorical_column') == categorical
    else:
        model.fit(X, y)
    return model


def metrics(y, p, threshold):
    pred = np.asarray(p) >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(n=len(y), fallecidos=int(np.sum(y)), prevalencia=float(np.mean(y)), umbral=float(threshold),
                AP=average_precision_score(y, p), ROC_AUC=roc_auc_score(y, p),
                precision=precision_score(y, pred, zero_division=0), recall=recall_score(y, pred),
                F1_fallecido=f1_score(y, pred), F1_macro=f1_score(y, pred, average='macro'),
                balanced_accuracy=balanced_accuracy_score(y, pred), accuracy=accuracy_score(y, pred),
                Brier=brier_score_loss(y, p), log_loss=log_loss(y, np.clip(p, 1e-7, 1-1e-7)),
                TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp))


def thresholds(y, p):
    prec, rec, t = precision_recall_curve(y, p)
    f1 = 2 * prec[:-1] * rec[:-1] / np.maximum(prec[:-1] + rec[:-1], 1e-15)
    best = np.flatnonzero(np.isclose(f1, np.max(f1), atol=1e-12, rtol=0))[-1]
    acceptable = np.flatnonzero(rec[:-1] >= 0.8)
    return {'F1_fallecido': float(t[best]), 'recall80': float(t[acceptable[-1]])}


def calibrate(raw, y):
    model = LogisticRegression(C=1e6, solver='lbfgs', max_iter=200, random_state=SEED)
    model.fit(logit(np.clip(raw, 1e-7, 1-1e-7)).reshape(-1, 1), y)
    assert model.coef_[0, 0] > 0, 'Calibracion invertida: requiere diagnostico, no tocar prueba'
    return model


def probabilities(bundle, X, calibrated=True):
    raw = bundle['pipeline'].predict_proba(X[bundle['features']])[:, 1]
    if calibrated and bundle.get('calibrador') is not None:
        return bundle['calibrador'].predict_proba(logit(np.clip(raw, 1e-7, 1-1e-7)).reshape(-1, 1))[:, 1]
    return raw


def fit_and_freeze(force=False):
    freeze_path = OUT / 'seleccion_congelada_antes_prueba.json'
    if freeze_path.exists() and not force:
        return json.loads(freeze_path.read_text(encoding='utf8'))
    d = load_data()
    dev = d[d.ano.le(2023)].copy()
    cal = d[(d.ano.eq(2024)) & d.fecha.lt('2024-07-01')].copy()
    val = d[(d.ano.eq(2024)) & d.fecha.ge('2024-07-01')].copy()
    # Las etiquetas y predicciones de prueba no se consultan en esta funcion.
    del d
    grid = specs()
    save_json(grid, OUT / 'grilla_predefinida.json')
    rows = []
    checkpoint = OUT / 'cv_checkpoint.json'
    if checkpoint.exists() and not force:
        rows = json.loads(checkpoint.read_text(encoding='utf8'))
    completed = {(r['nombre'], r['validar']) for r in rows}
    for spec in grid:
        features = feature_list(spec)
        for fold in PROTOCOL['cv']:
            yr = fold['validar']
            if (spec['nombre'], yr) in completed:
                continue
            tr = dev[dev.ano.le(fold['entrenar_hasta'])]
            va = dev[dev.ano.eq(yr)]
            start = time.perf_counter()
            model = make_model(spec, tr.fallecido)
            fit_model(model, spec, tr[features], tr.fallecido)
            prob = model.predict_proba(va[features])[:, 1]
            result = dict(nombre=spec['nombre'], familia=spec['familia'], entrenar_hasta=fold['entrenar_hasta'], validar=yr,
                          n_train=len(tr), n_val=len(va), segundos=time.perf_counter()-start,
                          **metrics(va.fallecido.to_numpy(), prob, 0.5))
            rows.append(result)
            save_json(rows, checkpoint)
            table(pd.DataFrame(rows), 'validacion_temporal_todas.csv')
            log(f"CV {spec['nombre']} -> {yr}: AP={result['AP']:.4f}, ROC={result['ROC_AUC']:.4f}, {result['segundos']:.1f}s")
            del model, tr, va
            gc.collect()
    cv = pd.DataFrame(rows)
    ranking = cv.groupby(['nombre', 'familia'], sort=False).agg(AP_media=('AP', 'mean'), AP_sd=('AP', 'std'), ROC_media=('ROC_AUC', 'mean'), F1_macro_05=('F1_macro', 'mean')).reset_index().sort_values('AP_media', ascending=False, kind='stable')
    table(ranking, 'ranking_CV.csv')
    winners = ranking.drop_duplicates('familia').copy()
    full = winners[~winners.familia.str.contains('sexo_edad')]
    selected = full.iloc[0]['nombre']
    best_specs = [next(s for s in grid if s['nombre'] == name) for name in winners.nombre]
    train_rows = []
    frozen = {'protocolo_sha256': hashlib.sha256((ROOT / 'protocolo.json').read_bytes()).hexdigest(),
              'seleccionado': selected, 'criterio': PROTOCOL['seleccion'], 'modelos': [], 'prueba_consultada': False}
    for spec in best_specs + [dict(nombre='Dummy_siempre_herido', familia='Dummy', tipo='dummy')]:
        start = time.perf_counter()
        features = FEATURES if spec['tipo'] == 'dummy' else feature_list(spec)
        if spec['tipo'] == 'dummy':
            model = DummyClassifier(strategy='prior')
            fit_model(model, spec, dev[features], dev.fallecido)
        else:
            model = make_model(spec, dev.fallecido)
            fit_model(model, spec, dev[features], dev.fallecido)
        bundle = dict(pipeline=model, features=features, calibrador=None, spec=spec)
        if spec['tipo'] != 'dummy':
            raw_cal = probabilities(bundle, cal, calibrated=False)
            bundle['calibrador'] = calibrate(raw_cal, cal.fallecido)
            p_val = probabilities(bundle, val)
            bundle['umbrales'] = thresholds(val.fallecido, p_val)
        else:
            p_val = probabilities(bundle, val)
            bundle['umbrales'] = dict(F1_fallecido=0.5, recall80=0.5)
        bundle['umbral'] = bundle['umbrales']['F1_fallecido']
        bundle['protocolo_sha256'] = frozen['protocolo_sha256']
        joblib.dump(bundle, ROOT / 'models' / f"{spec['nombre']}.joblib", compress=3)
        for split_name, frame in [('entrenamiento_2017_2023', dev), ('validacion_umbral_2024_H2', val)]:
            p = probabilities(bundle, frame)
            train_rows.append(dict(modelo=spec['nombre'], familia=spec['familia'], particion=split_name, regla='F1_validacion', **metrics(frame.fallecido.to_numpy(), p, bundle['umbral'])))
        for rule, t in [('umbral_05', 0.5), ('recall80_validacion', bundle['umbrales']['recall80'])]:
            train_rows.append(dict(modelo=spec['nombre'], familia=spec['familia'], particion='validacion_umbral_2024_H2', regla=rule, **metrics(val.fallecido.to_numpy(), p_val, t)))
        frozen['modelos'].append(dict(nombre=spec['nombre'], familia=spec['familia'], parametros=spec, umbral=bundle['umbral'], umbrales=bundle['umbrales'], archivo=f"models/{spec['nombre']}.joblib", segundos_ajuste=time.perf_counter()-start))
        log(f"Ajustado y calibrado {spec['nombre']}, umbral={bundle['umbral']:.4f}")
        del model, bundle
        gc.collect()
    table(pd.DataFrame(train_rows), 'metricas_train_validacion.csv')
    save_json(frozen, freeze_path)
    log(f'SELECCION CONGELADA: {selected}; prueba aun sin evaluar')
    return frozen


def cluster_bootstrap(test, p_main, p_age, threshold):
    from sklearn.utils import check_random_state
    y = test.fallecido.to_numpy()
    codes, groups = pd.factorize(test.id)
    n = len(groups)
    rng = np.random.default_rng(SEED)
    rows = []
    main_pred = p_main >= threshold
    for b in range(400):
        # Remuestreo multinomial de accidentes completos, no de personas aisladas.
        w_group = np.bincount(rng.integers(0, n, size=n), minlength=n)
        w = w_group[codes]
        ap = average_precision_score(y, p_main, sample_weight=w)
        ap_age = average_precision_score(y, p_age, sample_weight=w)
        rows.append(dict(replica=b, AP=ap, mejora_AP_sobre_sexo_edad=ap-ap_age,
                         recall=recall_score(y, main_pred, sample_weight=w),
                         precision=precision_score(y, main_pred, sample_weight=w, zero_division=0),
                         F1_macro=f1_score(y, main_pred, average='macro', sample_weight=w)))
    boot = pd.DataFrame(rows)
    table(boot, 'bootstrap_accidentes_prueba.csv')
    ci = pd.DataFrame([dict(metrica=c, IC95_bajo=float(boot[c].quantile(.025)), IC95_alto=float(boot[c].quantile(.975))) for c in boot if c != 'replica'])
    table(ci, 'intervalos_prueba_bootstrap.csv')
    return ci.to_dict('records')


def evaluate_once():
    result_path = OUT / 'fase3_resultados.json'
    if result_path.exists():
        log('Prueba ya registrada: se leen resultados guardados sin volver a seleccionar ni ajustar.')
        return json.loads(result_path.read_text(encoding='utf8'))
    frozen = json.loads((OUT / 'seleccion_congelada_antes_prueba.json').read_text(encoding='utf8'))
    assert hashlib.sha256((ROOT / 'protocolo.json').read_bytes()).hexdigest() == frozen['protocolo_sha256']
    d = load_data()
    test = d[d.ano.eq(2025)].copy()
    assert set(test.id).isdisjoint(set(d.loc[d.ano.le(2024), 'id']))
    y = test.fallecido.to_numpy()
    predictions = test[['id', 'pesid', 'fecha', 'fallecido', 'sexo', 'idade', 'tipo_envolvido', 'tipo_veiculo', 'uf']].copy()
    rows, probs, score_dtypes = [], {}, {}
    for item in frozen['modelos']:
        bundle = joblib.load(ROOT / item['archivo'])
        p = probabilities(bundle, test)
        score_dtypes[item['nombre']]=str(p.dtype)
        probs[item['nombre']] = p
        predictions[item['nombre']] = p
        for rule, t in [('F1_validacion', item['umbral']), ('umbral_05', 0.5), ('recall80_validacion', item['umbrales']['recall80'])]:
            row = dict(modelo=item['nombre'], familia=item['familia'], particion='prueba_2025', regla=rule, **metrics(y, p, t))
            rows.append(row)
            if rule == 'F1_validacion':
                log(f"PRUEBA {item['nombre']}: AP={row['AP']:.4f}, ROC={row['ROC_AUC']:.4f}, precision={row['precision']:.4f}, recall={row['recall']:.4f}, F1macro={row['F1_macro']:.4f}")
    pred_path = OUT / 'predicciones_prueba_2025.csv.gz'
    predictions.to_csv(pred_path, index=False, compression='gzip')
    save_json(score_dtypes,OUT/'predicciones_dtypes.json')
    table(pd.DataFrame(rows), 'metricas_prueba_2025.csv')
    prev = pd.read_csv(OUT / 'tables/metricas_train_validacion.csv')
    table(pd.concat([prev, pd.DataFrame(rows)], ignore_index=True), 'comparacion_train_validacion_prueba.csv')
    selected = frozen['seleccionado']
    selected_item = next(x for x in frozen['modelos'] if x['nombre'] == selected)
    ci = cluster_bootstrap(test, probs[selected], probs['LightGBM_solo_sexo_edad'], selected_item['umbral'])
    # Desgloses y errores con reglas ya congeladas, sin reajustar modelo o umbral.
    pred = probs[selected] >= selected_item['umbral']
    groups = []
    test['grupo_edad'] = pd.cut(test.idade, [0, 17, 29, 44, 59, 110], labels=['1-17', '18-29', '30-44', '45-59', '60-110']).astype(str)
    for col in ['sexo', 'grupo_edad', 'tipo_envolvido', 'tipo_veiculo', 'uf']:
        for value, indices in test.groupby(col, observed=True).groups.items():
            mask = test.index.isin(indices)
            if mask.sum() < 100 or len(np.unique(y[mask])) < 2:
                continue
            groups.append(dict(variable=col, grupo=str(value), **metrics(y[mask], probs[selected][mask], selected_item['umbral'])))
    table(pd.DataFrame(groups), 'errores_por_grupo.csv')
    mistakes = predictions.loc[pred != y].copy()
    mistakes['tipo_error'] = np.where(mistakes.fallecido.eq(1), 'FN_fallecido_clasificado_herido', 'FP_herido_clasificado_fallecido')
    mistakes['confianza_erronea'] = np.where(mistakes.fallecido.eq(1), 1 - mistakes[selected], mistakes[selected])
    table(mistakes.sort_values('confianza_erronea', ascending=False).head(20), 'errores_mayor_confianza.csv')
    bundle = joblib.load(ROOT / selected_item['archivo'])
    joblib.dump(bundle, ROOT / 'models/modelo_seleccionado.joblib', compress=3)
    # Importancia por permutacion en validacion, no se seleccionan variables con prueba.
    val = d[(d.ano.eq(2024)) & d.fecha.ge('2024-07-01')]
    val = val.sample(min(15000, len(val)), random_state=SEED)
    base = average_precision_score(val.fallecido, probabilities(bundle, val))
    importance = []
    rng = np.random.default_rng(SEED)
    for c in bundle['features']:
        differences = []
        for repeat in range(2):
            perturbed = val.copy()
            perturbed[c] = rng.permutation(perturbed[c].to_numpy())
            differences.append(base-average_precision_score(val.fallecido, probabilities(bundle, perturbed)))
        importance.append(dict(variable=c, caida_AP_media=float(np.mean(differences)), sd=float(np.std(differences)), n=len(val), particion='validacion_2024_H2'))
    table(pd.DataFrame(importance).sort_values('caida_AP_media', ascending=False), 'importancia_permutacion_validacion.csv')
    selected_results = next(x for x in rows if x['modelo'] == selected and x['regla'] == 'F1_validacion')
    result = dict(seleccionado=selected, criterio=frozen['criterio'], prueba=selected_results, intervalos=ci,
                  prueba_sha256=hashlib.sha256(pred_path.read_bytes()).hexdigest(),
                  alcance=PROTOCOL['alcance'], modelo_anterior=dict(F1_macro=.5299, ROC_AUC=.5809, precision=.2324, recall=.4541, accuracy=.6351, n=1099, positivos=196, nota='Informe anterior Paraguay; poblacion, prevalencia y division diferentes, no mejora causal ni equivalente'),
                  advertencia='Umbral elegido para F1 de fallecidos en 2024 H2. Scores calibrados en 2024 H1. CV elige por AP; prueba no se uso para elegir.')
    save_json(result, result_path)
    return result


if __name__ == '__main__':
    fit_and_freeze()
    evaluate_once()
