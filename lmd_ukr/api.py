import re
import json
import unicodedata
import urllib.parse
from dataclasses import dataclass, asdict

import httpx
from selectolax.parser import HTMLParser

from .enums import Selectors


@dataclass
class Article:
    article_id: int
    url: str
    title: str
    type_article: str
    keywords: list[str]
    content: str


@dataclass
class Comment:
    article_id: int
    url: str
    author: str
    content: str


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
        """Build client with custom headers, from personal tokens (abonné)"""

        if self.lmd_m and self.lmd_s:
            self.headers = Api.headers
            self.headers["cookie"] = Api.cookie.format(
                lmd_sso_twipe=f"%7B%22token%22%3A%22{self.lmd_m}%22%7D",
                lmd_s=self.lmd_s,
            )
            self.client = httpx.Client(headers=self.headers)
        else:
            raise ValueError('cookies abonné "lmd_m" et "lmd_s" nécessaires')

    def __exit__(self):
        self.client.close()

    def _fetch(self, url):
        res = self.client.get(url)
        html = HTMLParser(res.text)
        return html

    def search(self, query: str, start: str, end: str, **kwargs) -> list(dict):
        """
        Args
        -------
        query: str, e.g. "ukraine" or "guerre ukraine"
        start, end: str, "dd/mm/yyyy"

        Optional
        -------
        search_sort: optional["dateCreated_desc (default)", "dateCreated_asc, relevance_desc"]
        max_pages: optional(int) else we get all results pages
        """
        search_parameters = {"search_keywords": query, "start_at": start, "end_at": end}

        max_pages = kwargs.get("max_pages", 1)
        url = Api.searchUrl + urllib.parse.urlencode(search_parameters)
        print(f"Search url: {url}")

        # get result page
        html = self._fetch(url)
        isResult = True if not html.css_first(Selectors.S_IS_RESULT.value) else False

        # is result?, is several pages ?, n of pages
        if isResult:
            river = True if html.css(Selectors.S_RIVER.value) else False
            n_pages = int(html.css(Selectors.S_PAGES.value)[-1].text()) if river else 1
            max_pages = (
                kwargs.get("max_pages", n_pages) if max_pages <= n_pages else n_pages
            )
            print(f" # result pages: {n_pages}, # pages crawled : {max_pages}")

            # parse urls, titles
            page = 1
            results = []
            while page <= max_pages:
                html = self._fetch(f"{url}&page={page}")
                urls = [
                    url.attributes["href"] for url in html.css(Selectors.S_URL.value)
                ]
                titles = [title.text() for title in html.css(Selectors.S_TITLE.value)]
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

    def filter_search(self, urls: list(str), tag: str) -> list(str):
        """Narrow down a list of urls : keep articles containing a given tag"""

        filtered_search = []
        for url in urls:
            html = self._fetch(url)
            metadata = html.css_first("script").text()
            metadata = json.loads(re.search("({.+})", metadata).group(0))
            tags = metadata["analytics"]["smart_tag"]["tags"]["keywords"]
            filtered_search.append(url) if tag in tags else None

        return filtered_search

    def get_article(self, client, url: str) -> dict:
        """Parse article"""

        def get_metadata(html):
            """Extract metadada: id, keywords etc. from an article"""
            metadata = html.css_first(Selectors.A_METADATA.value).text()
            metadata = json.loads(re.search("({.+})", metadata).group(0))
            article_id = metadata["analytics"]["smart_tag"]["customObject"][
                "ID_Article"
            ]
            allow_comments = metadata["context"]["article"]["parsedMetadata"]["huit"][
                "allowComments"
            ]
            keywords = metadata["analytics"]["smart_tag"]["tags"]["keywords"]
            date = metadata["context"]["article"]["firstPublished"]["date"]
            type_article = metadata["analytics"]["smart_tag"]["customObject"]

            return metadata

        html = self._fetch(url)
        title = html.css_first(Selectors.A_TITLE.value).text()
        title = unicodedata.normalize("NFKD", "".join(title))
        desc = html.css_first(Selectors.A_DESC.value).text()
        content = [node.text() for node in html.css(Selectors.A_CONTENT.value)]
        content = unicodedata.normalize("NFKD", " ".join(content))
        metadata = get_metadata(html)

        article = Article(url=url, title="", keywords="", content="")

        return article

    def get_comments(self, Article, url: str) -> list(dict):
        """Parse comments from article"""
        return
