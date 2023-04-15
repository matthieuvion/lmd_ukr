from pathlib import Path
import json
import logging
import sqlite3
from sqlite3 import Error

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


"""

Create db.ukr (sqlite), create tables articles and comments,
Populate with previously api-crawled-saved, json files

"""


def create_connection(db_file):
    """create a database connection to a SQLite database
    Create db if does not exist
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def create_table(conn, sql_create_table):
    """create a table from sql statement"""
    try:
        c = conn.cursor()
        c.execute(sql_create_table)
    except Error as e:
        print(e)


def parse_article(article: dict) -> tuple:
    """Format a dict article to feed a tuple of n values into db"""
    return (
        article["article_id"],
        article["url"],
        article["title"],
        article["content"],
        article["date"],
        str(article["keywords"]),
        article["article_type"],
        article["allow_comments"],
    )


def parse_comments(comments: dict) -> list[tuple]:
    """Convert / parse dict comments into [n*(flattened comments values)]
    we will iterate before inserting into db
    """
    list_comms = []
    if comments["count"] > 0:
        for comm in comments["comments"]:
            list_comms.append(
                (
                    comments["article_id"],
                    comm["author"],
                    comm["content"],
                )
            )
        return list_comms
    else:
        return [(comments["article_id"], "None", "None")]


def create_article(conn, article: tuple):
    """Insert properly formatted article into db, row by row"""

    sql = """INSERT OR IGNORE INTO articles (
        article_id,
        url,
        title,
        content,
        date,
        keywords,
        article_type,
        allow_comments,
        premium
        ) VALUES(?,?,?,?,?,?,?,?,?)"""
    cur = conn.cursor()
    cur.execute(sql, article)
    conn.commit()
    return cur.lastrowid


def create_batch_comments(conn, list_comments: list[tuple]) -> None:
    """Insert properly formated comments into db
    Contrary to articles (+- 3k) we're having more than 250k comments
    Insertion is batch-wise, using executemany()
    """

    cur = conn.cursor()
    sql = """INSERT OR IGNORE INTO comments (
        article_id,
        author,
        comment
        ) VALUES(?,?,?)"""
    cur.executemany(sql, list_comments)
    conn.commit()


def main():
    database = r"ukr.db"

    path_articles = Path("articles_ukraine")
    articles_json = [article for article in path_articles.glob("*.json")]

    path_comments = Path("comments_ukraine")
    comments_json = [comment for comment in path_comments.glob("*.json")]

    """
    Sql queries to create articles & comments tables
    Note that column article_id (defined as a foreign key) exists in both
    """

    sql_create_articles_table = """CREATE TABLE IF NOT EXISTS articles (
        article_id integer PRIMARY KEY,
        url text,
        title text,
        content text,
        date text,
        keywords text,
        article_type text,
        allow_comments text,
        premium text
        );"""

    sql_create_comments_table = """CREATE TABLE IF NOT EXISTS comments (
        article_id integer,
        author text,
        comment text,
        FOREIGN KEY (article_id) REFERENCES articles (article_id)
        );"""

    # load json articles and comments

    # create db, create tables articles & comments
    conn = create_connection(database)

    with conn:
        create_table(conn, sql_create_articles_table)
        create_table(conn, sql_create_comments_table)

        # insert articles into according table
        for index, file in enumerate(articles_json):
            with open(file, "r") as f:
                article_dict = json.load(f)
                article = parse_article(article_dict)
                logging.info(
                    f"inserting article, id: {article[0]} {index}/{len(articles_json)}"
                )
                create_article(conn, article)

        # insert comments (batch per batch) into according table
        for index, file in enumerate(comments_json):
            with open(file, "r") as f:
                comments_dict = json.load(f)
                list_comments = parse_comments(comments_dict)
                create_batch_comments(conn, list_comments)
                logging.info(
                    f"inserting batch of {len(list_comments)} comments from article {index}/{len(comments_json)}"
                )
    conn.close()


if __name__ == "main__":
    main()
