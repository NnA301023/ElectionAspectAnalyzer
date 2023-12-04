import pandas as pd
from tqdm import tqdm
from gnews import GNews
from datetime import timedelta, date


# Instantiate object
google_news = GNews(language="id", country="ID")

# NOTE: This solution is generated based on @alearjun comment on Gnews Issue.
_end_date = date(2023, 11, 30)
_start_date = date(2023, 1, 1)
def crawling_news(keyword, start_date=_start_date, end_date=_end_date):
    list_url = []
    list_title = []
    list_article = []
    list_authors = []
    list_publisher = []
    list_description = []
    list_published_date = []
    while start_date <= end_date:
        scope_date = start_date + timedelta(days = 7)
        google_news.start_date = (start_date.year, start_date.month, start_date.day)
        google_news.end_date = (scope_date.year, scope_date.month, scope_date.day)
        google_news.period = "7d" # Period of 1 Day
        results = google_news.get_news(keyword)
        for res in results:
            url = res['url']
            article = google_news.get_full_article(url)
            if url in list_url:
                continue
            else:
                list_url.append(url)
                list_title.append(res['title'])
                list_article.append(article.text)
                list_authors.append(", ".join(article.authors))
                list_publisher.append(res['publisher']['title'])
                list_description.append(res['description'])
                list_published_date.append(res['published date'])
        start_date += timedelta(days = 7)
    return (
        list_url, list_title, list_article,
        list_authors, list_publisher, list_description,
        list_published_date
    )

if __name__ == "__main__":

    # Define List of keywords 
    list_keywords = [
        "Anies Baswedan", "Muhaimin Iskandar",
        "Ganjar Pranowo", "Mahfud MD",
        "Prabowo Subianto", "Gibran Rakabuming"
    ]
    keywords = []
    urls, titles, contents, authors, publisher, description, publish_date = [], [], [], [], [], [], []
    for keyword in tqdm(list_keywords, desc="Crawling Google News..."):
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