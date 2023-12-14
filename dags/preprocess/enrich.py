import re
import pandas as pd
from tqdm import tqdm
from keybert import KeyBERT
from typing import List, Tuple
from nltk.corpus import stopwords
from warnings import filterwarnings
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
filterwarnings("ignore")


class TopicGenerator:
    def __init__(self, corpus_path: str = "corpus/taxo.xlsx"):
        self.corpus_path = corpus_path
        taxonomy_general = self._load_taxonomy("General ID")
        taxonomy_specific = self._load_taxonomy("Government ID")
        self.attr_noun = pd.concat([taxonomy_specific, taxonomy_general])

    def _load_taxonomy(self, sheet_name: str) -> pd.DataFrame:
        required_columns = ['category', 'attr_noun']
        normalize_columns = ['category', 'attr_noun']
        return self._process_corpus(sheet_name, required_columns, normalize_columns)

    def _process_corpus(self, sheet_name: str, required_columns: List[str], normalize_columns: List[str]) -> pd.DataFrame:
        data = pd.read_excel(self.corpus_path, usecols=required_columns, sheet_name=sheet_name)
        data.columns = normalize_columns
        return data.dropna().drop_duplicates().reset_index(drop=True)

    @staticmethod
    def _apply_regex(phrase: List[str]) -> str:
        return r"\b(?:" + "|".join(map(re.escape, phrase)) + r")\b"

    @staticmethod
    def _process_term(list_term: List[str]) -> Tuple[List[str], List[str]]:
        single_term, phrase_term = [], []
        for word in list_term:
            try:
                if word == "":
                    continue
                if len(word.split()) == 1:
                    single_term.append(word)
                else:
                    phrase_term.append(word)
            except AttributeError:
                continue
        return single_term, phrase_term

    def generate_topic(self, content: str) -> List[str]:
        attr_noun_single, attr_noun_phrase = self._process_term(self.attr_noun['attr_noun'])
        attr_noun_single = self.attr_noun[self.attr_noun['attr_noun'].isin(attr_noun_single)].reset_index(drop=True)
        attr_noun_phrase = self.attr_noun[self.attr_noun['attr_noun'].isin(attr_noun_phrase)].reset_index(drop=True)
        regex_noun_phrase = self._apply_regex(attr_noun_phrase['attr_noun'].str.lower().tolist())
        regex_noun_single = self._apply_regex(attr_noun_single['attr_noun'].str.lower().tolist())
        list_noun_phrase = attr_noun_phrase['attr_noun'].str.lower().tolist()
        list_noun_single = attr_noun_single['attr_noun'].str.lower().tolist()

        content = content.lower()
        aspect_term, aspect_category = [], []
        phrase_noun = re.findall(regex_noun_phrase, content)
        single_noun = re.findall(regex_noun_single, content)
        if phrase_noun:
            for phrase in phrase_noun:
                for word in phrase.split():
                    if word in single_noun:
                        single_noun.remove(word)
                if phrase not in aspect_term:
                    aspect_term.append(phrase)
                    aspect_category.append(attr_noun_phrase['category'][list_noun_phrase.index(phrase)])
        if single_noun:
            for word in single_noun:
                if word not in aspect_term:
                    aspect_term.append(word)
                    aspect_category.append(attr_noun_single['category'][list_noun_single.index(word)])

        aspect_category = list(set(aspect_category))
        return aspect_category
    

class AspectDetection:

    def __init__(self, model="mdhugol/indonesia-bert-sentiment-classification", task = "text-classification"):
        tokenizer = AutoTokenizer.from_pretrained(model)
        finetune_model = AutoModelForSequenceClassification.from_pretrained(model)
        self.pipe = pipeline(task, model=finetune_model, tokenizer=tokenizer)
        self.label_index = {'LABEL_0': 'positif', 'LABEL_1': 'netral', 'LABEL_2': 'negatif'}

    def preprocess(self, content, aspect_category):
        return f'[CLS] {content} [ASP] {aspect_category} [ASP]'

    def single_inference(self, content, aspect_category):
        results = self.pipe(self.preprocess(content, aspect_category))
        results = list(map(lambda i: self.label_index[i['label']], results))
        return results


class HoaxDetection:

    def __init__(self, model="khavitidala/xlmroberta-large-fine-tuned-indo-hoax-classification", task = "text-classification"):
        self.pipe = pipeline(task, model=model, max_length=512, truncation=True)

    def batch_inference(self, contents):
        results = []
        for content in tqdm(contents):
            result = self.pipe(content)
            res = list(map(lambda i: i['label'], result))
            results.extend(res)
        return results
    
class KeywordExtraction:
    
    def __init__(self):
        self.extract = KeyBERT(model="indobenchmark/indobert-base-p1")
        stop_words = list(set(stopwords.words('indonesian')))
        data = 'https://raw.githubusercontent.com/Braincore-id/IndoTWEEST/main/stopwords_twitter.csv'
        df_stopwords = pd.read_csv(data, names=['stopword'])
        stop_words = stop_words + df_stopwords['stopword'].unique().tolist()
        self.stopwords = list(set(stop_words))

    def single_inference(self, content):
        result = self.extract.extract_keywords(
            content, keyphrase_ngram_range = (1, 1), 
            stop_words=self.stopwords
        )
        result = list(map(lambda i: i[0], result))
        return result



if __name__ == "__main__":

    """
    Aspect Category | Aspect Sentiment | Keywords (top 5) | Hoax Classification
    """
    # Define example content
    content = "VIVA Politik Anies Baswedan akan kembali melakukan safari politik seluruh Tanah Air. Akhir Januari 2023 ini Anies akan mengunjungi NTB. Beberapa wilayah Pulau Lombok dan Sumbawa telah disiapkan. Bakal calon presiden yang diusung Partai NasDem Anies Baswedan dijadwalkan akan mengunjungi Nusa Tenggara Barat pada 3031 Januari 2023 mendatang. Agendanya satu hari Pulau Lombok dan satu hari Pulau Sumbawa kata Ketua Panitia yang juga Ketua DPD Partai NasDem Lombok Timur Rumaksi Kantor DPW Partai NasDem NTB Kota Mataram Jumat dikutip dari Antara. mengatakan dalam kunjungannya NTB Anies Baswedan dijadwalkan akan bertemu dengan sejumlah tokoh agama tokoh masyarakat pemuda dan relawan dari lintas agama baik yang ada Pulau Lombok dan Pulau Sumbawa. Selain bertemu dengan tokoh lintas agama dan relawan. Anies Baswedan juga akan mengunjungi Desa Wisata Sade Lombok Tengah. Kemudian juga Pondok Pesantren Yatofa Bodak Lombok Tengah. Ponpes Yatofa Pak Anies akan bersilaturahmi dan melakukan pengajian bersama pimpinan pondok pesantren dan masyarakat ujarnya. Setelah itu dilanjutkan dengan mengunjungi peternak sapi Desa Wanaseba Kabupaten Lombok Timur. Tidak hanya itu bakal calon presiden Partai NasDem itu juga akan melaksanakan shalat berjemaah Masjid Jamik Masbagik Lombok Timur. Setelah dari Masjid Masbagik Pak Anies akan diarak pakai kuda menuju Lapangan Gotong Royong Masbagik. Pak Anies akan mengukuhkan pengurus ranting Partai Nasdem sePulau Lombok. Dari situ melanjutkan perjalanan Lombok Barat untuk silaturahmi dengan tokoh agama lintas agama bersama Bupati Lombok Barat selaku Ketua Dewan Pakar Partai NasDem terang Rumaksi. Kemudian pada Januari Anies Baswedan akan terbang Pulau Sumbawa. Pulau Sumbawa Anies Baswedan akan mengunjungi Kota Bima. Setelah itu akan bergerak menuju Kabupaten Sumbawa. Jadi kegiatan Pulau Sumbawa juga sama dengan yang ada Lombok ucapnya didampingi anggota DPR dapil NTB dari Fraksi Partai NasDem Syamsul Luthfi Ketua DPD NasDem Lombok Tengah Syamsul Hadi Ketua DPD NasDem Lombok Barat Tarmizi dan Ketua DPD NasDem Kota Bima Muthmainnah. Menurut dia panitia daerah siap mengawal kunjungan mantan Gubernur DKI Jakarta tersebut selama mengunjungi NTB bahkan DPW Partai NasDem memastikan bahwa kedatangan bakal calon presiden Anies Baswedan NTB akan berjalan aman dan kondusif. Karena itu pihaknya mempersilakan bagi siapapun khususnya tim relawan untuk melakukan komunikasi dengan DPW Partai NasDem terkait rencana kedatangan Anies Baswedan NTB. Khusus saat pertemuan Ponpes Yatofa akan ada kejutan yang disampaikan. Cuma apa kejutan itu nanti disampaikan saat Pak Anies Baswedan datang NTB katanya. Ant"

    # Example usage of TopicGenerator class
    generator = TopicGenerator()
    topics = generator.generate_topic(content)
    print(topics)
    # >>> ['Community', 'Institution', 'Public Figure', 'Leader', 'Transportation', 'Networking', 'Activities', 'Spokesperson', 'Social Media', 'Product Launch', 'Public Rally', 'Volunteer', 'Public Opinion', 'Election', 'Tourism', 'Geographical', 'Political Parties']

    # Example usage of HoaxDetection class
    hoax_detection = HoaxDetection()
    result = hoax_detection.batch_inference([content])
    print(result)
    # >>> ['Fakta']

    # Example usage of AspectDetection class
    aspect_detection = AspectDetection()
    for topic in topics:
        res = aspect_detection.single_inference(content, topic)
        print(f"{topic} - {res}")
    # >>> Institution  - ['netral']
    # >>> Networking   - ['netral']
    # >>> Public Rally - ['netral']

    # Example usage of HoaxDetection class
    keyword_extraction = KeywordExtraction()
    result = keyword_extraction.single_inference(content)
    print(result)
    # >>> ['agendanya', 'anies', 'nasdem', 'sumbawa', 'ntb']