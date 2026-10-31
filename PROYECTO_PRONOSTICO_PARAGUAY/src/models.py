"""Familias de pronostico con el mismo horizonte y sin variables futuras reales."""
import itertools
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from common import SEED

FEATURES=['rezago_1','rezago_2','rezago_3','rezago_6','rezago_12',
          'media_previa_3','media_previa_12','sin_mes','cos_mes','dias_mes']


def specifications():
    specs=[dict(familia='Referencia estacional',parametros={}),
           dict(familia='Referencia media12',parametros={})]
    specs += [dict(familia='Ridge',parametros=dict(alpha=a)) for a in [.1,1.,10.,100.]]
    specs += [dict(familia='Random Forest',parametros=dict(max_depth=d,min_samples_leaf=l,n_estimators=250))
              for d,l in itertools.product([3,None],[2,5,10])]
    specs += [dict(familia='SVR',parametros=dict(C=c,epsilon=e,gamma='scale'))
              for c,e in itertools.product([1.,10.,100.],[5.,15.])]
    specs += [dict(familia='ETS',parametros=dict(trend=t,seasonal=s,damped_trend=t is not None))
              for t,s in itertools.product([None,'add'],[None,'add'])]
    for i,spec in enumerate(specs):spec['id']=f'M{i:02d}'
    return specs


def feature_row(history,date):
    values=np.asarray(history,float)
    if len(values)<12:raise ValueError('Se requieren doce meses anteriores completos.')
    m=date.month
    return [values[-1],values[-2],values[-3],values[-6],values[-12],
            values[-3:].mean(),values[-12:].mean(),np.sin(2*np.pi*m/12),
            np.cos(2*np.pi*m/12),date.days_in_month]


def supervised(y):
    xx=[feature_row(y.iloc[:i],y.index[i]) for i in range(12,len(y))]
    return pd.DataFrame(xx,columns=FEATURES,index=y.index[12:]),y.iloc[12:]


def fit_model(y,spec):
    y=y.astype(float).copy();family=spec['familia'];params=spec['parametros']
    model=dict(spec=spec,history=y,warnings=[])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        if family=='Ridge':
            estimator=make_pipeline(StandardScaler(),Ridge(**params))
        elif family=='Random Forest':
            estimator=RandomForestRegressor(**params,random_state=SEED,n_jobs=1)
        elif family=='SVR':
            estimator=make_pipeline(StandardScaler(),SVR(**params))
        elif family=='ETS':
            estimator=ExponentialSmoothing(y.to_numpy(),seasonal_periods=12,
                initialization_method='estimated',**params).fit(optimized=True,remove_bias=False)
        elif family.startswith('Referencia'):
            estimator=None
        else:raise ValueError(f'Familia desconocida: {family}')
        if family in ['Ridge','Random Forest','SVR']:
            xx,yy=supervised(y);estimator.fit(xx,yy)
        model['estimator']=estimator
        model['warnings']=[str(w.message) for w in caught]
    return model


def forecast(model,months=12,perturb=None,rng=None):
    family=model['spec']['familia'];y=model['history'];values=y.to_numpy(float).tolist()
    dates=pd.date_range(y.index[-1]+pd.offsets.MonthBegin(1),periods=months,freq='MS')
    if family=='Referencia media12':pred=np.repeat(np.mean(values[-12:]),months)
    elif family=='Referencia estacional':pred=np.array([values[-12+i%12] for i in range(months)])
    elif family=='ETS':pred=np.asarray(model['estimator'].forecast(months),float)
    else:
        pred=[]
        for date in dates:
            row=feature_row(values,date)
            if perturb is not None:
                column,reference=perturb
                row[FEATURES.index(column)]=float(rng.choice(reference))
            xx=pd.DataFrame([row],columns=FEATURES)
            value=max(0.,float(model['estimator'].predict(xx)[0]))
            pred.append(value);values.append(value)
        pred=np.asarray(pred)
    pred=np.maximum(np.asarray(pred,float),0)
    if not np.isfinite(pred).all():raise ValueError('Prediccion no finita.')
    return pd.Series(pred,index=dates,name='prediccion')


def fitted_values(model):
    family=model['spec']['familia'];y=model['history']
    if family=='Referencia media12':pred=y.shift(1).rolling(12).mean().iloc[12:]
    elif family=='Referencia estacional':pred=y.shift(12).iloc[12:]
    elif family=='ETS':pred=pd.Series(np.asarray(model['estimator'].fittedvalues)[12:],index=y.index[12:])
    else:
        xx,_=supervised(y);pred=pd.Series(model['estimator'].predict(xx),index=xx.index)
    return pred.clip(lower=0)
