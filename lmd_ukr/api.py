from dataclasses import dataclass
import re
import json
import unicodedata
import random
import time
import urllib.parse

import httpx
from selectolax.parser import HTMLParser


from .enums import Css


@dataclass
class Search:
    query: str
    url: str
    is_result: bool
    pages: int
    retrieved: int
    results: list


@dataclass
class Article:
    url: str
    title: str
    desc: str
    content: str
    article_id: int
    date: str
    keywords: list[str]
    article_type: str
    allow_comments: bool
    premium: bool


@dataclass
class Comments:
    article_id: int
    count: int
    comments: list


class Api:
    """Le Monde (suscriber/abonnés), search articles and extract content
    Untested if not a suscriber, but should work with minor adaptations (i.e. rework headers)
    Rate limits:
    ------------
    Do exist but obv. not documented. Being too harsh can lead to an temporary (at least?) IP ban of +- 45mn
    E.g. Endpoint./recherche?  keep < 40 requests/mn
    """

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

    def __init__(self, lmd_m: str = None, lmd_s: str = None):
        self.lmd_m = lmd_m
        self.lmd_s = lmd_s
        self._login()

    def __repr__(self):
        return f"Logged in client: {self.client}"

    def __exit__(self):
        self.client.close()

    def _login(self):
        """Build httpx client with custom headers, from personal tokens (abonné)"""

        if self.lmd_m and self.lmd_s:
            self.headers = Api.headers
            self.headers["cookie"] = Api.cookie.format(
                lmd_sso_twipe=f"%7B%22token%22%3A%22{self.lmd_m}%22%7D",
                lmd_s=self.lmd_s,
                lmd_m=self.lmd_m,
            )
            self.client = httpx.Client(headers=self.headers, timeout=10)
        else:
            raise ValueError('cookies abonné "lmd_m" et "lmd_s" nécessaires')

    def _fetch(self, url):
        """Main method used to fetch url + parse html at once
        You should apply (your own) rate limits and/or caching in your main()
        """
        res = self.client.get(url)
        html = HTMLParser(res.text)
        time.sleep(random.uniform(0.6, 0.9))
        return html

    def get_css_first(self, html, selector) -> list | None:
        """Error Catching for HTMLParser .css_first & .text() methods
        Mainly used in get_article() to catch non "standard" article
        """
        try:
            return html.css_first(selector).text()
        except AttributeError as e:
            print(f"{e}, (attribute {selector} is missing)")
            return None

    def get_css(self, html, selector) -> str | None:
        """Error Catching for HTMLParser .css & .text() methods
        Mainly used in get_article() to catch non "standard" article
        """
        try:
            return [node.text() for node in html.css(selector)]
        except AttributeError as e:
            print(f"{e}, (attribute(s) {selector} are missing)")
            return None

    def _clean(self, string) -> str | None:
        """Util :remove white spaces / special char from content string"""
        string = unicodedata.normalize("NFKD", string) if string else None
        return " ".join(string.split()) if string else None

    def search(self, query: str, start: str, end: str, **kwargs) -> type[Search]:
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
        search_parameters["search_sort"] = kwargs.get(
            "dateCreated_desc", "dateCreated_desc"
        )
        max_pages = kwargs.get("max_pages", 1)

        url = f"{Api.searchUrl}{urllib.parse.urlencode(search_parameters)}"

        # get result page
        html = self._fetch(url)
        is_result = True if not html.css_first(Css.S_IS_RESULT.value) else False

        # is result?, is several pages ? (river)
        if is_result:
            river = True if html.css(Css.S_RIVER.value) else False
            n_pages = int(html.css(Css.S_PAGES.value)[-1].text()) if river else 1
            max_pages = (
                kwargs.get("max_pages", n_pages) if max_pages <= n_pages else n_pages
            )

            # parse urls, titles
            page = 1
            results = []
            while page <= max_pages:
                print(f"page:{page}/{max_pages}")
                html = self._fetch(f"{url}&page={page}")
                urls = [url.attributes["href"] for url in html.css(Css.S_URL.value)]
                titles = [title.text() for title in html.css(Css.S_TITLE.value)]
                result = [
                    {"url": a_url, "title": a_title}
                    for a_url, a_title in zip(urls, titles)
                ]

                results.extend(result)
                page += 1
        else:
            raise Exception("No Result found")
        return Search(
            query=query,
            url=url,
            is_result=is_result,
            pages=n_pages,
            retrieved=len(results) if results else 0,
            results=results,
        )

    def get_metadata(self, html, filter_by: str | None = None) -> dict:
        """
        Retrieve metadada from article's html
        Optional:
        ---------
        "filter_by" = "your_tag" : check if a given tag in metadata keywords (exact match)
        """
        # tag = kwargs.get("filter_by", False)
        tag = filter_by
        html_meta = html.css_first(Css.A_METADATA.value).text()
        dict_meta = (
            json.loads(re.search("({.+})", html_meta).group(0)) if html_meta else None
        )
        meta = {
            "article_id": dict_meta["analytics"]["smart_tag"]["customObject"][
                "ID_Article"
            ],
            "date": dict_meta["context"]["article"]["firstPublished"]["date"],
            "keywords": dict_meta["analytics"]["smart_tag"]["tags"]["keywords"],
            "article_type": dict_meta["analytics"]["smart_tag"]["customObject"][
                "Nature_edito"
            ],
            # "parsedMetadata" does not exist for Live "article"
            "allow_comments": dict_meta["context"]["article"]["parsedMetadata"]["huit"][
                "allowComments"
            ]
            if dict_meta["context"]["article"].get("parsedMetadata", False)
            else False,
            "suscribe": dict_meta["analytics"]["smart_tag"]["customObject"][
                "Statut_article"
            ],
        }
        if tag:
            meta["tags_contain"] = {
                "tag": tag,
                "is_tag": True if tag in meta["keywords"] else False,
            }
        return meta

    def get_article(self, url: str, **kwargs) -> type[Article]:
        """
        Parse article, given a (valid) article url
        "Live" urls are not fully supported (do not throws error but incomplete)
        Optional:
        ---------
        """
        html = self._fetch(url)
        title = self._clean(self.get_css_first(html, selector=Css.A_TITLE.value))
        desc = self._clean(self.get_css_first(html, selector=Css.A_DESC.value))
        content = " ".join(
            [self._clean(node.text()) for node in html.css(Css.A_CONTENT.value)]
        )
        meta = self.get_metadata(html)
        return Article(
            url=url,
            title=title,
            desc=desc,
            content=content,
            article_id=meta["article_id"],
            date=meta["date"],
            keywords=meta["keywords"],
            article_type=meta["article_type"],
            allow_comments=meta["allow_comments"],
            premium=True if meta["suscribe"] == "Abo" else False,
        )

    def get_comments(self, article: type[Article]) -> type[Comments]:
        """Parse comments, given a previously crawled Article()"""

        url = f"{article.url}?contributions"
        html = self._fetch(url)

        if article.allow_comments:
            is_comment = (
                True
                if self.get_css_first(html, selector=Css.C_IS_COMMENT.value)
                else False
            )
            if is_comment:
                river = True if html.css(Css.C_RIVER.value) else False
                count_str = html.css_first(Css.C_COUNT.value).text()
                count = int("".join(list(filter(str.isdigit, count_str))))
                n_pages = int(html.css(Css.C_PAGES.value)[-1].text()) if river else 1

                # parse coms authors, contents
                page = 1
                all_comments = []
                while page <= n_pages:
                    html = self._fetch(f"{url}&page={page}")
                    authors = [author.text() for author in html.css(Css.C_AUTHOR.value)]
                    contents = [
                        self._clean(content.text())
                        for content in html.css(Css.C_CONTENT.value)
                    ]
                    comments = [
                        {"author": author, "content": content}
                        for author, content in zip(authors, contents)
                    ]
                    all_comments.extend(comments)
                    page += 1

                return Comments(
                    article_id=article.article_id,
                    count=count if is_comment else 0,
                    comments=all_comments if is_comment else [None],
                )
            else:
                return Comments(article_id=article.article_id, count=0, comments=[None])
        else:
            return Comments(article_id=article.article_id, count=0, comments=[None])
