import openai
import pandas as pd
import streamlit as st 
from src.secret import OPENAI_KEY
from typing import Tuple, List, Dict
from streamlit_agraph import agraph, Node, Edge, Config
openai.api_key = OPENAI_KEY
st.set_page_config(layout = "wide")

@st.cache
def load_clean_data(dataset: str = "dataset/result.csv") -> pd.DataFrame: 
    data = pd.read_csv(dataset)
    data = data.drop_duplicates(subset=['keyword', 'author', 'topic'])
    data['keyword'] = data["keyword"].replace("Mahfud Md", "Mahfud MD")
    data = data.sample(500).reset_index(drop=True)
    return data

@st.cache
def create_graph(data_filter: pd.DataFrame, use_sentiment_aspect: bool = False, mapping_sentiment: Dict[str, str] = {
    "positive" : "#B3FFAE", "negative" : "#FF7D7D", "neutral" : "#F8FFDB"
    }) -> Tuple[List[str], List[str]]:
    # aspect_global = []
    # nodes, edges = [], []
    # candidates, organizations = [], []
    # for _, i in data_filter.iterrows():
    #     candidate_name = i['name']
    #     organization = i['entity']
    #     if organization != "" and isinstance(organization, str):
    #         for person in organization.split(","):
    #             if candidate_name not in candidates:
    #                 nodes.append(Node(id = candidate_name, label = candidate_name, symbolType = "diamond", color = "#FFF6F6", size = 20))
    #                 candidates.append(candidate_name)
    #             if person not in organizations and person not in candidates and person not in aspect_global:
    #                 nodes.append(Node(id = person, label = person, color = "#A7D397", size = 15))
    #                 organizations.append(person)
    #             edges.append(Edge(source = person, target = candidate_name))
    #         if use_sentiment_aspect:
    #             sentiments = i['sentiment']
    #             aspects    = i['aspect']
    #             if aspects != "" and isinstance(aspects, str):
    #                 for aspect, sentiment in zip(aspects.split(","), sentiments.split(",")):
    #                     if aspect not in aspect_global and aspect not in organizations and aspect not in candidates:
    #                         # print(f'[ASPECT] - {aspect} is not available in, orgs: {aspect not in organizations} asp: {aspect not in aspect_global}')
    #                         nodes.append(Node(id = aspect, label = aspect, size = 10, color = mapping_sentiment.get(sentiment)))
    #                         edges.append(Edge(source = aspect, target = person, label = sentiment))
    #                         aspect_global.append(aspect)
    aspect_global = []
    nodes, edges = [], []
    candidates, authors = [], []
    for _, i in data_filter.iterrows():
        candidate = i['keyword']
        author = i['author']
        if author != "" and isinstance(author, str):
            if candidate not in candidates:
                nodes.append(Node(id = candidate, label = candidate, symbolType = "diamond", color = "#FFF6F6", size = 25))
                candidates.append(candidate)
            elif author not in authors:
                nodes.append(Node(id = author, label = author, symbolType = "diamond", color = "#A7D397", size = 15))
                authors.append(author)
            # elif author in authors and candidate in candidates:
            edges.append(Edge(source = author, target = candidate))
        if use_sentiment_aspect:
            sentiment = i['sentiment'] 
            aspect = i['topic']
            if aspect != "" and isinstance(aspect, str) and aspect not in aspect_global:
                nodes.append(Node(id = aspect, label = aspect, size = 10, color = mapping_sentiment.get(sentiment)))
                edges.append(Edge(source = aspect, target = author, label = sentiment))
                aspect_global.append(aspect)
    return nodes, edges 

def prompt_qa(data: pd.DataFrame, query: str) -> str: 
    prompt = \
    f"""
    data = {data.sample(10).to_dict('records')}

    jawaban pertanyaan berikut berdasarkan informasi diatas yang diolah sesuai reasoning yang masuk akal.
    pertanyaan: Siapa Pemenang pemilu 2024?
    jawaban: Ganjar Pranowo
    
    pertanyaan: {query}

    dengan format dibawah:
    jawaban:
    """
    return prompt


def agent_qa_zero_shot(data: pd.DataFrame, query: str, model_base: str = "gpt-3.5-turbo"):
    token_usage = 0
    response_extraction = ""
    try:
        response = openai.ChatCompletion.create(
            model = model_base, 
            messages = [{"role" : "user", "content" : prompt_qa(data, query)}], 
            temperature = 0.5, max_tokens = 512, top_p = 1.0, 
            frequency_penalty = 0.0, presence_penalty = 0.0
        )
        response_extraction = response["choices"][0]["message"]["content"]
        token_usage = response["usage"]["total_tokens"]
    except Exception as E:
        print(f"[ERROR] - {E}")
        print("Retry with Recursive Func")
        agent_qa_zero_shot(data, query)
    return response_extraction, token_usage

    
def app(data: pd.DataFrame, config: Config):

    # Interface section
    st.sidebar.header("ElectionAspectAnalyzer v.0.1")

    # Sidebar section
    candidates = data["keyword"].unique().tolist()
    filter_candidate = st.sidebar.multiselect(
        "Select Candidates:", 
        options = candidates, 
        default = candidates[:3]
    )
    filter_data = data[data['keyword'].isin(filter_candidate)].reset_index(drop = True)
    use_aspect_sentiment = st.sidebar.checkbox("Use Aspect-Sentiment")

    # Graph section
    with st.spinner("Preprocess Data..."): 
        filter_node, filter_edge = create_graph(filter_data, use_sentiment_aspect = use_aspect_sentiment)
        st.success("Total Nodes Loaded: " + str(len(filter_node)))
    return_value = agraph(
        nodes = filter_node, 
        edges = filter_edge, 
        config = config
    )

    # QnA section
    # NOTE: Reduce token usage OpenAI Cost :)
    data_sample = pd.concat([df.sample(5) for _, df in filter_data.groupby("keyword")])
    query = st.sidebar.text_input(label = "Any Question about Election 2024?")
    if query != "":
        response, _ = agent_qa_zero_shot(data = data_sample, query = query)
        st.sidebar.success(response)

if __name__ == "__main__":
    config = Config(
        width = 1000, height = 500, 
        directed = True, physics = True, hierarchical = False
    )
    data = load_clean_data()
    app(data = data, config = config)