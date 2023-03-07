import os
from dotenv import load_dotenv
import logging
from pprint import pprint
from dataclasses import asdict

from lmd_ukr import Api

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


def main(**kwargs):

    """
    Login
    """

    # Suscriber's personal cookies stored locally in a .env file
    # Init Api / logged-in httpx client
    load_dotenv()
    lmd_m, lmd_s = (
        os.environ["lmd_m"],
        os.environ["lmd_s"],
    )

    api = Api(lmd_m=lmd_m, lmd_s=lmd_s)
    logging.info(f"Logged-in httpx client: {api}")

    # Search, here returns first page only
    search = api.search(
        query="macron", start="06/03/2023", end="07/03/2023", max_pages=1
    )
    logging.info(f"Search done, first 2 results:\n {search[0:2]}")

    """
    Get article
    """

    # Returns an object Article
    url = search[0]["url"]
    a = api.get_article(url)

    # Access article properties and/or as a Dict
    logging.info(f"Article id: {a.article_id}\n Article title: {a.title}")
    logging.info(f"Article dictionary:\n, {pprint(asdict(a), depth=1)}")

    """
    Get article's comments
    """
    comments = 


if __name__ == "__main__":
    main()
