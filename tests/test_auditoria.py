"""Pruebas de las correcciones inferenciales y del experimento agregado."""
from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.model_selection import GroupKFold
from src.preparar_datos import reconstruir
from src.auditoria_fase3 import analizar_edad, contraste_ordinal, evaluar_territorio
from src.complementos_fase3 import leer_resultados

ROOT = Path(__file__).resolve().parents[1]


class AuditoriaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df,_=reconstruir()
        cls.anterior,cls.actual,cls.mayor=analizar_edad(cls.df)
        cls.mensual,cls.metricas,cls.pred,cls.coef=evaluar_territorio()

    def test_h4_excluye_solo_desconocidos(self):
        a=self.actual
        self.assertEqual((a['n_fallecidos'],a['n_heridos']),(919,4221))
        self.assertEqual(a['U'],2299236.)
        d=self.df.loc[self.df.grupo_edad.ne('Ignorado')]
        x=d.loc[d.es_fallecido.eq(1),'edad_orden'].to_numpy(float)
        y=d.loc[d.es_fallecido.eq(0),'edad_orden'].to_numpy(float)
        r=stats.mannwhitneyu(x,y,alternative='greater',method='asymptotic')
        self.assertEqual(a['p'],r.pvalue)
        self.assertLess(a['p_bonferroni_4'],.05)
        self.assertEqual(self.anterior['U'],2576490.)
        self.assertAlmostEqual(self.anterior['p']/2.1956703482936283e-17,1.,places=10)
        self.assertTrue(self.df.loc[self.df.grupo_edad.eq('Ignorado'),['edad_orden','es_adulto_mayor']].isna().all().all())

    def test_bootstrap_efecto_reproducible_y_acotado(self):
        self.assertEqual(analizar_edad(self.df)[1],self.actual)
        lo,hi=self.actual['ic95_r_biserial']
        self.assertTrue(-1<=lo<self.actual['r_biserial']<hi<=1)
        self.assertEqual(self.actual['ic95_diferencia_mediana'],[1.,1.])
        # Ejemplo independiente: todos los rangos de fallecidos superan a heridos.
        simple=contraste_ordinal([2,3,3],[0,1,1],bootstrap=20)
        self.assertEqual(simple['U'],9.)
        self.assertEqual(simple['r_biserial'],1.)
        self.assertEqual(simple['ic95_r_biserial'],[1.,1.])
        from src.complementos_fase3 import serializar_tabla
        tabla=pd.DataFrame({'p':[self.actual['p'],self.mayor['p']]})
        resultado=serializar_tabla(tabla)
        self.assertEqual([fila['p'] for fila in resultado['data']],tabla.p.tolist())

    def test_adultos_mayores_usa_denominadores_conocidos(self):
        a=self.mayor
        self.assertEqual([a[k] for k in ['fallecidos_mayores','heridos_mayores','fallecidos_menores','heridos_menores']],[106,202,813,4019])
        self.assertAlmostEqual(a['RR'],(106/308)/(813/4832))
        self.assertAlmostEqual(a['OR'],106*4019/(202*813))
        self.assertTrue(a['ic95_RR'][0]>1)
        self.assertLess(a['p_bonferroni_4'],.05)
        self.assertAlmostEqual(a['p_bonferroni_4'],4*a['p'])

    def test_territorio_36_celdas_no_microdatos(self):
        d=self.mensual
        self.assertEqual(len(d),36)
        self.assertEqual(len(d[['mes','zona']].drop_duplicates()),36)
        self.assertEqual(d.total.sum(),1491)
        self.assertEqual(d.fallecidos.sum(),295)
        self.assertTrue(d.heridos.add(d.fallecidos).eq(d.total).all())
        self.assertEqual(len(self.metricas),6)

    def test_territorio_probabilidades_solo_meses_previos(self):
        d=self.mensual
        for (modelo,fin),p in self.pred.groupby(['modelo','ultimo_mes_train']):
            train=d.loc[d.mes.le(fin)]
            self.assertTrue(p.mes.gt(fin).all())
            self.assertTrue(p.mes.le(fin+2).all())
            if modelo=='Base (tasa global)':
                esperado=np.repeat(train.fallecidos.sum()/train.total.sum(),len(p))
            else:
                tasas=train.groupby('zona')[['fallecidos','total']].sum()
                esperado=p.zona.map(tasas.fallecidos/tasas.total)
            np.testing.assert_allclose(p.probabilidad,esperado,atol=1e-10)

    def test_metricas_territoriales_verificadas_por_conteos(self):
        for r in self.metricas.itertuples():
            p=self.pred.loc[self.pred.modelo.eq(r.modelo)&self.pred.ultimo_mes_train.eq(r.ultimo_mes_train)]
            q=p.probabilidad; f=p.fallecidos; h=p.heridos
            self.assertAlmostEqual(r.log_loss,float(-(f*np.log(q)+h*np.log1p(-q)).sum()/p.total.sum()))
            self.assertAlmostEqual(r.brier,float((f*(1-q)**2+h*q**2).sum()/p.total.sum()))

    def test_pliegues_de_perfiles_sin_solapamiento(self):
        from sklearn.model_selection import train_test_split
        x=self.df[['sexo','grupo_edad']]
        xt,_,yt,_=train_test_split(x,self.df.es_fallecido,test_size=.2,stratify=self.df.es_fallecido,random_state=42)
        grupos=xt.sexo+' | '+xt.grupo_edad
        vistos=[]
        for tr,va in GroupKFold(4).split(xt,yt,grupos):
            self.assertFalse(set(grupos.iloc[tr])&set(grupos.iloc[va]))
            vistos.extend(va)
            self.assertEqual(yt.iloc[va].nunique(),2)
        self.assertEqual(sorted(vistos),list(range(len(xt))))

    def test_reconstruccion_rechaza_cambios_de_target(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); (root/'data').mkdir(); (root/'output').mkdir()
            for p in (ROOT/'data').glob('12.2.1.*.csv'): shutil.copy2(p,root/'data'/p.name)
            original=self.df.copy(); original.loc[0,'es_fallecido']=1
            original.to_csv(root/'output/victimas_individual_limpio.csv',index=False)
            with self.assertRaises(AssertionError): reconstruir(root)

    def test_resumenes_regenerados_sin_output_previo(self):
        from src.regenerar_contexto import regenerar_resumenes
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            shutil.copytree(ROOT/'data',root/'data')
            nuevo,_=reconstruir(root)
            pd.testing.assert_frame_equal(nuevo,self.df)
            tablas=regenerar_resumenes(root)
            for nombre in tablas:
                pd.testing.assert_frame_equal(pd.read_csv(root/'output'/nombre),
                                              pd.read_csv(ROOT/'output'/nombre),check_dtype=False)
            self.assertFalse((root/'output/victimas_vehiculo_limpio.csv').exists())

    def test_contexto_sin_csv_vehicular_no_fabrica_categorias(self):
        from src.complementos_fase3 import preparar_contexto
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            shutil.copytree(ROOT/'data',root/'data')
            (root/'output/fase2').mkdir(parents=True)
            for nombre in ['victimas_individual_limpio.csv','victimas_zona_resumen.csv',
                           'fase2/resultados_fase2_consolidados.json']:
                shutil.copy2(ROOT/'output'/nombre,root/'output'/nombre)
            tablas,_,a=preparar_contexto(root)
            self.assertFalse(a['csv_vehicular_reconstruido'])
            self.assertFalse(a['categorias_vehiculares_acreditadas'])
            self.assertEqual(len(tablas['vehicular_mensual']),12)
            self.assertFalse((root/'output/victimas_vehiculo_limpio.csv').exists())


if __name__=='__main__': unittest.main()
