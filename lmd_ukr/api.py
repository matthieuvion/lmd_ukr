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


class Api:
    """Navigate Search, Articles, extract content"""

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

    @dataclass
    class Article:
        url: str
        title: str
        keywords: list[str]
        content: str

    def __init__(self, lmd_m=None, lmd_s=None):
        self.lmd_m = lmd_m
        self.lmd_s = lmd_s
        self._login()
        self.httpxclient = None

    def _login(self):
        """Build custom headers, with personal tokens (abonné)"""

        if self.lmd_m and self.lmd_s:
            self.headers = Api.headers
            self.headers["cookie"] = Api.cookie.format(
                lmd_sso_twipe=f"%7B%22token%22%3A%22{self.lmd_m}%22%7D",
                lmd_s=self.lmd_s,
            )
        else:
            raise ValueError("cookies abonné lmd_m et lmd_s nécessaires")

    def search(self, keywords, start, end, **kwargs):
        """Return index, titles and urls"""

        return keywords

    def parseArticle():
        """Parse article metadata"""
        return

    def parseComments():
        """Parse comments from article"""
        return
