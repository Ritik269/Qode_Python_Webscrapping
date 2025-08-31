import os, glob, gzip, json, re, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
from .utils import logger, normalize_hashtags
from dateutil import parser

MENTION_RE = re.compile(r"@([A-Za-z0-9_]{1,15})")

def clean_record(obj: dict) -> dict:
    content = obj.get("content", "") or ""
    hashtags = normalize_hashtags(" ".join(["#"+h for h in (obj.get("hashtags") or [])]) + " " + content)
    mentions = list(set(MENTION_RE.findall(content)))
    return {
        "id": str(obj.get("id")),
        "username": obj.get("user", {}).get("username", ""),
        "user_id": str(obj.get("user", {}).get("id") or ""),
        "timestamp": parser.isoparse(obj.get("date")),
        "content": content,
        "like_count": int(obj.get("likeCount") or 0),
        "retweet_count": int(obj.get("retweetCount") or 0),
        "reply_count": int(obj.get("replyCount") or 0),
        "quote_count": int(obj.get("quoteCount") or 0),
        "mentions": mentions,
        "hashtags": hashtags,
        "url": obj.get("url"),
    }

def load_raw_to_df(raw_dir: str) -> pd.DataFrame:
    rows = []
    for path in glob.glob(os.path.join(raw_dir, "*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                    rows.append(clean_record(obj))
                except Exception:
                    continue
    df = pd.DataFrame(rows)
    if df.empty: return df
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df

def write_parquet_partitioned(df: pd.DataFrame, out_root: str):
    if df.empty:
        logger.warning("No rows to write.")
        return
    df["dt"] = df["timestamp"].dt.date.astype(str)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_to_dataset(table, root_path=out_root, partition_cols=["dt"], existing_data_behavior="overwrite_or_ignore")
    logger.info(f"Wrote {len(df)} rows → {out_root} (partitioned by dt)")

def run():
    latest_batch = sorted(Path("data/raw").glob("*"))[-1]
    df = load_raw_to_df(str(latest_batch))
    logger.info(f"Loaded {len(df)} cleaned rows from {latest_batch}")
    write_parquet_partitioned(df, "data/curated")

if __name__ == "__main__":
    run()
