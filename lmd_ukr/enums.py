from enum import Enum


class Css(Enum):
    # search html selectors
    S_IS_RESULT = "p.search__no-result"
    S_RIVER = "a.river__pagination"
    S_PAGES = "a.river__pagination.river__pagination--page-search"
    S_URL = "a.teaser__link"
    S_TITLE = "h3.teaser__title"

    # article html selectors
    A_TITLE = "h1.article__title"
    A_DESC = "p.article__desc"
    A_METADATA = "script"
    A_CONTENT = "p.article__paragraph "

    # comments html selectors
    C_IS_COMMENT = "h3.comments__title"
    C_COUNT = "h3.comments__title"
    C_RIVER = "ul.pagination__list"
    C_PAGES = "a.pagination__link"
    C_AUTHOR = "span.comment__author"
    C_CONTENT = "p.comment__content"
