import requests
import pandas as pd
from tqdm import tqdm
from gnews import GNews
from bs4 import BeautifulSoup
from datetime import timedelta, date
from newspaper import Config, Article
from urllib.parse import unquote, urlparse


# Instantiate object
config = Config()
config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

def parsing_rss_url(rss_url):
    parse_url = None
    try:
        resp = requests.get(rss_url)
        soup = BeautifulSoup(resp.content, "html.parser")
        links = soup.find_all("link")
        for link in links:
            link = link.get("href")
            # TODO: Implement proper logic.
            try:
                if "embed" in link:
                    parse_url = unquote(urlparse(link).query.split("=")[1])
                    break
                if "amp" in link:
                    parse_url = unquote(link)
            except Exception as E:
                print(f"Error Occurede, Required Improve Link Parser: {links}")
    except Exception as E:
        print(f"Connection Broken with Error: {E}")
    return parse_url

# NOTE: This solution is generated based on @alearjun comment on Gnews Issue.
def crawling_news(keyword, start_date=date(2023, 1, 1), total_news=1000):
    list_url = []
    list_title = []
    list_article = []
    list_authors = []
    list_publisher = []
    list_description = []
    list_published_date = []
    n_news = 0
    google_news = GNews(language="id", country="ID")
    while n_news < total_news:
        scope_date = start_date + timedelta(days = 8)
        google_news.start_date = (start_date.year, start_date.month, start_date.day)
        google_news.end_date = (scope_date.year, scope_date.month, scope_date.day)
        results = google_news.get_news(keyword)
        for res in results:
            print(f'Total News: {n_news}')
            url = res['url']
            url = parsing_rss_url(url)
            if url is None:
                continue
            try:
                article = Article(url, config=config)
                article.download()
                article.parse()
            except Exception:
                pass
            if n_news >= total_news:
                break
            if (
                url in list_url or 
                article is None or 
                len(article.text.strip()) == 0
            ):
                continue
            else:
                list_url.append(url)
                list_title.append(res['title'])
                list_article.append(article.text)
                list_authors.append(", ".join(article.authors))
                list_publisher.append(res['publisher']['title'])
                list_description.append(res['description'])
                list_published_date.append(res['published date'])
                n_news += 1
        start_date += timedelta(days = 7)
    return (
        list_url, list_title, list_article,
        list_authors, list_publisher, list_description,
        list_published_date
    )

if __name__ == "__main__":

    # Define List of keywords 
    list_keywords = [
        #"Anies Baswedan", 
        "Muhaimin Iskandar",
        "Ganjar Pranowo", "Mahfud MD",
        "Prabowo Subianto", "Gibran Rakabuming"
    ]
    for keyword in tqdm(list_keywords, desc="Crawling Google News..."):
        keywords = []
        urls, titles, contents, authors, publisher, description, publish_date = [], [], [], [], [], [], []
        (
            list_url, list_title, list_article,
            list_authors, list_publisher, 
            list_description, list_published_date
        ) = crawling_news(keyword=keyword)
        urls.extend(list_url)
        titles.extend(list_title)
        contents.extend(list_article)
        authors.extend(list_authors)
        publisher.extend(list_publisher)
        description.extend(list_description)
        publish_date.extend(list_published_date)
        keywords.extend([keyword] * len(list_url))
    
        # Check dimension
        print(
            len(urls), len(titles), len(contents), len(authors), 
            len(publisher), len(description), len(publish_date)
        )

        # Save into csv
        df = pd.DataFrame({
            "keyword": keywords,
            "url": urls,
            "title": titles,
            "content": contents,
            "author": authors,
            "publisher": publisher,
            "description": description,
            "publish_date": publish_date
        })
        df.to_csv(f"result_news_{keyword.replace(' ', '_')}.csv", index=False)