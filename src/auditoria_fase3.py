"""Contrastes corregidos y predicción territorial sobre frecuencias originales.

Los intervalos son condicionales a conteos y supuestos multinomiales/binomiales;
no incorporan conglomeración por siniestro ni errores de cobertura desconocidos.
"""
from pathlib import Path
import json
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
    # Se conserva el ajuste de cuatro pruebas del análisis anterior para cotejo.
    # preparar_contexto publica además un ajuste conjunto de seis contrastes,
    # incorporando H3 documentada y su sensibilidad sin motocarro.
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


def contraste_h3(fallecidos, heridos, fallecidos_resto, heridos_resto):
    """Asociación entre grupos de víctimas registradas, a partir de cuatro celdas.

    RR/OR con IC logarítmicos Katz/Woolf; Fisher unilateral en la dirección
    histórica de H3. Se conserva Z de dos proporciones para cotejar Fase 2.
    Los intervalos y p suponen independencia; no ajustan confusión o siniestro.
    """
    celdas = np.asarray([fallecidos, heridos, fallecidos_resto, heridos_resto])
    if not np.isfinite(celdas).all() or not (celdas > 0).all() or not np.equal(celdas, celdas.astype(int)).all():
        raise ValueError('H3 requiere cuatro conteos enteros positivos, sin microdatos fabricados.')
    a,b,c,d = celdas.astype(int)
    n1,n0 = int(a+b),int(c+d)
    rr,odds = (a/n1)/(c/n0), a*d/(b*c)
    z95 = stats.norm.ppf(.975)
    se_rr = np.sqrt(1/a-1/n1+1/c-1/n0)
    se_or = np.sqrt(1/a+1/b+1/c+1/d)
    pooled = (a+c)/(n1+n0)
    z = (a/n1-c/n0)/np.sqrt(pooled*(1-pooled)*(1/n1+1/n0))
    fisher = float(stats.fisher_exact([[a,b],[c,d]],alternative='greater').pvalue)
    return dict(fallecidos_grupo=int(a),heridos_grupo=int(b),
                fallecidos_resto=int(c),heridos_resto=int(d),n_grupo=n1,n_resto=n0,
                n_analisis=n1+n0,fraccion_grupo=float(a/n1),fraccion_resto=float(c/n0),
                RR=float(rr),OR=float(odds),
                ic95_RR=np.exp(np.log(rr)+np.array([-1,1])*z95*se_rr).tolist(),
                ic95_OR=np.exp(np.log(odds)+np.array([-1,1])*z95*se_or).tolist(),
                Z_historico=float(z),p_Z_unilateral=float(stats.norm.sf(z)),
                p_Fisher_unilateral=fisher,
                p_Fisher_bilateral=float(stats.fisher_exact([[a,b],[c,d]],alternative='two-sided').pvalue),
                p_bonferroni_4=min(1.,4*fisher),p_bonferroni_6=min(1.,6*fisher))


def auditar_h3(mensual_ine, root=ROOT):
    """Coteja DINATRAN por mes/rol contra INE; devuelve tablas agregadas.

    La referencia JSON es una transcripción verificable de pp.130 y 136;
    pp.132/133/135 nombran los roles motocicleta/motocarro. No se lee el CSV
    expandido histórico para definir grupos ni se asigna vehículo a personas.
    """
    archivo = root/'data/referencia_h3_dinatran_2021.json'
    evidencia = json.loads(archivo.read_text(encoding='utf-8'))
    if evidencia['periodo'] != 2021:
        raise ValueError('La evidencia H3 debe corresponder a 2021.')
    tablas = evidencia['tablas']
    general = pd.DataFrame(tablas['todos_usuarios']['mensual'])
    moto = pd.DataFrame(tablas['motociclistas_y_motocarro']['mensual'])
    columnas = [c for c in general if c != 'mes']
    roles = ['conductores','acompanantes','pasajeros','ciclistas','peatones']
    if len(general) != 12 or len(moto) != 12 or general.mes.tolist() != moto.mes.tolist():
        raise ValueError('H3 requiere los mismos doce meses y roles.')
    control = []
    for nombre,tabla in [('todos_usuarios',general),('motociclistas_y_motocarro',moto)]:
        valores = tabla[columnas].to_numpy()
        if not np.isfinite(valores).all() or not (valores >= 0).all() or not np.equal(valores,valores.astype(int)).all():
            raise ValueError('Conteos H3 no enteros o negativos.')
        for col in columnas:
            if int(tabla[col].sum()) != tablas[nombre]['anual'][col]:
                raise ValueError('El total anual DINATRAN no coincide con sus meses: '+col)
        for gravedad in ['heridos','fallecidos']:
            if not tabla[[r+'_'+gravedad for r in roles]].sum(axis=1).eq(tabla['total_'+gravedad]).all():
                raise ValueError('Los roles no suman el total mensual de víctimas.')
    normalizar = lambda s:s.str.lower().str.replace('septiembre','setiembre',regex=False)
    if normalizar(general.mes).tolist() != normalizar(mensual_ine.mes).tolist():
        raise ValueError('Los meses INE y DINATRAN no corresponden.')
    for tabla,sufijo in [(general,'12_2_5'),(moto,'12_2_10')]:
        for gravedad in ['heridos','fallecidos']:
            if not np.array_equal(tabla['total_'+gravedad],mensual_ine[gravedad+'_'+sufijo]):
                raise ValueError('Diferencia entre INE y DINATRAN por mes/desenlace.')
    for i in range(12):
        for rol in roles:
            vals = [int(general.loc[i,rol+'_'+g]-moto.loc[i,rol+'_'+g]) for g in ['heridos','fallecidos']]
            if min(vals) < 0:
                raise ValueError('El supuesto de subgrupo no es compatible con los conteos por rol/mes.')
            control.append(dict(mes=general.loc[i,'mes'],rol=rol,heridos_resto=vals[0],fallecidos_resto=vals[1]))
    a = tablas['motociclistas_y_motocarro']['anual']
    g = tablas['todos_usuarios']['anual']
    if [a[c] for c in ['conductores_heridos','conductores_fallecidos','acompanantes_heridos',
                       'acompanantes_fallecidos','pasajeros_heridos','pasajeros_fallecidos']] != [332,129,51,22,1,4]:
        raise ValueError('La transcripción debe preservar las categorías verificadas de DINATRAN.')
    if [g['total_heridos'],g['total_fallecidos']] != [1055,269]:
        raise ValueError('Cobertura general distinta de las 1.324 víctimas verificadas.')
    resumen = pd.DataFrame([
        ['Conductores de motocicleta',a['conductores_heridos'],a['conductores_fallecidos']],
        ['Acompañantes de motocicleta',a['acompanantes_heridos'],a['acompanantes_fallecidos']],
        ['Pasajeros de motocarro',a['pasajeros_heridos'],a['pasajeros_fallecidos']],
        ['Demás usuarios registrados',g['total_heridos']-a['total_heridos'],g['total_fallecidos']-a['total_fallecidos']]
    ],columns=['grupo','heridos','fallecidos']).set_index('grupo')
    resumen['total'] = resumen.heridos+resumen.fallecidos
    comparaciones = pd.DataFrame([
        contraste_h3(155,384,114,671),
        contraste_h3(151,383,114,671)
    ],index=pd.Index(['Histórica: motocicleta y motocarro / demás usuarios',
                     'Precisa: solo motocicleta / demás usuarios (sin motocarro)'],name='comparacion'))
    comparaciones['excluidos_motocarro'] = [0,5]
    return {'h3_usuarios':resumen,'h3_contrastes':comparaciones,
            'h3_cotejo_roles':pd.DataFrame(control)},evidencia
