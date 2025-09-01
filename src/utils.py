import os, sys, gzip, logging, subprocess, json, pathlib
from datetime import datetime, timezone
import snscrape.modules.twitter as sntwitter
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

LOG_PATH = "logs/app.log"
os.makedirs("logs", exist_ok=True)

def setup_logger():
    logger = logging.getLogger("market-intel")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_PATH)
    ch = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logger()

def jsonl_gz_writer(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return gzip.open(path, "at", encoding="utf-8")   # text mode

def write_jsonl_gz(file, obj: dict):
    file.write(json.dumps(obj, ensure_ascii=False) + "\n")

def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(1, 8))
def snscrape_search(query: str, limit: int = 100):
    """
    Scrape tweets using snscrape's Python API.
    Uses Bearer token + cookies.json (auth_token, ct0, etc.) to bypass restrictions.
    Returns list of JSON strings (1 per tweet).
    """
    tweets = []
    try:
        scraper = sntwitter.TwitterSearchScraper(query)

        # Inject Bearer token into session headers
        BEARER_TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
        scraper._session.headers.update({
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "User-Agent": "Mozilla/5.0",
        })

        # Load cookies.json (auth_token, ct0, etc.)
        cookies_path = pathlib.Path("cookies.json")
        if cookies_path.exists():
            try:
                with open(cookies_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                jar = {}
                for c in cookies:
                    if c.get("name") in ["auth_token", "ct0", "gt", "_twitter_sess"]:
                        jar[c["name"]] = c["value"]
                if jar:
                    scraper._session.cookies.update(jar)
                    logger.info(f"Loaded {len(jar)} Twitter auth cookies")
                else:
                    logger.warning("cookies.json found but no auth cookies inside!")
            except Exception as ce:
                logger.warning(f"Failed to load cookies.json: {ce}")

        # Collect tweets
        for i, tweet in enumerate(scraper.get_items()):
            if i >= limit:
                break
            tweets.append(json.dumps(tweet.__dict__, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise
    return tweets

def chunk_timerange(start_iso, end_iso, minutes=60):
    from dateutil import parser, rrule
    s, e = parser.isoparse(start_iso), parser.isoparse(end_iso)
    times = list(rrule.rrule(rrule.MINUTELY, interval=minutes, dtstart=s, until=e))
    for a, b in zip(times[:-1], times[1:]):
        yield a.isoformat(), b.isoformat()

def normalize_hashtags(s: str) -> list[str]:
    return list({x.lstrip("#").lower() for x in s.split() if x.startswith("#")})
