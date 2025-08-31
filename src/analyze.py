import os, glob, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk; nltk.download('vader_lexicon', quiet=True)
from .utils import logger
from .viz import plot_time_series_memory_smart

def load_curated(curated_root="data/curated") -> pd.DataFrame:
    files = glob.glob(os.path.join(curated_root, "**/*.parquet"), recursive=True)
    if not files: return pd.DataFrame()
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df

def text_to_features(df: pd.DataFrame):
    vect = TfidfVectorizer(lowercase=True, min_df=3, max_df=0.9, ngram_range=(1,2), strip_accents="unicode")
    X = vect.fit_transform(df["content"].fillna(""))
    svd = TruncatedSVD(n_components=min(128, X.shape[1]-1))
    X_red = svd.fit_transform(X)
    sid = SentimentIntensityAnalyzer()
    s = df["content"].fillna("").map(lambda t: sid.polarity_scores(t)["compound"]).to_numpy().reshape(-1,1)
    eng = df[["like_count","retweet_count","reply_count","quote_count"]].fillna(0).to_numpy()
    eng = StandardScaler().fit_transform(eng)
    comp = 0.55*StandardScaler().fit_transform(s) + 0.35*StandardScaler().fit_transform(eng.mean(axis=1).reshape(-1,1)) + 0.10*StandardScaler().fit_transform(X_red[:,0].reshape(-1,1))
    return {"signal": comp.ravel()}

def aggregate_signal(df: pd.DataFrame, sig: np.ndarray, freq="5min"):
    s = pd.Series(sig, index=df["timestamp"]).sort_index()
    agg = s.resample(freq).mean().to_frame("signal_mean")
    count = df.set_index("timestamp").resample(freq)["id"].count()
    std = s.groupby(pd.Grouper(freq=freq)).std()
    agg["n"] = count
    agg["stderr"] = (std / np.sqrt(np.maximum(1, count))).fillna(0)
    return agg.dropna()

def run():
    df = load_curated()
    if df.empty:
        logger.warning("No curated data found.")
        return
    feats = text_to_features(df)
    agg = aggregate_signal(df, feats["signal"], freq="5min")
    out_csv = "data/curated/signal_5min.csv"
    agg.to_csv(out_csv)
    logger.info(f"Signal saved → {out_csv}")
    plot_time_series_memory_smart(series=agg["signal_mean"], title="Composite Tweet Signal (5-min mean)", path="data/curated/signal_plot.png")
    logger.info("Plots saved.")

if __name__ == "__main__":
    run()
