"""Cuatro contrastes declarados; tres familias clasicas y regresion agrupada.

Las pruebas clasicas usan una victima elegida al azar por accidente para no
suponer independencia entre pasajeros del mismo evento. Su estimando se
explicita; no se confunde con la tasa ponderada por todas las victimas.
"""
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest
from common import OUT, SEED, load_data, save_json, table, log


def main():
    d = load_data(); dev = d[d.ano.le(2023)].copy()
    # Orden aleatorio sin mirar el desenlace y una participacion por accidente.
    rng = np.random.default_rng(SEED)
    one = dev.iloc[rng.permutation(len(dev))].drop_duplicates('id').copy()
    assert one.id.is_unique
    hypotheses, checks = [], []
    sex = one[one.sexo.isin(['MASCULINO', 'FEMININO'])]
    ct = pd.crosstab(sex.sexo, sex.fallecido)
    chi, p, df, exp = stats.chi2_contingency(ct, correction=False)
    effect = float(np.sqrt(chi / ct.to_numpy().sum()))
    boot_cells = rng.multinomial(int(ct.to_numpy().sum()), ct.to_numpy().ravel()/ct.to_numpy().sum(), size=5000).reshape(-1, 2, 2)
    boot_exp = boot_cells.sum(axis=2)[:, :, None]*boot_cells.sum(axis=1)[:, None, :]/boot_cells.sum(axis=(1, 2))[:, None, None]
    boot_v = np.sqrt((((boot_cells-boot_exp)**2/boot_exp).sum(axis=(1, 2)))/ct.to_numpy().sum())
    v_ci = np.quantile(boot_v, [.025, .975])
    checks.append(dict(contraste='H1', supuesto='Una victima por accidente; frecuencias esperadas >=5', resultado=f'min esperado {exp.min():.1f}; sin IDs duplicados', decision='Chi cuadrado; no requiere normalidad'))
    hypotheses.append(dict(id='H1', H0='Sexo y desenlace son independientes en una victima aleatoria por accidente', H1='Existe asociacion entre sexo y desenlace', prueba='Chi cuadrado independencia', n=len(sex), estadistico=float(chi), gl=float(df), p=float(p), efecto='V de Cramer', valor_efecto=effect, IC95_bajo=float(v_ci[0]), IC95_alto=float(v_ci[1]), alcance='Una victima aleatoria por accidente; sexo conocido; IC bootstrap multinomial'))
    age = one.dropna(subset=['idade'])
    dead = age.loc[age.fallecido.eq(1), 'idade'].to_numpy()
    injured = age.loc[age.fallecido.eq(0), 'idade'].to_numpy()
    sh1 = stats.shapiro(rng.choice(dead, min(5000, len(dead)), replace=False))
    sh0 = stats.shapiro(rng.choice(injured, min(5000, len(injured)), replace=False))
    lev = stats.levene(dead, injured, center='median')
    u = stats.mannwhitneyu(dead, injured, alternative='two-sided', method='asymptotic')
    rrb = 2*u.statistic/(len(dead)*len(injured))-1
    levels = np.unique(np.concatenate([dead, injured]))
    a_counts = np.array([(dead == x).sum() for x in levels])
    b_counts = np.array([(injured == x).sum() for x in levels])
    boot_a = rng.multinomial(len(dead), a_counts/len(dead), size=5000)
    boot_b = rng.multinomial(len(injured), b_counts/len(injured), size=5000)
    boot_u = (boot_a * (np.cumsum(boot_b, axis=1)-.5*boot_b)).sum(axis=1)
    rank_ci = np.quantile(2*boot_u/(len(dead)*len(injured))-1, [.025, .975])
    checks.append(dict(contraste='H2', supuesto='Distribucion de edades, normalidad, dispersion e independencia por accidente', resultado=f'Shapiro submuestras: p fallecidos={sh1.pvalue:.3g}, heridos={sh0.pvalue:.3g}; Levene p={lev.pvalue:.3g}', decision='Mann-Whitney compara distribuciones/rangos, no solo medianas; no exige varianzas iguales'))
    hypotheses.append(dict(id='H2', H0='Distribuciones de edad iguales entre fallecidos y heridos', H1='Las distribuciones de edad difieren', prueba='Mann-Whitney bilateral, correccion de empates', n=len(age), estadistico=float(u.statistic), gl=None, p=float(u.pvalue), efecto='Correlacion biserial de rangos', valor_efecto=float(rrb), IC95_bajo=float(rank_ci[0]), IC95_alto=float(rank_ci[1]), alcance='Una victima por accidente con edad 1..110; IC bootstrap estratificado por desenlace'))
    users = one[one.tipo_envolvido.isin(['CONDUTOR', 'PASSAGEIRO']) & one.tipo_veiculo.ne('DESCONOCIDO')].copy()
    users['moto'] = users.tipo_veiculo.isin(['MOTOCICLETA', 'MOTONETA', 'CICLOMOTOR'])
    n1, n0 = int(users.moto.sum()), int((~users.moto).sum())
    k1, k0 = int(users.loc[users.moto, 'fallecido'].sum()), int(users.loc[~users.moto, 'fallecido'].sum())
    p1, p0 = k1/n1, k0/n0
    z, p = proportions_ztest([k1, k0], [n1, n0], alternative='two-sided')
    rd = p1-p0
    se = np.sqrt(p1*(1-p1)/n1+p0*(1-p0)/n0)
    classic = [float(rd-1.96*se), float(rd+1.96*se)]
    # Bootstrap no parametrico exacto para la distribucion empirica Bernoulli,
    # estratificado por grupo. Una observacion por accidente en esta muestra.
    bootstrap = rng.binomial(n1, p1, size=5000)/n1-rng.binomial(n0, p0, size=5000)/n0
    ci = np.quantile(bootstrap, [.025, .975])
    checks.append(dict(contraste='H3', supuesto='Muestras de accidentes disjuntos; exitos y fracasos >=5', resultado=f'moto muertos/vivos={k1}/{n1-k1}; otros={k0}/{n0-k0}', decision='Prueba z dos proporciones; bootstrap de Bernoulli empiricas como contraste de IC'))
    hypotheses.append(dict(id='H3', H0='Proporcion de fallecimiento igual en usuarios de moto y otros vehiculos', H1='Las proporciones difieren', prueba='Z bilateral de dos proporciones', n=len(users), estadistico=float(z), gl=None, p=float(p), efecto='Diferencia de riesgos moto menos otros', valor_efecto=float(rd), IC95_bajo=float(ci[0]), IC95_alto=float(ci[1]), alcance='Una victima por accidente; conductores/pasajeros con vehiculo conocido'))
    # Regresion sobre todas las victimas elegibles con datos de covariables conocidos.
    g = dev[dev.idade.notna() & dev.sexo.isin(['MASCULINO', 'FEMININO']) & dev.uso_solo.isin(['SIM', 'NAO']) & dev.fase_dia.isin(['PLENA NOITE', 'PLENO DIA']) & dev.tipo_envolvido.ne('DESCONOCIDO') & (dev.tipo_veiculo.ne('DESCONOCIDO') | dev.tipo_envolvido.eq('PEDESTRE'))].copy()
    X = pd.DataFrame({'intercepto': 1.0, 'noche': g.fase_dia.eq('PLENA NOITE').astype(float),
                      'edad_por_10': g.idade/10, 'edad_por_10_cuadrado': (g.idade/10)**2,
                      'masculino': g.sexo.eq('MASCULINO').astype(float),
                      'usuario_moto': (g.tipo_veiculo.isin(['MOTOCICLETA', 'MOTONETA', 'CICLOMOTOR']) & g.tipo_envolvido.isin(['CONDUTOR', 'PASSAGEIRO'])).astype(float),
                      'peaton': g.tipo_envolvido.eq('PEDESTRE').astype(float), 'rural': g.uso_solo.eq('NAO').astype(float),
                      'anio_desde_2017': g.ano.astype(float)-2017}, index=g.index).astype(float)
    fit = sm.GLM(g.fallecido.astype(float), X, family=sm.families.Binomial()).fit(cov_type='cluster', cov_kwds={'groups': g.id})
    ci_log = fit.conf_int()
    coefs = pd.DataFrame({'variable': X.columns, 'beta': fit.params.values, 'SE_cluster_accidente': fit.bse.values, 'p': fit.pvalues.values,
                          'OR': np.exp(fit.params.values), 'OR_IC95_bajo': np.exp(ci_log[0].values), 'OR_IC95_alto': np.exp(ci_log[1].values)})
    table(coefs, 'regresion_logistica_inferencial.csv')
    coef = coefs.set_index('variable').loc['noche']
    hypotheses.append(dict(id='H4', H0='Coeficiente de noche igual a cero condicionado a los controles', H1='Coeficiente de noche distinto de cero', prueba='Wald z de GLM binomial; SE agrupados por accidente', n=len(g), estadistico=float(fit.tvalues['noche']), gl=None, p=float(coef['p']), efecto='Odds ratio ajustado noche frente a pleno dia', valor_efecto=float(coef.OR), IC95_bajo=float(coef.OR_IC95_bajo), IC95_alto=float(coef.OR_IC95_alto), alcance='Todas las victimas de desarrollo con covariables completas; dependencia dentro de accidente ajustada'))
    checks.append(dict(contraste='H4', supuesto='Convergencia; dependencia intraccidente; forma funcional y confusores', resultado=f'convergio={fit.converged}; accidentes={g.id.nunique()}; rango X={np.linalg.matrix_rank(X.to_numpy())}/{X.shape[1]}', decision='Sandwich por accidente; edad cuadratica; no garantiza ausencia de confusion, independencia temporal o seleccion ignorable'))
    reject, adjusted, _, _ = multipletests([h['p'] for h in hypotheses], alpha=.05, method='holm')
    for h, padj, rej in zip(hypotheses, adjusted, reject):
        h['p_Holm'] = float(padj)
        h['decision'] = 'Rechazar H0' if rej else 'No rechazar H0'
    table(pd.DataFrame(hypotheses), 'contrastes_fase2.csv')
    table(pd.DataFrame(checks), 'supuestos_fase2.csv')
    table(pd.DataFrame({'replica': np.arange(len(bootstrap)), 'diferencia_riesgos': bootstrap}), 'bootstrap_diferencia_moto.csv')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    stats.probplot(rng.choice(dead, min(2000, len(dead)), replace=False), plot=axes[0]);axes[0].set_title('Q-Q edad de fallecidos')
    stats.probplot(rng.choice(injured, min(2000, len(injured)), replace=False), plot=axes[1]);axes[1].set_title('Q-Q edad de heridos')
    fig.tight_layout();fig.savefig(OUT/'figures/f2_01_normalidad.png',dpi=160);plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 3.5));ax.hist(bootstrap*100, bins=40, color='#287c9b', alpha=.8)
    for value in ci:ax.axvline(value*100,color='#d75b47',linestyle='--')
    ax.set(xlabel='Diferencia de letalidad: moto menos otros (puntos porcentuales)',ylabel='Réplicas',title='Bootstrap de una víctima por accidente: diferencia condicionada')
    fig.tight_layout();fig.savefig(OUT/'figures/f2_02_bootstrap.png',dpi=160);plt.close(fig)
    result = dict(n_desarrollo=len(dev), n_muestra_una_victima_por_accidente=len(one), estimando_clasico='Caracteristicas de una victima aleatoria por accidente con al menos una victima herida/fallecida; accidentes ponderados por igual. No misma ponderacion que todas las victimas.', contrastes=hypotheses,
                  bootstrap=dict(efecto=rd, IC95_bootstrap=[float(x) for x in ci], IC95_clasico=classic, razon_riesgos=p1/p0, proporcion_moto=p1, proporcion_otros=p0, replicas=5000),
                  GLM=dict(n=len(g), accidentes=int(g.id.nunique()), convergio=bool(fit.converged), nota='No es el modelo predictivo final; complete case puede introducir seleccion; observaciones externas al mismo accidente pueden seguir dependientes'),
                  limites='Registros administrativos, sin muestreo probabilistico ni exposicion vial; p e IC describen incertidumbre bajo supuestos, no corrigen subregistro o sesgo de seleccion. Holm sobre cuatro contrastes; IC95 marginales, no simultaneos. No causalidad. No se seleccionan predictores solo por significancia.')
    save_json(result, OUT / 'fase2_resultados.json')
    log('Fase 2 terminada: cuatro contrastes con Holm, bootstrap y agrupacion por accidente')
    return result


if __name__ == '__main__':
    main()
