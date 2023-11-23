import argparse
import pandas as pd
from typing import Union, List, Tuple


def read_file(filename: str) -> Union[pd.DataFrame, None]:
    data = None
    try:
        if filename.endswith("csv"):
            data = pd.read_csv(filename)
        if filename.endswith("xlsx"):
            data = pd.read_excel(filename)
        data = data.dropna().reset_index(drop = True)
    except Exception as E:
        print(f"[ERROR] - {E}")
    return data

def clean_result(result: str) -> List[str]:
    return result.split(": ")[-1].replace('[','').replace(']', '').replace('"', '').split(", ")

def parse_result(result: str) -> Tuple[List[str], List[str], List[str]]:
    aspect, entity, sentiment = [], [], []
    try:
        tokenize = [res for res in result.split("\n") if res != ""]
        entity_raw = clean_result(tokenize[0])
        if len(entity_raw) >= 1 and entity_raw[0] != "":
            entity.extend(entity_raw)
        aspect_raw = clean_result(tokenize[1])
        if len(aspect_raw) >= 1 and aspect_raw[0] != "":
            for asp_sen in aspect_raw: 
                try:
                    asp, sen = asp_sen.split("(")
                    sen = sen.replace(")", "")
                    aspect.append(asp.strip())
                    sentiment.append(sen.strip())
                except ValueError as E:
                    pass 
    except AttributeError as E:
        print(f"[ERROR] - {E}")
        print(result)
    # print(f"[ENTITY]: {entity} - [ASPECT]: {aspect} - [SENTIMENT]: {sentiment}")
    return aspect, entity, sentiment

def main():

    parser = argparse.ArgumentParser(
        description = "Read and ELT .csv file using pandas"
    )
    parser.add_argument("--filename", help = "Name of .csv file based on extracted dataset", required = True)
    args = parser.parse_args()
    filename = args.filename 

    path = "dataset/data_clean.csv"
    data = read_file(filename = filename)
    aspects, entities, sentiments = [], [], []
    for result in data['result extraction']:
        aspect, entity, sentiment = parse_result(result = result)
        aspects.append(",".join(aspect))
        entities.append(",".join(entity))
        sentiments.append(",".join(sentiment))

    data["entity"] = entities
    data["aspect"] = aspects
    data["sentiment"] = sentiments

    data.to_csv(path, index = False)
    print(f'[INFO] - Save File into {path}')

if __name__ == "__main__":
    """
    Usage: 
        python src/extract_enrichment.py --filename dataset/data_twitter_pemilu_2024_enrich.csv
    """
    main()