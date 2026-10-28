"""Conteos, procedencia y contrastes H3, sin fabricar personas ni usar red."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import numpy as np
import pandas as pd
from scipy import stats
from src.auditoria_fase3 import auditar_h3,contraste_h3
from src.complementos_fase3 import preparar_contexto,leer_resultados

ROOT=Path(__file__).resolve().parents[1]


class H3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tablas,_,cls.auditoria=preparar_contexto()
        cls.contrastes=cls.tablas['h3_contrastes']

    def test_fuente_documenta_roles_y_periodo(self):
        e=json.loads((ROOT/'data/referencia_h3_dinatran_2021.json').read_text(encoding='utf-8'))
        self.assertEqual(e['periodo'],2021)
        self.assertEqual(e['dinatran']['paginas'],[130,132,133,135,136])
        self.assertEqual(e['ine']['paginas'],[307,311])
        self.assertRegex(e['dinatran']['sha256'],r'^[0-9a-f]{64}$')
        self.assertIn('motocarro',e['definiciones']['pasajeros_motocarro'])
        roles=self.tablas['h3_usuarios']
        self.assertEqual(roles[['heridos','fallecidos','total']].values.tolist(),
                         [[332,129,461],[51,22,73],[1,4,5],[671,114,785]])
        self.assertEqual(roles.sum().tolist(),[1055,269,1324])

    def test_subgrupo_por_rol_mes_y_cotejo_dos_fuentes(self):
        control=self.tablas['h3_cotejo_roles']
        self.assertEqual(len(control),60)
        self.assertEqual(len(control[['mes','rol']].drop_duplicates()),60)
        self.assertTrue(control[['heridos_resto','fallecidos_resto']].ge(0).all().all())
        self.assertEqual(control[['heridos_resto','fallecidos_resto']].sum().tolist(),[671,114])
        peatones=control.loc[control.rol.eq('peatones'),['heridos_resto','fallecidos_resto']].sum()
        ciclistas=control.loc[control.rol.eq('ciclistas'),['heridos_resto','fallecidos_resto']].sum()
        self.assertEqual(peatones.tolist(),[47,28])
        self.assertEqual(ciclistas.tolist(),[2,4])

    def test_historia_reproduce_rr_or_y_z_fase2(self):
        a=self.contrastes.iloc[0]
        self.assertAlmostEqual(a.RR,(155/539)/(114/785),places=14)
        self.assertAlmostEqual(a.OR,155*671/(384*114),places=14)
        self.assertAlmostEqual(a.p_Z_unilateral/1.2712438129521372e-10,1.,places=10)
        np.testing.assert_allclose(a.ic95_RR,[1.5962369324197536,2.4565076551125835],atol=1e-13)
        np.testing.assert_allclose(a.ic95_OR,[1.809298593757778,3.119794870123816],atol=1e-13)

    def test_sensibilidad_excluye_cinco_sin_transferirlos(self):
        a,b=self.contrastes.iloc[0],self.contrastes.iloc[1]
        self.assertEqual([b.n_grupo,b.n_resto,b.n_analisis,b.excluidos_motocarro],[534,785,1319,5])
        self.assertEqual([a.fallecidos_grupo-b.fallecidos_grupo,a.heridos_grupo-b.heridos_grupo],[4,1])
        self.assertEqual([b.fallecidos_resto,b.heridos_resto],[114,671])
        self.assertAlmostEqual(b.RR,(151/534)/(114/785))
        self.assertGreater(b.ic95_RR[0],1)

    def test_pruebas_sobre_cuatro_celdas_y_multiplicidad(self):
        for r in self.contrastes.itertuples():
            tabla=[[r.fallecidos_grupo,r.heridos_grupo],[r.fallecidos_resto,r.heridos_resto]]
            self.assertEqual(r.p_Fisher_unilateral,stats.fisher_exact(tabla,alternative='greater').pvalue)
            self.assertEqual(r.p_Fisher_bilateral,stats.fisher_exact(tabla,alternative='two-sided').pvalue)
            self.assertAlmostEqual(r.p_bonferroni_6,6*r.p_Fisher_unilateral)
            self.assertLess(r.p_bonferroni_6,.05)
        m=self.tablas['multiplicidad_actual']
        self.assertEqual(len(m),6)
        np.testing.assert_allclose(m.p_bonferroni_6,np.minimum(1,6*m.p_crudo),atol=0,rtol=0)
        self.assertFalse(bool(m.iloc[0].rechazo_005))
        self.assertEqual(self.tablas['h4_ordinal'].loc['Corregido edad conocida','p'],1.656775033883798e-20)

    def test_rechaza_fuente_alterada_y_cotejo_incompatible(self):
        mensual=self.tablas['vehicular_mensual'].copy()
        mensual.loc[0,'heridos_12_2_10']+=1
        with self.assertRaisesRegex(ValueError,'Diferencia entre INE y DINATRAN'):
            auditar_h3(mensual)
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);(base/'data').mkdir()
            e=json.loads((ROOT/'data/referencia_h3_dinatran_2021.json').read_text(encoding='utf-8'))
            e['periodo']=2020
            (base/'data/referencia_h3_dinatran_2021.json').write_text(json.dumps(e),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'2021'):
                auditar_h3(self.tablas['vehicular_mensual'],base)
        for vals in [(0,384,114,671),(-1,384,114,671),(155.5,384,114,671)]:
            with self.assertRaises(ValueError):contraste_h3(*vals)

    def test_notebook_publica_evidencia_y_modelo_nacional_sin_vehiculo(self):
        r=leer_resultados()
        for nombre in ['h3_contrastes','h3_usuarios','h3_cotejo_roles','multiplicidad_actual']:
            pd.testing.assert_frame_equal(r['tablas'][nombre],self.tablas[nombre],check_dtype=False,atol=1e-14)
        self.assertEqual(r['metadatos']['variables'],['sexo','grupo_edad'])
        self.assertIn('534',r['conclusiones'])
        self.assertIn('DINATRAN',r['contexto']['interpretacion_h3'])
        self.assertIn('no se estima riesgo poblacional',r['contexto']['conclusion_integral'])
        import pymupdf
        with ZipFile(ROOT/'docs/fase3/Informe_Fase3.docx') as z:
            xml=ET.fromstring(z.read('word/document.xml'))
            word=''.join(xml.itertext())
            self.assertIn('TOC',word)
        with pymupdf.open(ROOT/'docs/fase3/Informe_Fase3.pdf') as pdf:
            self.assertEqual(len(pdf),15)
            texto=''.join(p.get_text() for p in pdf)
        for nombre in ['DINATRAN','534','539','785','motocarro','1,9472','2,3206','0,069847']:
            self.assertIn(nombre,word)
            self.assertIn(nombre,texto)


if __name__=='__main__':unittest.main()
