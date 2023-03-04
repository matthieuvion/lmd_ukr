import os
import requests
import re
import json
import unicodedata
import urllib.parse
from dataclasses import dataclass, asdict

import httpx
from selectolax.parser import HTMLParser
from dotenv import load_dotenv


@dataclass
class Article:
    url: str
    title: str
    keywords: list[str]
    content: str


@dataclass
class Search:
    index: int
    url: str
    title: str


class Api:
    """Le Monde (abonnés), search articles and extract content"""

    baseUrl = "https://www.lemonde.fr"
    searchUrl = "https://www.lemonde.fr/recherche/?"

    cookie = "lmd_sso_twipe={lmd_sso_twipe}; lmd_a_s={lmd_s}; lmd_a_sp={lmd_s}; lmd_stay_connected=1; lmd_a_m={lmd_m}; lmd_a_c=1; uid_dm=f8bb6ded-ea6d-42fd-6eb0-ae4eb62eb552; xtvrn=$43260$; xtan43260=-; xtant43260=1; kw.session_ts=1677086760394; kw.pv_session=4"
    headers = {
        "authority": "www.lemonde.fr",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "cookie": None,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    }

    def __init__(self, lmd_m=None, lmd_s=None):
        self.lmd_m = lmd_m
        self.lmd_s = lmd_s
        self._login()

    def _login(self):
        """Build custom headers, with personal tokens (abonné)"""

        if self.lmd_m and self.lmd_s:
            self.headers = Api.headers
            self.headers["cookie"] = Api.cookie.format(
                lmd_sso_twipe=f"%7B%22token%22%3A%22{self.lmd_m}%22%7D",
                lmd_s=self.lmd_s,
            )
        else:
            raise ValueError('cookies abonné "lmd_m" et "lmd_s" nécessaires')

    def search(self, query: str, start: str, end: str, **kwargs) -> list(dict):
        """
        Search

        Args
        -------
        query: str, e.g. "ukraine" or "guerre ukraine"
        start, end: str, "dd/mm/yyyy"

        Optional
        -------
        search_sort: optional["dateCreated_desc (default)", "dateCreated_asc, relevance_desc"]
        max_pages: int, default is max number of results pages
        """
        search_parameters = {"search_keywords": query, "start_at": start, "end_at": end}

        max_pages = kwargs.get("max_pages", 1)
        url = Api.searchUrl + urllib.parse.urlencode(search_parameters)
        print(f"Search url: {url}")

        with httpx.Client(headers=self.headers) as client:

            # get result page
            res = client.get(url)
            html = HTMLParser(res.text)
            isResult = True if not html.css_first("p.search__no-result") else False

            # isResult?, n of pages
            if isResult:
                river = True if html.css("a.river__pagination") else False
                n_pages = (
                    int(
                        html.css("a.river__pagination.river__pagination--page-search")[
                            -1
                        ].text()
                    )
                    if river
                    else 1
                )
                max_pages = (
                    kwargs.get("max_pages", n_pages)
                    if max_pages <= n_pages
                    else n_pages
                )
                print(f" # result pages: {n_pages}, # pages crawled : {max_pages}")

                # parse urls, titles
                page = 1
                results = []
                while page <= max_pages:
                    res = client.get(f"{url}&page={page}")
                    html = HTMLParser(res.text)
                    urls = [
                        url.attributes["href"] for url in html.css("a.teaser__link")
                    ]
                    titles = [title.text() for title in html.css("h3.teaser__title")]
                    result = [
                        {"url": a_url, "title": a_title}
                        for a_url, a_title in zip(urls, titles)
                    ]

                    print(f" Crawling page: {page}")
                    results.extend(result)
                    page += 1
            else:
                raise Exception("No Result found")
            return results

    def parse_article():
        """Parse article metadata"""
        return

    def parse_comments():
        """Parse comments from article"""
        return
