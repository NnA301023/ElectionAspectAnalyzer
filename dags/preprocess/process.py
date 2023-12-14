import os
import re
import pandas as pd
from tqdm import tqdm
from enrich import (
    TopicGenerator, HoaxDetection, 
    AspectDetection, KeywordExtraction
)
tqdm.pandas()
pd.set_option("display.max_columns", None)


def clean_text(text, min_length=3):
    try:
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^a-zA-Z0-9.\s]', '', text)
        text = ' '.join(word for word in text.split() if len(word) >= min_length)
    except Exception as E:
        print(f'[ERROR] - {E}')
        print(text)
    return text


def integration(folder):
    dataset = []
    column_used = {
        "news": ["keyword", "publish_date", "publisher", "content"], 
        "twitter": ["created_at", "username", "full_text"]
    }
    column_normalization = ["keyword", "timestamp", "author", "content"]
    for fname in os.listdir(folder):
        filename = os.path.join(folder, fname)
        source = fname.split("_")[0]
        column_required = column_used[source]
        df = pd.read_csv(filename, usecols=column_required)
        if len(df.columns) != len(column_normalization):
            keywords = " ".join(fname.split(".")[0].split("_")[1:]).title()
            keywords = [keywords] * len(df)
            df = df[column_required]
            df.insert(0, column_normalization[0], keywords)
        else:
            df = df[column_required]
        df.columns = column_normalization
        df.insert(0, 'source', source)
        dataset.append(df)
    data = pd.concat(dataset)
    data = data.dropna().reset_index(drop=True)
    return data


if __name__ == "__main__":
    """
    Usage
        ~/ElectionAspectAnalyzer/dags >>> python process.py
    """

    result_data = integration("../crawler/final_dataset")
    result_data['clean_content'] = result_data['content'].progress_apply(clean_text)

    # Hoax Detection
    # hoax = HoaxDetection()
    # list_hoax = hoax.batch_inference(result_data['clean_content'].tolist())
    # result_data['hoax_extract'] = list_hoax

    # Keyword Extraction
    # kw_extract = KeywordExtraction()
    # result_data['keyword_extract'] = result_data['clean_content'].progress_apply(
    #     lambda i: ", ".join(kw_extract.single_inference(i))
    # )

    # Topic generation
    topic_gen = TopicGenerator()
    result_data['topic_extract'] = result_data['clean_content'].progress_apply(
        lambda i: ", ".join(topic_gen.generate_topic(i))
    )

    # Sentiment Extraction
    # ...

    result_data.to_csv("final_dataset/clean_data.csv", index=False)