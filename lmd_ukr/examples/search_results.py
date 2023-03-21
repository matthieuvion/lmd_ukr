import os
from dotenv import load_dotenv
import logging
from dataclasses import asdict
from datetime import datetime
import json
import time
import random

from lmd_ukr import Api

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


def main(query, start, end):

    # Load suscriber's credentials
    load_dotenv()
    lmd_m, lmd_s = (
        os.environ["lmd_m"],
        os.environ["lmd_s"],
    )

    def to_filename(query, start, end):
        """path + date to filename"""
        s, e = datetime.strptime(start, "%d/%m/%Y"), datetime.strptime(end, "%d/%m/%Y")
        return f"data/results_{query}_{s.day:02}{s.month:02}_{e.day:02}{e.month:02}_{s.year}.json"

    api = Api(lmd_m=lmd_m, lmd_s=lmd_s)
    logging.info(f"api: {api}")

    search = api.search(query=query, start=start, end=end)
    logging.info(f"number of pages: {search.pages}, retrieved {search.retrieved} urls")
    filename = to_filename(query, start, end)

    with open(filename, "w") as outfile:
        json.dump(asdict(search), outfile)


if __name__ == "__main__":
    # start war = 24/02/2022
    query = "macron"
    start = "22/02/2023"
    end = "28/02/2023"
    main(query, start, end)
