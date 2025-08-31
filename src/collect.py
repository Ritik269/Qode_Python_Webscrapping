# src/collect.py

import tweepy
import json
import logging
from datetime import datetime, timedelta

# --------------------------
# Configure logging
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# --------------------------
# User Configuration
# --------------------------
BEARER_TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

TAGS = ["#nifty50", "#stockmarket", "#finance"]  # Hashtags to scrape
WINDOW_MINUTES = 60  # Window size
NUM_WINDOWS = 3      # Number of windows
LIMIT_PER_WINDOW = 100  # Max tweets per window per tag

# --------------------------
# Initialize Twitter Client
# --------------------------
client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)

# --------------------------
# Functions
# --------------------------
def scrape_hashtag(tag, start_time, end_time, limit=100):
    """
    Scrape tweets for a given hashtag using Tweepy Client.
    Returns a list of dictionaries.
    """
    tweets_list = []
    query = f"{tag} -is:retweet lang:en"  # Ignore retweets, only English

    try:
        paginator = tweepy.Paginator(
            client.search_recent_tweets,
            query=query,
            start_time=start_time.isoformat() + "Z",
            end_time=end_time.isoformat() + "Z",
            tweet_fields=["created_at", "author_id", "text"],
            max_results=100
        )
        count = 0
        for page in paginator:
            if page.data:
                for tweet in page.data:
                    tweets_list.append({
                        "id": tweet.id,
                        "date": tweet.created_at.isoformat(),
                        "author_id": tweet.author_id,
                        "content": tweet.text
                    })
                    count += 1
                    if count >= limit:
                        break
            if count >= limit:
                break

        logging.info(f"Scraped {len(tweets_list)} tweets for {tag} from {start_time} to {end_time}")
    except Exception as e:
        logging.error(f"Error scraping {tag} from {start_time} to {end_time}: {e}")

    return tweets_list


def collect_windows(tags, window_minutes=60, num_windows=1, limit_per_window=100):
    """
    Collect tweets across multiple windows and hashtags.
    """
    all_tweets = []
    now = datetime.utcnow()
    logging.info(f"Collecting {len(tags)} tags across {num_windows} windows ({window_minutes} minutes each)")

    for w in range(num_windows):
        end_time = now - timedelta(minutes=window_minutes * w)
        start_time = end_time - timedelta(minutes=window_minutes)
        logging.info(f"Window {w+1}: {start_time.isoformat()} to {end_time.isoformat()}")

        for tag in tags:
            tweets = scrape_hashtag(tag, start_time, end_time, limit=limit_per_window)
            all_tweets.extend(tweets)

    logging.info(f"Total tweets collected: {len(all_tweets)}")
    return all_tweets

# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    results = collect_windows(
        tags=TAGS,
        window_minutes=WINDOW_MINUTES,
        num_windows=NUM_WINDOWS,
        limit_per_window=LIMIT_PER_WINDOW
    )

    output_file = "tweets.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logging.info(f"Tweets saved to {output_file}")
