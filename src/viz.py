import numpy as np, matplotlib.pyplot as plt, pandas as pd
from .utils import logger

def _adaptive_sample(x: np.ndarray, y: np.ndarray, max_points: int = 12000):
    n = len(x)
    if n <= max_points: return x, y
    stride = max(1, n // (max_points // 2))
    xs = x[::stride]
    yv = y.reshape(-1,1)
    ya = yv[: len(xs)*stride].reshape(-1, stride)
    ymin = ya.min(axis=1).ravel()
    ymax = ya.max(axis=1).ravel()
    X = np.repeat(xs, 2)
    Y = np.column_stack([ymin, ymax]).ravel(order="C")
    return X, Y

def plot_time_series_memory_smart(series: pd.Series, title: str, path: str):
    s = series.dropna()
    x = s.index.view("i8").to_numpy()
    y = s.to_numpy(dtype=float)
    X, Y = _adaptive_sample(x, y, max_points=12000)
    plt.figure(figsize=(11, 4.0))
    plt.plot(pd.to_datetime(X), Y, linewidth=0.8)
    plt.title(title)
    plt.xlabel("Time"); plt.ylabel("Signal")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    logger.info(f"Saved plot → {path}")
