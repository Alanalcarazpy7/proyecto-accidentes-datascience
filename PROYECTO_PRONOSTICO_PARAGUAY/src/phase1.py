"""Exploracion exclusivamente sobre desarrollo: enero 2016-diciembre 2022."""
import numpy as np
import pandas as pd
from scipy import stats

from common import MONTH_NAMES, TYPES, development, plt, save_figure, save_json, save_table


def main():
    df = development()
    y = df['accidentes']
    features = pd.DataFrame({'accidentes': y, 'rezago_1': y.shift(1), 'rezago_12': y.shift(12),
                             'media_previa_3': y.shift(1).rolling(3).mean(),
                             'dias_mes': df['dias_mes']})
    save_table('variables_exploratorias.csv', features.reset_index())
    summary = []
    for name in ['accidentes', 'tasa_diaria_mes']:
        v = df[name]
        summary.append(dict(variable=name, n=len(v), media=v.mean(), mediana=v.median(),
                            moda='; '.join(map(str, v.mode().tolist())), desv_est=v.std(ddof=1),
                            cv=v.std(ddof=1)/v.mean(), minimo=v.min(), maximo=v.max(),
                            iqr=v.quantile(.75)-v.quantile(.25), asimetria=stats.skew(v, bias=False),
                            curtosis_exceso=stats.kurtosis(v, bias=False),
                            **{f'p{q}': v.quantile(q/100) for q in [5, 25, 50, 75, 95]}))
    save_table('descriptivos_desarrollo.csv', pd.DataFrame(summary))
    groups = df.groupby('mes')['accidentes'].agg(['count','mean','median','std','min','max'])
    save_table('resumen_por_mes_desarrollo.csv', groups.reset_index())
    for name, matrix in [('pearson', features.corr(method='pearson')),
                         ('spearman', features.corr(method='spearman'))]:
        save_table(f'correlaciones_{name}.csv', matrix.reset_index())
    contingency = df.groupby('semestre')[TYPES].sum()
    save_table('contingencia_semestre_tipo_absoluta.csv', contingency.reset_index())
    save_table('contingencia_semestre_tipo_por_fila.csv', (contingency.div(contingency.sum(axis=1),axis=0)*100).reset_index())
    save_table('contingencia_semestre_tipo_por_columna.csv', (contingency.div(contingency.sum(axis=0),axis=1)*100).reset_index())
    frequencies = df[TYPES].sum().sort_values(ascending=False).rename('cantidad').to_frame()
    frequencies['porcentaje'] = frequencies['cantidad']/frequencies['cantidad'].sum()*100
    save_table('frecuencias_tipos_desarrollo.csv', frequencies.rename_axis('tipo').reset_index())
    interpretations = {}
    fig, ax = plt.subplots(figsize=(10,3.8))
    ax.plot(y.index,y,label='Observado',color='#21496d')
    ax.plot(y.index,y.rolling(12).mean(),label='Media movil descriptiva de 12 meses',color='#ba7730')
    ax.set(title='Siniestros mensuales en desarrollo (2016-2022)',ylabel='Siniestros por mes',xlabel='Mes calendario')
    ax.legend(fontsize=8); ax.grid(alpha=.2)
    save_figure('f1_01_serie.png',fig)
    interpretations['f1_01_serie.png'] = f'Los conteos van de {int(y.min())} a {int(y.max())} por mes. La media movil describe el historial; no se usa para pronosticar el mismo mes.'
    fig,ax=plt.subplots(figsize=(7,3.6));ax.hist(y,bins=12,color='#38698a',edgecolor='white')
    ax.axvline(y.mean(),color='#b96b25',label=f'Media {y.mean():.1f}');ax.axvline(y.median(),color='#3f7e5a',linestyle='--',label=f'Mediana {y.median():.1f}')
    ax.set(title='Distribucion de 84 cantidades mensuales',xlabel='Siniestros por mes',ylabel='Cantidad de meses');ax.legend(fontsize=8)
    save_figure('f1_02_histograma.png',fig)
    interpretations['f1_02_histograma.png'] = f'La asimetria es {stats.skew(y,bias=False):.2f}. La media resume el nivel, pero mezcla anos con contextos distintos; tambien se informa la mediana.'
    fig,ax=plt.subplots(figsize=(10,3.6));ax.boxplot([df.loc[df.mes==m,'accidentes'] for m in range(1,13)],tick_labels=MONTH_NAMES,patch_artist=True)
    ax.set(title='Variacion por mes del calendario',xlabel='Mes (7 observaciones por grupo)',ylabel='Siniestros por mes');save_figure('f1_03_cajas_mes.png',fig)
    interpretations['f1_03_cajas_mes.png'] = 'Cada caja resume siete anos del mismo mes. La superposicion muestra que el mes del calendario por si solo no determina el conteo.'
    clean=features.dropna();fig,ax=plt.subplots(figsize=(6.5,3.6));ax.scatter(clean.rezago_12,clean.accidentes,c='#38698a',alpha=.8)
    ax.set(title='Cantidad actual y cantidad doce meses antes',xlabel='Siniestros del mismo mes del ano anterior',ylabel='Siniestros del mes actual');save_figure('f1_04_dispersion.png',fig)
    interpretations['f1_04_dispersion.png'] = f'La correlacion de Pearson es {clean.accidentes.corr(clean.rezago_12):.2f}; la de Spearman es {clean.accidentes.corr(clean.rezago_12,method="spearman"):.2f}. No demuestran causalidad ni sustituyen la validacion de pronosticos.'
    annual=df.groupby('ano').accidentes.sum();fig,ax=plt.subplots(figsize=(8,3.6));ax.bar(annual.index.astype(str),annual,color='#38698a')
    ax.set(title='Siniestros registrados por ano de desarrollo',xlabel='Ano',ylabel='Siniestros por ano');save_figure('f1_05_barras_ano.png',fig)
    interpretations['f1_05_barras_ano.png'] = f'El total anual minimo es {int(annual.min())} y el maximo {int(annual.max())}. La variacion requiere considerar cambios reales y posibles cambios en registro o cobertura.'
    corr=features.corr();fig,ax=plt.subplots(figsize=(7,4));im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
    ax.set_xticks(range(len(corr)),corr.columns,rotation=30,ha='right');ax.set_yticks(range(len(corr)),corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',fontsize=9)
    ax.set_title('Correlaciones de variables historicas (Pearson)');fig.colorbar(im,ax=ax,label='Correlacion');save_figure('f1_06_correlaciones.png',fig)
    interpretations['f1_06_correlaciones.png'] = 'Los rezagos y medias anteriores pueden estar correlacionados entre si. Se excluyen los componentes del total del mismo mes para no filtrar la respuesta.'
    pivot=df.pivot(index='ano',columns='mes',values='accidentes');fig,ax=plt.subplots(figsize=(9,3.8));im=ax.imshow(pivot,cmap='Blues',aspect='auto')
    ax.set_xticks(range(12),MONTH_NAMES);ax.set_yticks(range(len(pivot)),pivot.index)
    ax.set(title='Calendario de conteos observados',xlabel='Mes',ylabel='Ano');fig.colorbar(im,ax=ax,label='Siniestros/mes');save_figure('f1_07_calendario.png',fig)
    interpretations['f1_07_calendario.png'] = 'El calendario distingue anos y meses con niveles diferentes. No se rellenan con cero periodos ausentes; los 84 periodos de desarrollo estan publicados.'
    fig,ax=plt.subplots(figsize=(8,3.8));ax.barh(frequencies.index[::-1],frequencies.cantidad.iloc[::-1],color='#38698a')
    ax.set(title='Composicion por tipo de siniestro (2016-2022)',xlabel='Siniestros acumulados',ylabel='Tipo');save_figure('f1_08_tipos.png',fig)
    concentration=frequencies.porcentaje.iloc[:2].sum()
    interpretations['f1_08_tipos.png'] = f'Las dos categorias mas frecuentes concentran {concentration:.1f}% del total. Son 2 de 7 categorias (28,6%), no exactamente el 20%.'
    fig,ax=plt.subplots(figsize=(7,3.6));ax.bar(MONTH_NAMES,groups['mean'],yerr=groups['std'],color='#38698a',capsize=3)
    ax.set(title='Perfil mensual: promedio y dispersion entre anos',xlabel='Mes',ylabel='Media y desvio de siniestros/mes');save_figure('f1_09_perfil.png',fig)
    interpretations['f1_09_perfil.png'] = 'Las barras de error representan dispersion entre anos, no intervalos de confianza ni bandas de pronostico. La estacionalidad se contrasta en la Fase 2.'
    fig,ax=plt.subplots(figsize=(6.5,3.6));ax.scatter(df.dias_mes,df.accidentes,color='#38698a',alpha=.6)
    ax.set(title='Duracion del mes y cantidad de siniestros',xlabel='Dias del mes',ylabel='Siniestros por mes');save_figure('f1_10_exposicion.png',fig)
    interpretations['f1_10_exposicion.png'] = 'Un mes mas largo ofrece mas dias de observacion, pero dias del mes no equivale a kilometros recorridos o volumen de transito. No se estima riesgo por viaje.'
    q1,q3=y.quantile([.25,.75]);outliers=y[(y<q1-1.5*(q3-q1))|(y>q3+1.5*(q3-q1))]
    save_table('atipicos_iqr_conservados.csv',outliers.rename('accidentes').reset_index())
    result=dict(n_desarrollo=len(df), inicio=str(df.index.min().date()), fin=str(df.index.max().date()),
                total=int(y.sum()), media=y.mean(), mediana=y.median(), desviacion=y.std(),
                minimo=dict(fecha=str(y.idxmin().date()),valor=int(y.min())),
                maximo=dict(fecha=str(y.idxmax().date()),valor=int(y.max())),
                atipicos_conservados=len(outliers), concentracion_dos_tipos_pct=concentration,
                interpretaciones=interpretations)
    save_json('fase1_resultados.json',result)
    print('Fase 1 - EDA:',len(df),'meses; 10 graficos; prueba y calibracion fuera de la exploracion.')
    return result


if __name__=='__main__':main()
