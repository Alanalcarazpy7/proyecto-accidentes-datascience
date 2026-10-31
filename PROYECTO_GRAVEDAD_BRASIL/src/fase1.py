"""Exploracion exclusivamente de desarrollo: 2017-2023."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from common import OUT, load_data, save_json, table
from preparar import FEATURES, CAT

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 120, 'savefig.dpi': 160})
COLORS = ['#287c9b', '#d75b47']


def save(name):
    plt.tight_layout()
    plt.savefig(OUT / 'figures' / name, bbox_inches='tight')
    plt.close()


def main():
    d = load_data()
    dev = d[d.ano.le(2023)].copy()
    dev['desenlace'] = dev.fallecido.map({0: 'Herida', 1: 'Fallecida'})
    numeric = ['idade', 'idade_veiculo', 'hora', 'km', 'latitude', 'longitude']
    stats = []
    for c in numeric:
        x = dev[c].dropna()
        stats.append(dict(variable=c, n=len(x), media=x.mean(), mediana=x.median(), moda=x.mode().iloc[0], sd=x.std(), CV=x.std()/abs(x.mean()) if x.mean() else np.nan,
                          minimo=x.min(), maximo=x.max(), IQR=x.quantile(.75)-x.quantile(.25), p5=x.quantile(.05), p25=x.quantile(.25), p50=x.quantile(.5), p75=x.quantile(.75), p95=x.quantile(.95), asimetria=x.skew(), curtosis_exceso=x.kurt()))
    table(pd.DataFrame(stats), 'descriptivos_desarrollo.csv')
    counts, concentration = [], []
    for c in CAT:
        f = dev[c].value_counts()
        for value, n in f.items():
            if n:
                counts.append(dict(variable=c, categoria=value, n=n, proporcion=n/len(dev)))
        nonzero = f[f.gt(0)]
        concentration.append(dict(variable=c, categorias_observadas=len(nonzero), cobertura_20pct_categorias=nonzero.head(max(1, int(np.ceil(.2*len(nonzero))))).sum()/len(dev)))
    table(pd.DataFrame(counts), 'frecuencias_categoricas.csv')
    table(pd.DataFrame(concentration), 'concentracion_categorias.csv')
    for c in ['sexo', 'tipo_veiculo', 'uf', 'tipo_envolvido', 'fase_dia']:
        ct = pd.crosstab(dev[c], dev.fallecido)
        ct.columns = ['Herida', 'Fallecida']
        table(ct.reset_index(), f'contingencia_{c}_absoluta.csv')
        table(ct.div(ct.sum(axis=1), axis=0).reset_index(), f'contingencia_{c}_fila.csv')
        table(ct.div(ct.sum(axis=0), axis=1).reset_index(), f'contingencia_{c}_columna.csv')
    corr_fields = numeric + ['fallecido']
    table(dev[corr_fields].corr(method='pearson').reset_index(names='variable'), 'correlacion_pearson.csv')
    table(dev[corr_fields].corr(method='spearman').reset_index(names='variable'), 'correlacion_spearman.csv')
    table(dev.groupby('desenlace')[numeric].agg(['count', 'mean', 'median', 'std']).reset_index().set_axis(['desenlace']+[f'{a}_{b}' for a,b in dev.groupby('desenlace')[numeric].agg(['count', 'mean', 'median', 'std']).columns], axis=1), 'descriptivos_por_desenlace.csv')
    monthly = dev.groupby(dev.fecha.dt.to_period('M')).agg(victimas=('pesid', 'size'), fallecidos=('fallecido', 'sum'))
    monthly['letalidad'] = monthly.fallecidos / monthly.victimas
    monthly.index = monthly.index.to_timestamp()
    table(monthly.reset_index(), 'serie_mensual_desarrollo.csv')
    texts = {}
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    v = dev.desenlace.value_counts().reindex(['Herida', 'Fallecida'])
    ax.bar(v.index, v.values, color=COLORS)
    for i, n in enumerate(v):ax.text(i, n+len(dev)*.015, f'{n:,}\n{n/len(dev):.2%}', ha='center')
    ax.set(ylabel='Participaciones registradas', title='Desbalance del desenlace en desarrollo (2017-2023)', ylim=(0, max(v)*1.19))
    save('f1_01_clases.png')
    texts['f1_01_clases.png'] = f'En desarrollo hay {int(dev.fallecido.sum()):,} fallecidos entre {len(dev):,} víctimas ({dev.fallecido.mean():.2%}). La clase mayoritaria domina el total de aciertos, por lo que evaluar solo exactitud ocultaría los errores de fallecidos.'
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for value, color in zip([0, 1], COLORS):
        ax.hist(dev.loc[dev.fallecido.eq(value), 'idade'].dropna(), bins=np.arange(0, 116, 5), density=True, alpha=.5, color=color, label=['Herida', 'Fallecida'][value])
    ax.set(xlabel='Edad (años)', ylabel='Densidad', title='Distribución de edad por desenlace; áreas normalizadas')
    ax.legend();save('f1_02_histograma_edad.png')
    medians = dev.groupby('fallecido').idade.median()
    texts['f1_02_histograma_edad.png'] = f'La mediana de edad registrada es {medians[0]:.0f} años en heridos y {medians[1]:.0f} en fallecidos. Se comparan densidades para que la mayor cantidad de heridos no oculte la distribución de fallecidos; edad faltante se conserva en los modelos mediante imputación.'
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.boxplot([dev.loc[dev.fallecido.eq(y), 'idade'].dropna() for y in [0, 1]], tick_labels=['Herida', 'Fallecida'], showfliers=False, patch_artist=True)
    ax.set(ylabel='Edad (años)', title='Edad por desenlace: mediana y rango intercuartílico')
    save('f1_03_cajas_edad.png')
    texts['f1_03_cajas_edad.png'] = 'Las cajas muestran dispersión y superposición de edades. Una diferencia de centros entre grupos no permite clasificar perfectamente individuos; los bigotes no se usan para borrar edades plausibles.'
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 5.5), sharex=True)
    axes[0].plot(monthly.index, monthly.victimas, color=COLORS[0], label='Víctimas elegibles')
    axes[0].plot(monthly.index, monthly.victimas.rolling(12).mean(), color='#273c53', label='Media móvil 12 meses')
    axes[0].set(ylabel='Víctimas / mes', title='Evolución mensual en los siete años de desarrollo');axes[0].legend(fontsize=8)
    axes[1].plot(monthly.index, monthly.letalidad*100, color=COLORS[1]);axes[1].set(ylabel='Fallecidos / víctimas (%)', xlabel='Fecha del siniestro')
    save('f1_04_serie_temporal.png')
    texts['f1_04_serie_temporal.png'] = 'El volumen y la proporción de fallecimientos no permanecen idénticos todos los años. La serie corresponde a víctimas heridas o fallecidas registradas, sin medir exposición al tránsito; cambios de movilidad y registro pueden afectar las diferencias. Se respeta el orden temporal al validar.'
    rates = dev.groupby('tipo_veiculo', observed=True).agg(n=('pesid', 'size'), tasa=('fallecido', 'mean'))
    rates = rates[rates.n.ge(1000)].sort_values('tasa')
    fig, ax = plt.subplots(figsize=(8.2, 5))
    ax.barh(rates.index, rates.tasa*100, color=COLORS[0]);ax.set(xlabel='Fallecidos / víctimas del grupo (%)', title='Letalidad registrada por tipo de vehículo asociado (n ≥ 1.000)')
    save('f1_05_vehiculos.png')
    texts['f1_05_vehiculos.png'] = 'Los tipos de vehículo muestran proporciones diferentes, calculadas con las víctimas de cada grupo como denominador. No representan riesgo por viaje ni una comparación causal; peatones y vehículo desconocido requieren interpretar el rol de participación.'
    sample = dev.dropna(subset=['idade', 'idade_veiculo']).groupby('fallecido').sample(n=3000, random_state=42)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for value, color in zip([0, 1], COLORS):
        z=sample[sample.fallecido.eq(value)]
        ax.scatter(z.idade, z.idade_veiculo, s=7, alpha=.18, color=color, label=['Herida', 'Fallecida'][value])
    ax.set(xlabel='Edad de la víctima (años)', ylabel='Antigüedad del vehículo (años)', title='Edad y antigüedad del vehículo: muestra solo para visualizar')
    ax.legend();save('f1_06_dispersion.png')
    texts['f1_06_dispersion.png'] = 'Se muestran 3.000 casos por clase únicamente para que ambas sean visibles. Este balance visual no modifica el entrenamiento ni la prueba. La superposición indica que dos características aisladas no separan completamente los desenlaces.'
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    sns.heatmap(dev[corr_fields].corr(), annot=True, fmt='.2f', cmap='vlag', center=0, ax=ax, vmin=-1, vmax=1)
    ax.set_title('Correlaciones de Pearson: variables numéricas en desarrollo')
    save('f1_07_correlaciones.png')
    texts['f1_07_correlaciones.png'] = 'La correlación lineal resume solo una parte de la relación. Latitud y longitud describen localización, y la variable binaria de desenlace permite una lectura descriptiva, sin demostrar causalidad ni sustituir la evaluación predictiva.'
    timing = dev.assign(hora_entera=dev.hora.fillna(-1).astype(int)).query('hora_entera >= 0').groupby(['dia_semana', 'hora_entera'], observed=True).fallecido.agg(['mean', 'size'])
    heat = timing['mean'].where(timing['size'].ge(30)).unstack()*100
    heat.index = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    fig, ax = plt.subplots(figsize=(9, 3.5));sns.heatmap(heat, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Fallecidos / víctimas (%)'})
    ax.set(xlabel='Hora del día', ylabel='Día de semana', title='Letalidad por día y hora; celdas con al menos 30 víctimas')
    save('f1_08_dia_hora.png')
    texts['f1_08_dia_hora.png'] = 'El patrón horario justifica estudiar nocturnidad, con diferencias de exposición y tipo de siniestro como posibles confusores. Las celdas contienen víctimas, no conteos independientes de accidentes; un mapa más intenso no mide riesgo por kilómetro recorrido.'
    missing = pd.Series({c:float((dev[c].isna() | dev[c].astype(str).eq('DESCONOCIDO')).mean()) for c in FEATURES})
    missing = missing[missing.gt(0)].sort_values()
    fig, ax = plt.subplots(figsize=(7.5, 4));ax.barh(missing.index, missing*100, color='#96734d')
    ax.set(xlabel='Valores faltantes o desconocidos (%)', title='Información ausente después de aplicar reglas de calidad')
    save('f1_09_faltantes.png')
    texts['f1_09_faltantes.png'] = 'Las ausencias pueden relacionarse con el tipo de víctima y la calidad del registro; no se supone que falten completamente al azar. Se conservan filas y categorías desconocidas, con imputación numérica aprendida exclusivamente dentro de cada entrenamiento.'
    save_json(dict(n_desarrollo=len(dev), fallecidos=int(dev.fallecido.sum()), interpretaciones=texts,
                   hipotesis=['H1 sexo y desenlace', 'H2 edad y desenlace', 'H3 usuarios de moto y letalidad', 'H4 nocturnidad ajustada'],
                   limitacion='Análisis condicionado a víctimas lesionadas registradas por PRF; sin exposición vial ni seguimiento de mortalidad posterior'), OUT / 'fase1_resultados.json')
    return texts


if __name__ == '__main__':
    main()
