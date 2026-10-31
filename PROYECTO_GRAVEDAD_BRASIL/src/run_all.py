"""Reproduce resultados. No redescarga ni reevalua prueba si ya esta registrada."""
from common import RAW, OUT, DATA
from preparar import prepare
from fase1 import main as fase1
from fase2 import main as fase2
from modelado import fit_and_freeze, evaluate_once
from graficos_modelos import main as plots


def main():
    if not (DATA/'victimas_modelado.joblib').exists():
        if not (RAW/'pessoas_2017.zip').exists():
            from descargar_fuentes import main as descargar
            descargar()
        prepare()
    fase1();fase2();fit_and_freeze();evaluate_once();plots()
    print('Tablas, figuras y modelos listos. python src/entregables.py genera notebooks/HTML; python src/informes_pdf.py genera PDF con reportlab.')


if __name__=='__main__':main()
