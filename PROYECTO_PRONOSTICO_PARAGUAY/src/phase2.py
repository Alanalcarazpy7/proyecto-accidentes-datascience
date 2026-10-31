"""Cuatro contrastes predefinidos, familias distintas y cautela temporal.

Los contrastes usan solo 2016-2022. Los IC bootstrap re-muestrean anos o
bloques de residuos, nunca victimas artificiales. No se eligen pruebas por p.
"""
import itertools

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox

from common import PROTOCOL, SEED, development, plt, save_figure, save_json, save_table


def friedman_q(matrix):
    n,k=matrix.shape
    ranks=stats.rankdata(matrix,axis=1)
    tie_sum=0
    for row in matrix:
        _,counts=np.unique(row,return_counts=True)
        tie_sum+=np.sum(counts**3-counts)
    correction=1-tie_sum/(n*k*(k*k-1))
    q=(12/(n*k*(k+1))*np.sum(ranks.sum(axis=0)**2)-3*n*(k+1))/correction
    return q,ranks,correction


def main():
    rng=np.random.default_rng(SEED)
    df=development();y=df.accidentes.astype(float)
    matrix=df.pivot(index='ano',columns='mes',values='accidentes').to_numpy(float)
    n,k=matrix.shape; B=PROTOCOL['bootstrap_replicas']
    rows=[]
    q,ranks,correction=friedman_q(matrix)
    shifts=rng.integers(0,k,size=(PROTOCOL['permutaciones_H1'],n,1))
    ix=(np.arange(k)[None,None,:]+shifts)%k
    perm=np.take_along_axis(np.broadcast_to(ranks,(len(shifts),n,k)),ix,axis=2)
    qp=(12/(n*k*(k+1))*np.sum(perm.sum(axis=1)**2,axis=1)-3*n*(k+1))/correction
    p1=(1+np.sum(qp>=q-1e-10))/(len(qp)+1)
    w=q/(n*(k-1))
    bootw=[]
    for _ in range(B):
        bootw.append(friedman_q(matrix[rng.integers(0,n,size=n)])[0]/(n*(k-1)))
    ciw=np.quantile(bootw,[.025,.975])
    classical=stats.friedmanchisquare(*matrix.T)
    rows.append(dict(id='H1',familia='Comparacion de 12 medidas apareadas',
                     hipotesis='No hay alineacion mensual sistematica entre anos',
                     prueba='Friedman con referencia de desplazamientos circulares por ano',
                     n_bloques=n,estadistico=q,gl=k-1,p=p1,p_clasico=classical.pvalue,
                     efecto=w,nombre_efecto='W de Kendall',ic_bajo=ciw[0],ic_alto=ciw[1],
                     tipo_ic='Bootstrap de anos completos; exploratorio',
                     supuestos='Anos aproximadamente independientes; fase mensual intercambiable bajo H0. Conserva orden circular dentro del ano.'))
    first=matrix[:,:6].mean(axis=1);second=matrix[:,6:].mean(axis=1);delta=second-first
    wil=stats.wilcoxon(delta,alternative='two-sided',method='exact',zero_method='wilcox')
    absrank=stats.rankdata(np.abs(delta));rbc=(absrank[delta>0].sum()-absrank[delta<0].sum())/absrank.sum()
    boot_delta=delta[rng.integers(0,n,size=(B,n))].mean(axis=1)
    ci_delta=np.quantile(boot_delta,[.025,.975]);se=stats.sem(delta)
    ci_t=stats.t.interval(.95,n-1,loc=delta.mean(),scale=se)
    rows.append(dict(id='H2',familia='Comparacion apareada de dos semestres',
                     hipotesis='Centro simetrico de diferencias segundo-primer semestre igual a cero',
                     prueba='Wilcoxon apareado por ano (bilateral, exacto)',n_bloques=n,
                     estadistico=wil.statistic,gl=None,p=wil.pvalue,p_clasico=wil.pvalue,
                     efecto=delta.mean(),nombre_efecto='Diferencia media: siniestros/mes',
                     ic_bajo=ci_delta[0],ic_alto=ci_delta[1],tipo_ic='Bootstrap de pares anuales para diferencia media',
                     supuestos='Pares anuales aproximadamente independientes; diferencias simetricas para interpretar un desplazamiento de localizacion.'))
    annual=matrix.mean(axis=1); years=np.arange(n)
    rho=stats.spearmanr(years,annual).statistic
    rotations=np.array([stats.spearmanr(years,np.roll(annual,s)).statistic for s in range(n)])
    p3=np.mean(np.abs(rotations)>=abs(rho)-1e-12)
    exact=np.array([stats.spearmanr(years,np.asarray(v)).statistic for v in itertools.permutations(annual)])
    p_indep=np.mean(np.abs(exact)>=abs(rho)-1e-12)
    brho=[]
    for _ in range(B):
        ids=rng.integers(0,n,size=n)
        if np.unique(ids).size>1:brho.append(stats.spearmanr(years[ids],annual[ids]).statistic)
    cr=np.quantile(brho,[.025,.975])
    rows.append(dict(id='H3',familia='Asociacion monotona',hipotesis='Rho entre ano y promedio anual igual a cero',
                     prueba='Spearman; referencia circular de la secuencia anual',n_bloques=n,
                     estadistico=rho,gl=None,p=p3,p_clasico=p_indep,
                     efecto=rho,nombre_efecto='Rho de Spearman',ic_bajo=cr[0],ic_alto=cr[1],
                     tipo_ic='Bootstrap de pares anuales; aproximado, depende de independencia entre anos',
                     supuestos='Orden anual preservado en referencia circular; cierre circular y estacionariedad bajo H0 son aproximaciones. Resolucion 1/7.'))
    design=pd.DataFrame({'rezago_1':y.shift(1),'rezago_12':y.shift(12),
                         'tendencia_ano':np.arange(len(y))/12,
                         'sin_mes':np.sin(2*np.pi*df.mes/12),'cos_mes':np.cos(2*np.pi*df.mes/12),
                         'dias_mes':df.dias_mes.astype(float),'indicador_2020':(df.ano==2020).astype(float)},index=df.index)
    mask=design.notna().all(axis=1);X=sm.add_constant(design.loc[mask]).astype(float);target=y.loc[mask]
    ols=sm.OLS(target,X).fit()
    robust=ols.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True)
    idx=X.columns.get_loc('rezago_1');ci4=robust.conf_int()[idx]
    residual=ols.resid.to_numpy();centered=residual-residual.mean();length=len(centered)
    # Remuestreo circular en bloques de doce residuos con diseno fijo.
    starts=rng.integers(0,length,size=(B,int(np.ceil(length/12))))
    indices=((starts[:,:,None]+np.arange(12))%length).reshape(B,-1)[:,:length]
    simulated=ols.fittedvalues.to_numpy()[None,:]+centered[indices]
    betas=simulated@np.linalg.pinv(X.to_numpy()).T
    boot_ci=np.quantile(betas[:,idx],[.025,.975])
    rows.append(dict(id='H4',familia='Regresion multiple robusta',
                     hipotesis='Beta de rezago un mes igual a cero, controlando otras covariables',
                     prueba='t de coeficiente OLS con HAC(12)',n_bloques=len(target),
                     estadistico=robust.tvalues[idx],gl=robust.df_resid,p=robust.pvalues[idx],
                     p_clasico=ols.pvalues.iloc[idx],efecto=robust.params[idx],
                     nombre_efecto='Cambio condicional por un siniestro previo',ic_bajo=ci4[0],ic_alto=ci4[1],
                     tipo_ic='IC 95% HAC con t; no causal',
                     supuestos='Especificacion lineal y estabilidad aproximadas; HAC corrige covarianza, no confusores ni errores de registro.'))
    results=pd.DataFrame(rows)
    results['p_bonferroni']=np.minimum(results.p*4,1)
    results['decision']=np.where(results.p_bonferroni<PROTOCOL['alpha'],'Rechazar H0','No rechazar H0')
    save_table('contrastes_fase2.csv',results)
    assumptions=[]
    for label,values in [('Conteos mensuales',y),('Diferencias de semestres por ano',delta),('Residuos OLS',residual)]:
        sw=stats.shapiro(values)
        assumptions.append(dict(prueba='Shapiro-Wilk',variable=label,estadistico=sw.statistic,p=sw.pvalue,
                                interpretacion='Diagnostico; n pequeno no prueba normalidad. No activa busquedas de pruebas por significancia.'))
    lev=stats.levene(first,second,center='median')
    assumptions.append(dict(prueba='Levene (mediana)',variable='Promedios de semestres',estadistico=lev.statistic,p=lev.pvalue,
                            interpretacion='Diagnostico descriptivo; igualdad de varianzas NO es requisito de Wilcoxon apareado.'))
    lb=acorr_ljungbox(residual,lags=[1,6,12],return_df=True)
    for lag,row in lb.iterrows():assumptions.append(dict(prueba=f'Ljung-Box({lag})',variable='Residuos OLS',estadistico=row.lb_stat,p=row.lb_pvalue,
                                                       interpretacion='Diagnostico de dependencia residual; no es una quinta hipotesis primaria.'))
    save_table('supuestos_fase2.csv',pd.DataFrame(assumptions))
    coefficient_table=pd.DataFrame(dict(variable=X.columns,coeficiente=robust.params,error_estandar_HAC=robust.bse,
                                         t=robust.tvalues,p_sin_ajuste=robust.pvalues,
                                         ic95_inferior=robust.conf_int()[:,0],ic95_superior=robust.conf_int()[:,1]))
    save_table('regresion_inferencial_HAC.csv',coefficient_table)
    sensitivity=[]
    for lag in [6,12]:
        rr=ols.get_robustcov_results(cov_type='HAC',maxlags=lag,use_correction=True,use_t=True)
        sensitivity.append(dict(rezagos_HAC=lag,beta=rr.params[idx],p=rr.pvalues[idx],ic_bajo=rr.conf_int()[idx,0],ic_alto=rr.conf_int()[idx,1]))
    save_table('sensibilidad_HAC.csv',pd.DataFrame(sensitivity))
    save_table('diferencias_pareadas_semestres.csv',pd.DataFrame(dict(ano=df.ano.unique(),primero=first,segundo=second,diferencia=delta)))
    fig,axes=plt.subplots(1,2,figsize=(10,3.5));sm.qqplot(y,line='s',ax=axes[0]);sm.qqplot(residual,line='s',ax=axes[1]);axes[0].set_title('Q-Q de conteos de desarrollo');axes[1].set_title('Q-Q de residuos inferenciales')
    save_figure('f2_01_supuestos_qq.png',fig)
    fig,ax=plt.subplots(figsize=(8,3.4));ax.bar(df.ano.unique().astype(str),delta,color=np.where(delta>=0,'#38698a','#ba7730'))
    ax.axhline(0,color='black',linewidth=.8);ax.set(title='Diferencia segundo menos primer semestre, por ano',xlabel='Ano',ylabel='Diferencia de medias (siniestros/mes)');save_figure('f2_02_semestres.png',fig)
    fig,ax=plt.subplots(figsize=(7,3.4));ax.hist(boot_delta,bins=30,color='#38698a');ax.axvline(delta.mean(),color='#ba7730');ax.set(title='Bootstrap de diferencias medias por pares anuales',xlabel='Diferencia (siniestros/mes)',ylabel='Replicas');save_figure('f2_03_bootstrap.png',fig)
    fig,ax=plt.subplots(figsize=(8,3.4));ax.plot(target.index,residual,color='#38698a');ax.axhline(0,color='black',linewidth=.8)
    ax.set(title='Residuos del modelo inferencial (desarrollo)',xlabel='Mes',ylabel='Residuo (siniestros/mes)');save_figure('f2_04_residuos.png',fig)
    summary=dict(n_desarrollo=len(y),n_anos=n,alpha=PROTOCOL['alpha'],familias=4,
                 contrastes=results.to_dict('records'),supuestos=assumptions,
                 comparacion_ic_media_semestres=dict(estimacion=delta.mean(),bootstrap=ci_delta,clasico_t=ci_t,
                                                     nota='Ambos IC estiman la diferencia media; Wilcoxon contrasta un centro de diferencias bajo simetria.'),
                 regresion=dict(n=len(target),r2=ols.rsquared,r2_ajustado=ols.rsquared_adj,
                                coef_rezago1=robust.params[idx],ic_HAC=ci4,ic_OLS=ols.conf_int().iloc[idx].tolist(),
                                ic_bootstrap_bloques=boot_ci,coeficientes=coefficient_table.to_dict('records')),
                 limites=['Siete anos son pocos bloques: no rechazar no demuestra ausencia de efecto.',
                          'La independencia entre anos no puede garantizarse; las bandas bootstrap son aproximadas.',
                          'Las rotaciones circulares conservan orden pero introducen un cierre artificial de la serie.',
                          'Los contrastes describen registros institucionales y no establecen causas ni riesgos por viaje.'])
    save_json('fase2_resultados.json',summary)
    print(results[['id','estadistico','p','p_bonferroni','decision']].to_string(index=False))
    return summary


if __name__=='__main__':main()
