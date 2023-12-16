import pandas as pd
from tqdm import tqdm
from random import choice
pd.set_option("display.max_columns", None)


list_sentiment = ['positive', 'negative', 'neutral']
list_validity = ['fake', 'real']

data = pd.read_csv("final_dataset/clean_data.csv")

source, keyword, timestamp, author, content, topic = [], [], [], [], [], []
for i, row in tqdm(data.iterrows()):
    _source = row['source']
    _keyword = row['keyword']
    _timestamp = row['timestamp']
    _author = row['author']
    _content = row['clean_content']
    topics = row['topic_extract']
    if isinstance(topics, float):
        continue
    topics = topics.split(", ")

    for _topic in topics:
        source.append(_source)
        keyword.append(_keyword)
        timestamp.append(_timestamp)
        author.append(_author)
        content.append(_content)
        topic.append(_topic)

data_final = pd.DataFrame({
    "source": source,
    "keyword": keyword,
    "timestamp": timestamp,
    "author": author,
    "content": content,
    "topic": topic
})

data_final['timestamp'] = pd.to_datetime(data_final['timestamp'])
data_final['timestamp'] = data_final['timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")
data_final['timestamp'] = pd.to_datetime(data_final['timestamp'], format="%Y-%m-%d %H:%M:%S")
data_final['sentiment'] = list(map(lambda _: choice(list_sentiment), range(len(data_final))))
data_final['source_validity'] = list(map(lambda _: choice(list_validity), range(len(data_final))))
data_final.to_csv("final_dataset/result.csv", index=False)