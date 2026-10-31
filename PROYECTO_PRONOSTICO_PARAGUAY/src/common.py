"""Utilidades compartidas: rutas relativas, semillas y salidas legibles."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
PROTOCOL = json.loads((ROOT / 'protocolo.json').read_text(encoding='utf-8'))
SEED = PROTOCOL['semilla']
MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
TYPES = ['choque', 'roce', 'vuelco', 'arrollamiento', 'incendio', 'casual', 'atropellamiento']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titlelocation': 'left', 'figure.dpi': 110})


def serializable(value):
    if isinstance(value, dict):
        return {str(k): serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    if isinstance(value, np.ndarray):
        return serializable(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    return value


def save_json(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serializable(value), ensure_ascii=False, indent=2,
                               allow_nan=False), encoding='utf-8')
    return path


def save_table(name, frame):
    path = OUT / 'tables' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding='utf-8-sig')
    return path


def save_figure(name, fig):
    path = OUT / 'figures' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def load_series():
    frame = pd.read_csv(ROOT / 'data/processed/serie_mensual.csv', parse_dates=['fecha'])
    return frame.set_index('fecha').sort_index()


def development():
    return load_series().loc['2016-01-01':'2022-12-01'].copy()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protocol_hash():
    return sha256(ROOT / 'protocolo.json')
