import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from dataclasses import asdict
import json
import time
import random

from joblib import Memory
from functools import lru_cache
from pyrate_limiter import Duration, Limiter, RequestRate
import httpx
import backoff

from lmd_ukr import Api
from lmd_ukr.api import Article

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)

"""
Rate limiting, caching & backoff policies
"""

# Rate limits cf. doc pyrate limiter
rate_limits = (
    RequestRate(25, Duration.MINUTE),  # 20 requests per minute
    RequestRate(1000, Duration.HOUR),  # 1000 requests per hour
)
limiter = Limiter(*rate_limits)


# Disk caching
cache_location = "./data/cache"
memory = Memory(cache_location, verbose=0)

# Load suscriber's credentials
load_dotenv()
lmd_m, lmd_s = (
    os.environ["lmd_m"],
    os.environ["lmd_s"],
)


@lru_cache(maxsize=1)
def unique_api():
    """Cache trick to ensure we only have one, unique, httpx client instance, for caching.
    Cached fetch (api.get_comments, function being outside ou main() should ne enough, though.
    """
    return Api(lmd_m=lmd_m, lmd_s=lmd_s)


@memory.cache
@backoff.on_exception(backoff.expo, httpx.HTTPError, max_time=10, max_tries=3)
@limiter.ratelimit("article", delay=True)
def cached_get_comments(api, article):
    time.sleep(random.uniform(0.4, 0.6))
    res = api.get_comments(article)
    return res


"""
Get Comments
"""


def main(start: int, end: int):
    """Read previously fetched Articles (json) and get associated comments
    Continuous save to disk as json
    """

    def load_articles():
        """load articles (json files), return as list of objects Articles()"""
        parent_path = Path("data/articles_ukraine")
        filenames = [
            file.name
            for file in parent_path.iterdir()
            if file.name.startswith("article")
        ]
        all_articles = []
        for file in filenames:
            f = open(f"data/articles_ukraine/{file}")
            data = json.load(f)
            object = Article(**data)
            all_articles.append(object)
        return all_articles

    def to_filename(start, end, idx):
        """path + start/end indexes to filename"""
        return f"data/comments_batch_{start}_to_{end}_url_idx_{idx}.json"

    articles = load_articles()
    logging.info(f"loaded {len(articles)} articles")

    # (optional) make sure unique API instance (httpx client) is created, for caching
    api = unique_api()

    # Gather Comments, save to disk
    for idx, article in enumerate(articles[start:end]):
        logging.info(f" call: {idx}, url: {article.url}")
        comments = cached_get_comments(api, article)
        logging.info(f" {comments.count} comments collected")

        filename = to_filename(start, end, idx)
        with open(filename, "w") as outfile:
            json.dump(asdict(comments), outfile)


if __name__ == "__main__":
    start = 3000
    end = 3120
    main(start, end)
