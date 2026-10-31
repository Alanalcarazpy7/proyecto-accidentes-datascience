"""Reproduce preparacion, fases y resultados registrados; ajuste completo opcional."""
import argparse
from common import ROOT,RAW,OUT


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reentrenar',action='store_true');args=ap.parse_args()
    if not (RAW/'pessoas_2017.zip').exists():
        from descargar_fuentes import main as descargar
        descargar()
    from preparar import prepare,original_dictionary
    prepare(force=True);original_dictionary()
    from fase1 import main as fase1
    from fase2 import main as fase2
    fase1();fase2()
    if args.reentrenar:
        from comparacion import fit_and_freeze,evaluate_once,OUT as INITIAL_OUT
        fit_and_freeze(force=True)
        (INITIAL_OUT/'fase3_resultados.json').unlink(missing_ok=True)
        evaluate_once()
    from modelado import main as fase3
    fase3(reentrenar=args.reentrenar)
    from graficos import main as graficos
    graficos()
    print('Resultados reproducidos. python src/notebooks.py ejecuta los notebooks; python src/informes.py genera los PDF.')


if __name__=='__main__':main()
