"""Reconstruye las tres fases. Ejecutar desde cualquier directorio con Python."""
import argparse
import importlib.metadata
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

from common import ROOT,OUT,save_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-notebooks',action='store_true')
    parser.add_argument('--sin-pdf',action='store_true')
    parser.add_argument('--pdf-python',default=None,help='Python con reportlab, si difiere del de analisis')
    args=parser.parse_args()
    from data_prep import main as prepare
    from phase1 import main as phase1
    from phase2 import main as phase2
    from phase3 import main as phase3
    prepare();phase1();phase2();phase3()
    versions={}
    for package in ['numpy','pandas','scipy','statsmodels','scikit-learn','matplotlib','openpyxl','pypdf','joblib','nbformat','nbclient','nbconvert']:
        versions[package]=importlib.metadata.version(package)
    save_json('entorno.json',dict(python=platform.python_version(),plataforma=platform.platform(),paquetes=versions))
    if not args.sin_notebooks:
        from build_notebooks import generate,execute
        execute(generate())
    if not args.sin_pdf:
        pdf_python=args.pdf_python or sys.executable
        if args.pdf_python is None and importlib.util.find_spec('reportlab') is None:
            bundled=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            if bundled.exists():pdf_python=str(bundled)
        subprocess.run([pdf_python,'-X','utf8',str(ROOT/'src/pdf_reports.py')],check=True)
    from verify import main as verify
    verify(check_notebooks=not args.sin_notebooks,check_pdf=not args.sin_pdf)
    print('Tres fases reproducidas. Informes en output/reports; notebooks en notebooks.')


if __name__=='__main__':main()
