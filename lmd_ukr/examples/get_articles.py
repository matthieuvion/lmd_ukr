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

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)

"""
Rate limiting, caching & backoff policies
"""

# Rate limits cf. doc pyrate limiter
rate_limits = (
    RequestRate(25, Duration.MINUTE),  # 25 requests per minute
    RequestRate(1200, Duration.HOUR),  # 1200 requests per hour
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
    Cached fetch (api.get_article, function being outside ou main() should be enough, though.
    """
    return Api(lmd_m=lmd_m, lmd_s=lmd_s)


@memory.cache
@backoff.on_exception(backoff.expo, httpx.HTTPError, max_time=10, max_tries=3)
@limiter.ratelimit("article", delay=True)
def cached_get_article(api, url):
    time.sleep(random.uniform(0.4, 0.6))
    res = api.get_article(url)
    return res


"""
Get Articles
"""


def main(tag: str, start: int, end: int):
    """
    Fetch articles from urls[index_start:index_end]
    Save to disk as json, if given "tag" in article.keywords
    """

    def load_search_results():
        """load search results (json files), return urls
        Use case here : Search results previously saved as json file
        """
        parent_path = Path("data/results_ukraine")
        filenames = [
            file.name
            for file in parent_path.iterdir()
            if file.name.startswith("results")
        ]
        all_urls = []
        for file in filenames:
            f = open(f"data/results_ukraine/{file}")
            data = json.load(f)
            urls = [result["url"] for result in data["results"]]
            all_urls.extend(urls)
        return all_urls

    def to_filename(start, end, idx):
        """path + start/end indexes to filename"""
        return f"data/article_batch_{start}_to_{end}_url_idx_{idx}.json"

    urls = load_search_results()
    logging.info(f"loaded {len(urls)} urls")

    # (optional) make sure unique API instance (httpx client) is created, for caching
    api = unique_api()
    logging.info(f"api: {api}, api: {api}")

    # Gather Articles content (batch of x articles), save to disk
    for idx, url in enumerate(urls[start:end]):
        logging.info(f" call: {idx}, url: {url}")
        # blog urls not supported
        if api._type_url(url) == "article":
            article = cached_get_article(api, url)

            # check if Article keywords contains "ukraine"
            filename = to_filename(start, end, idx)
            if tag in article.keywords:
                # save to disk as json
                with open(filename, "w") as outfile:
                    json.dump(asdict(article), outfile)


if __name__ == "__main__":
    tag = "ukraine"
    start = 0
    end = 200
    main(tag, start, end)
