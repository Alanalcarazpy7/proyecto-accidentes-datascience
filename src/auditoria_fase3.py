"""Contrastes corregidos y predicción territorial sobre frecuencias originales.

Los intervalos son condicionales a conteos y supuestos multinomiales/binomiales;
no incorporan conglomeración por siniestro ni errores de cobertura desconocidos.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]


def contraste_ordinal(fallecidos, heridos, bootstrap=2000, semilla=42):
    x, y = np.asarray(fallecidos), np.asarray(heridos)
    u, p = stats.mannwhitneyu(x, y, alternative='greater', method='asymptotic')
    n, m = len(x), len(y)
    _, ties = np.unique(np.r_[x, y], return_counts=True)
    var = n*m/12 * (n+m+1 - np.sum(ties**3-ties)/((n+m)*(n+m-1)))
    z = (u-n*m/2)/np.sqrt(var)  # Rosenthal histórico, sin continuidad; p de scipy con continuidad.
    rng = np.random.default_rng(semilla)
    valores = np.unique(np.r_[x, y])
    cx = np.array([(x==v).sum() for v in valores])
    cy = np.array([(y==v).sum() for v in valores])
    bx = rng.multinomial(n, cx/n, size=bootstrap)
    by = rng.multinomial(m, cy/m, size=bootstrap)
    # U por frecuencias: P(X>Y) + 0.5 P(X=Y), sin inventar vínculos.
    ub = (bx*(np.cumsum(by, axis=1)-by/2)).sum(axis=1)
    rb = 2*ub/(n*m)-1
    def medianas(c):
        acumulado = c.cumsum(axis=1)
        total = c.sum(axis=1)
        lo = (acumulado <= ((total-1)//2)[:,None]).sum(axis=1)
        hi = (acumulado <= (total//2)[:,None]).sum(axis=1)
        return (valores[lo]+valores[hi])/2
    return dict(n_fallecidos=n, n_heridos=m, U=float(u), p=float(p),
                Z=float(z), r_rosenthal=float(z/np.sqrt(n+m)),
                r_biserial=float(2*u/(n*m)-1),
                ic95_r_biserial=np.quantile(rb,[.025,.975]).tolist(),
                diferencia_mediana=float(np.median(x)-np.median(y)),
                ic95_diferencia_mediana=np.quantile(medianas(bx)-medianas(by),[.025,.975]).tolist(),
                bootstrap=bootstrap, semilla=semilla)


def analizar_edad(df):
    conocido = df.grupo_edad.ne('Ignorado')
    def ordinal(d):
        return contraste_ordinal(d.loc[d.es_fallecido.eq(1),'edad_orden'].to_numpy(float),
                                 d.loc[d.es_fallecido.eq(0),'edad_orden'].to_numpy(float))
    historico = df.copy()
    historico['edad_orden'] = historico.edad_orden.fillna(-1)
    anterior, corregido = ordinal(historico), ordinal(df.loc[conocido])
    adultos = df.loc[conocido].groupby('es_adulto_mayor').es_fallecido.agg(['sum','count'])
    a, b = int(adultos.loc[1,'sum']), int(adultos.loc[1,'count']-adultos.loc[1,'sum'])
    c, d = int(adultos.loc[0,'sum']), int(adultos.loc[0,'count']-adultos.loc[0,'sum'])
    rr, odds = (a/(a+b))/(c/(c+d)), a*d/(b*c)
    se_rr = np.sqrt(1/a-1/(a+b)+1/c-1/(c+d))
    se_or = np.sqrt(1/a+1/b+1/c+1/d)
    p = float(stats.fisher_exact([[a,b],[c,d]], alternative='greater').pvalue)
    # Familia conservadora: H1, H2, H4 ordinal y contraste adicional >=60.
    # H3 se excluye por falta de categorías acreditadas, sin validarlo por su p histórico.
    for resultado in [anterior, corregido]:
        resultado['p_bonferroni_4'] = min(1.,4*resultado['p'])
    mayor = dict(fallecidos_mayores=a, heridos_mayores=b, fallecidos_menores=c, heridos_menores=d,
                 RR=rr, OR=odds, ic95_RR=np.exp(np.log(rr)+np.array([-1,1])*1.959963984540054*se_rr).tolist(),
                 ic95_OR=np.exp(np.log(odds)+np.array([-1,1])*1.959963984540054*se_or).tolist(),
                 p=p, p_bonferroni_4=min(1.,4*p))
    return anterior, corregido, mayor


def territorio_mensual(root=ROOT):
    raw = pd.read_csv(next((root/'data').glob('12.2.6.*.csv')),sep=';',dtype=str)
    def numero(s):
        return 0 if s.strip()=='-' else int(s.replace('.',''))
    filas=[]
    for mes, (_,r) in enumerate(raw.iloc[1:].iterrows(),1):
        for zona,col in [('Asunción','ASUNCION'),('Central','ZONA CENTRAL'),('Interior','INTERIOR')]:
            h,f,n = [numero(r[k+' - '+col]) for k in ['HERIDOS','MUERTOS','TOTAL']]
            if h+f != n or n<=0:
                raise ValueError('Conteos territoriales inconsistentes')
            filas.append(dict(mes=mes,zona=zona,heridos=h,fallecidos=f,total=n))
    df=pd.DataFrame(filas)
    if len(df)!=36 or df[['heridos','fallecidos','total']].sum().tolist()!=[1196,295,1491]:
        raise ValueError('Granularidad o totales territoriales inesperados')
    return df


def evaluar_territorio(root=ROOT):
    """GLM binomial por zona; 3 bloques prospectivos internos, sin búsqueda.

    Mes determina el corte, no es predictor: un único ciclo anual no identifica
    estacionalidad. El GLM con intercepto y dos zonas estima las tasas por zona.
    """
    df=territorio_mensual(root)
    design=pd.DataFrame({'intercepto':1.,'Central':df.zona.eq('Central').astype(float),
                         'Interior':df.zona.eq('Interior').astype(float)})
    filas=[]
    predicciones=[]
    for fin in [6,8,10]:
        tr,va=df.mes.le(fin),df.mes.between(fin+1,fin+2)
        modelo=sm.GLM(df.loc[tr,['fallecidos','heridos']].to_numpy(),design.loc[tr],
                      family=sm.families.Binomial()).fit()
        p_base=df.loc[tr,'fallecidos'].sum()/df.loc[tr,'total'].sum()
        for nombre,p in [('Base (tasa global)',np.full(va.sum(),p_base)),
                         ('Binomial (zona)',modelo.predict(design.loc[va]).to_numpy())]:
            v=df.loc[va]; n=v.total.to_numpy(); y=v.fallecidos.to_numpy(); q=y/n
            p=np.clip(p,1e-12,1-1e-12)
            filas.append(dict(modelo=nombre,ultimo_mes_train=fin,primer_mes_validacion=fin+1,
                              ultimo_mes_validacion=fin+2,celdas_train=int(tr.sum()),celdas_validacion=int(va.sum()),
                              victimas_validacion=int(n.sum()),
                              log_loss=float(-(y*np.log(p)+(n-y)*np.log1p(-p)).sum()/n.sum()),
                              brier=float((y*(1-p)**2+(n-y)*p**2).sum()/n.sum()),
                              MAE_proporcion_ponderado=float(np.average(abs(q-p),weights=n))))
            predicciones.append(v.assign(modelo=nombre,ultimo_mes_train=fin,probabilidad=p))
    final=sm.GLM(df[['fallecidos','heridos']].to_numpy(),design,family=sm.families.Binomial()).fit()
    coef=pd.DataFrame({'coeficiente':final.params,'OR':np.exp(final.params)})
    return df,pd.DataFrame(filas),pd.concat(predicciones,ignore_index=True),coef


def complementos_auditados(df,root=ROOT):
    anterior,actual,mayor=analizar_edad(df)
    mensual,metricas,predicciones,coef=evaluar_territorio(root)
    return {'h4_ordinal':pd.DataFrame([anterior,actual],index=['Histórico con -1','Corregido edad conocida']),
            'h4_mayores60':pd.DataFrame([mayor]),'territorio_mensual':mensual,
            'territorio_validacion':metricas,'territorio_predicciones':predicciones,
            'territorio_coeficientes':coef}
