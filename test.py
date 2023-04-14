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

    # Sscriber's personal cookies stored locally in .env file
    # Init Api / logged-in httpx client
    load_dotenv()
    lmd_m, lmd_s = (
        os.environ["lmd_m"],
        os.environ["lmd_s"],
    )

    api = Api(lmd_m=lmd_m, lmd_s=lmd_s)
    logging.info(f"api: {api}")

    """
    Search (-> object)
    ------
    """

    # Search lemonde.fr/recherche? ; here returns first page only
    search = api.search(
        query="grève", start="05/03/2023", end="08/03/2023", max_pages=1
    )

    logging.info(
        f"Query: {search.query}, Is result: {search.is_result}, # urls retrieved: {search.retrieved}"
    )
    pprint(search, depth=1)
    pprint(asdict(search), depth=1)

    """
    Article (-> object)
    -------
    """

    #  Get Article, for more flexibility our input param is an url
    url = search.results[0]["url"]
    article = api.get_article(url)

    logging.info(f"Retrieved Article with attr. : {article.__dict__.keys()}")
    pprint(f"Article id: {article.article_id}")

    """
    Comments (-> object)
    --------
    """

    # Get article's comments, this time our input param in an Article object
    coms = api.get_comments(article)
    logging.info(f"Retrieved Comments with attr.: {coms.__dict__.keys()}")
    pprint(f"Comments for article {coms.article_id}: {coms}")


if __name__ == "__main__":
    main()
