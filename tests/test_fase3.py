"""Pruebas de Fase 3 sin CSV, JSON, PNG ni modelos candidatos auxiliares."""
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
import os
import subprocess
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import joblib
import numpy as np
import pandas as pd
import nbformat
import matplotlib

matplotlib.use('Agg')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.preparar_datos import reconstruir
from src.inferencia import inferir
from src.complementos_fase3 import leer_resultados, leer_figuras
from src.empaquetar_entrega import archivos_entrega

HISTORICOS = {
    'Fase1_Accidentes_Transito.ipynb': 'abd33db56fead6e534c608e3a5f48a270e8f4adbe859b280a949a46d38fb9834',
    'Fase2_Analisis_Inferencial.ipynb': '2bf7df89109715fd92dd9c452bd7f056cbc81524d620bbade042563f859eb7df'}
# Referencia anterior a la limpieza: F1 macro, recall positivo y AUC de prueba.
REFERENCIA = {
    'Línea Base (Dummy)': [.45104895104895104, 0., .5],
    'Regresión Logística': [.5211985768110563, .5153061224489796, .5869296223472779],
    'Árbol de Decisión': [.5298714210887336, .45408163265306123, .580917915338893],
    'Random Forest': [.4971358365070835, .5204081632653061, .5816015775080796],
    'Naive Bayes Categórico': [.5211985768110563, .5153061224489796, .5989304359617601]}


class Fase3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sklearn.model_selection import GridSearchCV
        cls.df, _ = reconstruir()
        cls.resultados = leer_resultados()
        cls.modelo = joblib.load(ROOT / 'output/fase3/mejor_modelo_fase3.joblib')
        cls.nb = nbformat.read(ROOT / 'notebooks/Fase3_Accidentes_AUDITADA.ipynb', as_version=4)
        cls.ns = {'__name__': '__fase3_test__'}
        cls.ajustes = []
        ajustar_original = GridSearchCV.fit

        def ajustar(busqueda, x, y, *args, **kwargs):
            cls.ajustes.append(set(x.index))
            return ajustar_original(busqueda, x, y, *args, **kwargs)

        # Recalcula todos los candidatos en memoria. Se prohíbe guardar figuras,
        # se captura el único dump y se compara después con el modelo real de disco.
        with redirect_stdout(StringIO()), patch('IPython.display.display'), \
             patch('src.complementos_fase3.display'), patch('matplotlib.pyplot.show'), \
             patch('matplotlib.figure.Figure.savefig', side_effect=AssertionError('No guardar PNG')), \
             patch.object(GridSearchCV, 'fit', ajustar), patch('joblib.dump') as dump:
            for i, c in enumerate(cls.nb.cells):
                if c.cell_type == 'code':
                    exec(compile(c.source, f'notebook:celda-{i}', 'exec'), cls.ns)
            cls.dumps = list(dump.call_args_list)

    def test_conteos_y_procedencia(self):
        self.assertEqual(self.df.es_fallecido.value_counts().to_dict(), {0: 4513, 1: 980})
        self.assertEqual(len(self.df[['sexo', 'grupo_edad']].drop_duplicates()), 16)
        self.assertTrue((self.df.es_fallecido == self.df.gravedad.eq('Fallecido')).all())

    def test_territorio_cotejado_y_contraste_historico(self):
        t = self.ns['tablas_contexto']['territorio']
        self.assertEqual(len(t), 3)
        self.assertEqual(t.total_victimas.tolist(), [167, 476, 848])
        self.assertEqual(t.fallecidos.tolist(), [26, 82, 187])
        np.testing.assert_allclose(t.tasa_fallecidos_pct, 100*t.fallecidos/t.total_victimas)
        h1 = self.ns['tablas_contexto']['territorio_h1']
        self.assertEqual(h1.loc['Metropolitana', ['heridos','fallecidos','total_victimas']].tolist(), [535,108,643])
        self.assertEqual(h1.loc['Interior','total_victimas'], 848)
        hist = self.ns['tablas_contexto']['antecedentes_historicos']
        self.assertAlmostEqual(hist.loc['H1','p_valor_ajustado_bonferroni'], .046564674809012656)
        self.assertIn('pequeño', self.resultados['contexto']['interpretacion_h1'])
        self.assertEqual(len(self.ns['X_demog']), 5493)
        self.assertEqual(list(self.ns['X_demog'].columns), ['sexo','grupo_edad'])

    def test_procedencia_vehicular_y_limites(self):
        t = self.ns['tabla_vehicular']
        self.assertEqual(t[['heridos','fallecidos']].to_numpy().tolist(), [[384,155],[1055,269],[671,114]])
        mensual = self.ns['tablas_contexto']['vehicular_mensual']
        self.assertEqual(len(mensual),12)
        self.assertEqual(mensual[['heridos_resta','fallecidos_resta']].sum().tolist(),[671,114])
        self.assertTrue((mensual[['heridos_resta','fallecidos_resta']]>=0).all().all())
        p = self.ns['tablas_contexto']['vehicular_procedencia']
        self.assertEqual(p[['heridos','fallecidos']].to_numpy().tolist(),[[384,155],[671,114]])
        a = self.resultados['contexto']
        self.assertTrue(a['csv_vehicular_reconstruido'])
        self.assertFalse(a['categorias_vehiculares_acreditadas'])
        self.assertFalse(a['universo_vehicular_comparable_acreditado'])
        self.assertEqual(a['periodo'],2021)
        self.assertEqual(a['meses_verificados'],12)
        for nombre,digest in a['sha256_originales'].items():
            self.assertEqual(hashlib.sha256((ROOT/'data'/nombre).read_bytes()).hexdigest(),digest)

    def test_edad_desconocida_separada(self):
        desconocida = self.df.grupo_edad.eq('Ignorado')
        self.assertEqual(int(desconocida.sum()),353)
        self.assertEqual(int(self.df.loc[desconocida,'es_fallecido'].sum()),61)
        self.assertTrue(self.df.loc[desconocida,'edad_orden'].eq(-1).all())
        self.assertTrue(self.df.loc[desconocida,'es_adulto_mayor'].eq(0).all())
        grupos = self.ns['tablas_contexto']['edad_auditoria']
        self.assertEqual(grupos.victimas.tolist(),[4832,308,353])
        self.assertEqual(int(grupos.victimas.sum()),5493)
        enc = self.modelo.named_steps['prep'].named_transformers_['cat']
        self.assertIn('grupo_edad_Ignorado',enc.get_feature_names_out(['sexo','grupo_edad']))
        dos = pd.DataFrame({'sexo':['Hombre','Hombre'], 'grupo_edad':['Ignorado','De 0 a 13 anos']})
        transformado = self.modelo.named_steps['prep'].transform(dos)
        self.assertFalse(np.array_equal(transformado[0],transformado[1]))

    def test_integracion_hipotesis_y_salidas_de_contexto(self):
        t = self.resultados['tablas']['hipotesis_integradas']
        self.assertEqual(t.index.tolist(),['H1','H2','H3','H4'])
        self.assertIn('H1',self.resultados['conclusiones'])
        self.assertIn('H3',self.resultados['conclusiones'])
        self.assertIn('H4',self.resultados['conclusiones'])
        self.assertIn('conservó -1',self.resultados['contexto']['interpretacion_edad'])
        for nombre,tabla in self.ns['tablas_contexto'].items():
            pd.testing.assert_frame_equal(self.resultados['tablas'][nombre],tabla,check_dtype=False,atol=1e-14)

    def test_reconstruccion_sin_csv_previo(self):
        with tempfile.TemporaryDirectory(prefix='accidentes_datos_') as carpeta:
            base = Path(carpeta)
            (base/'data').mkdir()
            fuente = next((ROOT/'data').glob('12.2.1.*.csv'))
            shutil.copy2(fuente,base/'data'/fuente.name)
            self.assertFalse((base/'output/victimas_individual_limpio.csv').exists())
            nuevo,_ = reconstruir(base)
            pd.testing.assert_frame_equal(nuevo,self.df)
            self.assertTrue((base/'output/victimas_individual_limpio.csv').exists())

    def test_particion_y_pliegues_reproducibles(self):
        from sklearn.model_selection import train_test_split
        tr, te = train_test_split(self.df.index, test_size=.2, random_state=42, stratify=self.df.es_fallecido)
        n = self.ns
        self.assertEqual(set(tr), set(n['X_train_d'].index))
        self.assertEqual(set(te), set(n['X_test_d'].index))
        self.assertFalse(set(tr) & set(te))
        self.assertEqual(len(te), 1099)
        self.assertEqual(int(n['y_test_d'].sum()), 196)
        self.assertEqual(len(n['pliegues']), 5)
        for a, b in n['pliegues']:
            self.assertFalse(set(a) & set(b))
            self.assertEqual(len(a) + len(b), len(tr))

    def test_ajuste_sin_datos_de_prueba(self):
        train = set(self.ns['X_train_d'].index)
        test = set(self.ns['X_test_d'].index)
        self.assertEqual(len(self.ajustes), 4)
        for indices in self.ajustes:
            self.assertEqual(indices, train)
            self.assertFalse(indices & test)
        for m in self.ns['modelos_optimizados'].values():
            self.assertEqual(list(m.feature_names_in_), ['sexo', 'grupo_edad'])
        from sklearn.base import clone
        m = clone(self.modelo).fit(self.ns['X_train_d'], self.ns['y_train_d'])
        np.testing.assert_allclose(m.predict_proba(self.ns['X_test_d']), self.modelo.predict_proba(self.ns['X_test_d']), atol=1e-14)

    def test_cuatro_modelos_tres_familias_y_seleccion_cv(self):
        from sklearn.pipeline import Pipeline
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.naive_bayes import CategoricalNB
        candidatos = self.ns['modelos_optimizados']
        self.assertEqual(len(candidatos), 4)
        self.assertEqual({type(m.named_steps['clf']) for m in candidatos.values()},
                         {LogisticRegression, DecisionTreeClassifier, RandomForestClassifier, CategoricalNB})
        self.assertTrue(all(isinstance(m, Pipeline) for m in candidatos.values()))
        cv = self.ns['df_reporte_cv'].loc[list(candidatos), 'F1-Macro (Validación CV)']
        self.assertEqual(cv.idxmax(), 'Árbol de Decisión')
        self.assertEqual(self.ns['nombre_mejor_modelo'], cv.idxmax())
        self.assertEqual(self.modelo.metadatos_fase3_['modelo'], cv.idxmax())

    def test_metricas_iguales_a_antes_de_limpiar(self):
        t = self.ns['df_resultados_test']
        for nombre, valores in REFERENCIA.items():
            np.testing.assert_allclose(t.loc[nombre, ['F1-Macro', 'Recall (Fallecido)', 'ROC-AUC']].to_numpy(float),
                                       valores, atol=1e-14, rtol=0)

    def test_metricas_recalculadas_y_embebidas(self):
        from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                                     roc_auc_score, balanced_accuracy_score, brier_score_loss)
        n = self.ns
        for nombre, m in {'Línea Base (Dummy)': n['dummy_baseline'], **n['modelos_optimizados']}.items():
            y, pred, prob = n['y_test_d'], m.predict(n['X_test_d']), m.predict_proba(n['X_test_d'])[:, 1]
            valores = [accuracy_score(y,pred), precision_score(y,pred,zero_division=0),
                       recall_score(y,pred), f1_score(y,pred), f1_score(y,pred,average='macro'),
                       roc_auc_score(y,prob), recall_score(y,pred,pos_label=0),
                       balanced_accuracy_score(y,pred), brier_score_loss(y,prob)]
            cols = ['Accuracy','Precision (Fallecido)','Recall (Fallecido)','F1-Score (Fallecido)',
                    'F1-Macro','ROC-AUC','Specificity','Balanced Accuracy','Brier']
            np.testing.assert_allclose(n['df_resultados_test'].loc[nombre,cols].to_numpy(float), valores, atol=1e-14)
        for clave, variable in [('metricas_test','df_resultados_test'), ('validacion','df_reporte_cv'), ('brechas','df_brechas')]:
            pd.testing.assert_frame_equal(self.resultados['tablas'][clave], n[variable], check_dtype=False, atol=1e-14)

    def test_errores_y_solapamiento(self):
        from sklearn.metrics import confusion_matrix
        n = self.ns
        x, y = n['X_test_d'], n['y_test_d']
        pred = self.modelo.predict(x)
        self.assertEqual(confusion_matrix(y,pred).ravel().tolist(), [609,294,107,89])
        fn = x.loc[(y == 1) & (pred == 0)]
        mujer = fn.sexo.eq('Mujer')
        joven = fn.grupo_edad.isin(['De 0 a 13 anos','De 14 a 17 anos','De 18 a 29 anos'])
        self.assertEqual([len(fn),int(mujer.sum()),int(joven.sum()),int((mujer&joven).sum()),int((mujer|joven).sum())], [107,33,81,15,99])
        resto = fn.loc[~(mujer|joven)]
        self.assertEqual(len(resto),8)
        self.assertTrue((resto.sexo.eq('Hombre') & resto.grupo_edad.eq('Ignorado')).all())
        self.assertEqual(n['tablas_extra']['descomposicion_FN'].FN.sum(),107)
        self.assertEqual(self.resultados['solapamiento'], n['solapamiento_FN'])

    def test_sensibilidad_y_equivalencia(self):
        n = self.ns
        tabla = n['tablas_extra']['sensibilidad_todos']
        self.assertEqual(len(tabla),20)
        s = tabla.groupby('Modelo')[['F1_macro','AUC_ROC']].mean().loc['Árbol de Decisión']
        np.testing.assert_allclose(s, [.4555926527627962, .5248064569405873], atol=1e-12)
        self.assertLess(n['equivalencia_frecuencias']['max_diferencia_puntuacion'], .002)

    def test_unico_modelo_y_metadatos_integrados(self):
        self.assertEqual([p.name for p in (ROOT/'output').rglob('*.joblib')], ['mejor_modelo_fase3.joblib'])
        self.assertEqual(len(self.dumps),1)
        self.assertIs(self.dumps[0].args[0], self.ns['mejor_modelo_demografico'])
        x = self.df[['sexo','grupo_edad']].drop_duplicates()
        np.testing.assert_allclose(self.modelo.predict_proba(x), self.ns['mejor_modelo_demografico'].predict_proba(x), atol=1e-14)
        self.assertEqual(self.modelo.metadatos_fase3_, self.ns['metadatos'])

    def test_inferencia_independiente_y_categorias(self):
        for row in self.df[['sexo','grupo_edad']].drop_duplicates().to_dict('records'):
            r = inferir(**row)
            self.assertAlmostEqual(r['puntuacion_no_calibrada'], self.modelo.predict_proba(pd.DataFrame([row]))[0,1])
        for sexo,edad in [('Otro','Ignorado'),('Hombre','20'),('',''),('Hombre',None)]:
            with self.assertRaises(ValueError): inferir(sexo,edad)
        for sexo,esperado in [('Hombre',0),('INVALIDO',2)]:
            p = subprocess.run([sys.executable,str(ROOT/'src/inferencia.py'),'--sexo',sexo,'--grupo-edad','Ignorado'],
                               cwd=ROOT/'notebooks',capture_output=True,text=True,encoding='utf-8',
                               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
            self.assertEqual(p.returncode,esperado,p.stderr)
            if esperado == 0:
                r = json.loads(p.stdout)
                self.assertEqual(r, inferir(sexo,'Ignorado'))

    def test_notebooks_historicos_intactos(self):
        for nombre,digest in HISTORICOS.items():
            self.assertEqual(hashlib.sha256((ROOT/'notebooks'/nombre).read_bytes()).hexdigest(),digest)

    def test_notebook_html_y_figuras_sin_archivos_png(self):
        for c in self.nb.cells:
            if c.cell_type == 'code':
                self.assertIsNotNone(c.execution_count)
                self.assertFalse(any(o.output_type=='error' for o in c.outputs))
                self.assertNotIn('.savefig(',c.source)
                self.assertNotIn('.to_csv(',c.source)
        figuras = leer_figuras()
        self.assertEqual(len(figuras),11)
        self.assertTrue(all(v.startswith(b'\x89PNG\r\n\x1a\n') for v in figuras.values()))
        f3 = ROOT/'output/fase3'
        self.assertEqual({p.name for p in f3.iterdir()}, {'Fase3_Accidentes_AUDITADA.html','mejor_modelo_fase3.joblib'})
        html = (f3/'Fase3_Accidentes_AUDITADA.html').read_text(encoding='utf-8')
        self.assertGreaterEqual(html.count('data:image/png;base64,'),11)

    def test_paquete_sin_material_local(self):
        paths = archivos_entrega()
        self.assertTrue(all(p.is_file() for p in paths))
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in paths if p.suffix == '.md'], ['README.md'])
        self.assertTrue(all('local' not in p.relative_to(ROOT).parts for p in paths))
        self.assertFalse(any(p.suffix.lower() == '.png' or p.name.endswith('_excel.csv') for p in paths))
        self.assertIn(ROOT/'src/inferencia.py', paths)
        self.assertIn(ROOT/'tests/test_fase3.py', paths)
        self.assertIn(ROOT/'output/fase3/mejor_modelo_fase3.joblib', paths)

    def test_informes_autocontenidos_y_limites_pdf(self):
        import pymupdf
        from xml.etree import ElementTree as ET
        for nombre,limite,min_imagenes in [('Informe_Fase3',15,7),('Informe_Integrador_DataScience',30,5)]:
            carpeta = ROOT/'docs'/('fase3' if nombre == 'Informe_Fase3' else 'integrador')
            with ZipFile(carpeta/(nombre+'.docx')) as z:
                self.assertIsNone(z.testzip())
                self.assertGreaterEqual(len([f for f in z.namelist() if f.startswith('word/media/')]),min_imagenes)
                rels=ET.fromstring(z.read('word/_rels/document.xml.rels'))
                self.assertFalse(any(r.get('Type','').endswith('/image') and r.get('TargetMode')=='External' for r in rels))
                raiz = ET.fromstring(z.read('word/document.xml'))
                word = ''.join(raiz.itertext())
            with pymupdf.open(carpeta/(nombre+'.pdf')) as pdf:
                self.assertLessEqual(len(pdf),limite)
                self.assertGreaterEqual(sum(len(p.get_images()) for p in pdf),min_imagenes)
                self.assertIn('33+81-15=99',''.join(p.get_text() for p in pdf).replace(' ',''))
                texto = ''.join(p.get_text() for p in pdf)
                for clave in ['H1','H2','H3','H4','353','308','0.5299','0.5809']:
                    self.assertIn(clave,word)
                    self.assertIn(clave,texto)
                self.assertRegex(word,r'4[.\s]?832')
                self.assertRegex(texto,r'4[.\s]?832')


if __name__ == '__main__':
    unittest.main(verbosity=2)
