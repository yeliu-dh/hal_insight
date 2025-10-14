# import igraph as ig#非纯py，不适合安装在st cloud
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
# import unidecode
from collections import Counter, defaultdict
import pandas as pd

import networkx as nx
from pyvis.network import Network
from streamlit.components.v1 import html #在st中显示


#my utils 
from utils.upload import missing_data_warning
from utils.wordcloud import preprocess_text



def generate_network(df, options, n=10, min_freq=2):
    """
    df 必须包含两列：
    - 'authFullName_s': 字符串，如 'Annick Vignes; Julien Lefournier; Antoine Rieu'
    - 'keyword_s': 字符串，如 'Adjustment strategy; New form of employment'

    """
    COL_MAP={
            "authFullName_s":'authors',
             'keywords_s':"mots clés",
             "abstract_s":"résumés"
             }
    
    # 1️⃣ 把col中的值变成list
    ## authors 列填nan，按；拆成list
    df['authFullName_s'] = df['authFullName_s'].fillna("nan").apply(lambda x: [a.strip() for a in x.split(';') if a.strip()])


    # 筛选options任何一列非空行：
    df = df[
    df[options].apply(
            lambda row: any(
                (isinstance(v, str) and v.strip() != '') or pd.notna(v)
                for v in row
            ),
            axis=1
        )
    ]

    # 清洗options列上的值    
    #-----------nltk stopwords----------------
    stop_en=['won', 'an', 'having', "mightn't", 'the', "hasn't", 'more', 'in', 'only', 'under',
            'o', 'ain', 'can', 'some', 'with', 'these', 'had', 'they', 'me', 'its', 'such', "wouldn't", 
            'as', 'own', "they'd", 'weren', 'or', "shan't", 'don', 'him', 'yours', 'after', 'so', 
            "don't", 'down', 't', 'hadn', "she'll", 'been', 'y', 'whom', 'because', 'about', 'am',
            'my', 'there', 'here', 'up', 'on', 'those', 'once', 'hers', 'too', 'this', 'do', 'further',
            'not', 'at', 'any', 'for', 'haven', 'ours', 'then', 'we', 'each', 'than', "she's", 'herself', 
            "i'm", 's', 'did', 'didn', "i'd", 'shouldn', 'himself', 'you', 'other', 'why', "he'll", 'nor', 
            "needn't", 'couldn', 'needn', 'should', 'where', "haven't", 'i', 'being', "they'll", "he's", 'from',
            'mustn', "we'll", "wasn't", "should've", 'of', 'now', 'until', 'all', 'has', "shouldn't", 'his', 
            "you'll", "it'd", 'll', "they're", "it's", 'does', 'no', 'while', 'into', "that'll", 'itself', 
            'your', 'were', 'above', "it'll", 'ma', 'doing', "mustn't", 'between', 'them', 'and', "they've", 
            'are', 'our', 'off', "i've", 'most', 'out', "won't", 'before', 'will', 'shan', "we're", 'who', "you're",
            'doesn', 'hasn', 'have', 'against', 'just', 'yourselves', 'be', 'is', "isn't", 'a', "aren't", 
            'again', "you'd", "hadn't", 'that', 'but', 'when', "didn't", 'ourselves', "doesn't", 've', 'yourself', 
            'myself', "couldn't", 'd', 'was', "you've", 'both', 'themselves', 'if', 'over', "she'd", 'few', 'her', "he'd",
            'through', 'wouldn', "we'd", 'below', 'theirs', 'aren', 'to', "we've", 'same', 'mightn', 'isn', 'by', 'during',
            'what', 'he', "i'll", 'very', 'how', 'wasn', 'she', "weren't", 'm', 'their', 'which', 'it', 're', "article",
            'research']    

    stop_fr=['j', 'avions', 'avez', 'ta', 'son', 'avais', 'étaient', 'une', 'ai', 'seront', 'il', 'soient', 'étions',
              'sommes','serai', 'me', 'l', 'est', 'tes', 'aurez', 'ayons', 'as', 'elle', 'eusses', 'été', 'fût', 
              'par', 't', 'auraient', 'et', 'notre', 'y', 'aie', 'eux', 'leur', 'le', 'on', 'avaient', 'ont',
              'eue', 'aurait', 'aies', 'eussent', 'eut', 'soit', 'sur', 'avec', 'serions', 'ses', 'n', 'du', 
              'aurions', 'ils', 'es', 'un', 's', 'vous', 'dans', 'qui', 'étée', 'auriez', 'aient', 'je', 'étante',
             'étant', 'fusses', 'mon', 'eurent', 'nous', 'êtes', 'serez', 'auront', 'fut', 'ayants', 'aurais', 'même',
               'fussent', 'auras', 'qu', 'fûtes', 'étiez', 'seras', 'fussions', 'soyez', 'les', 'sois', 'aviez', 'mes', 
               'serait', 'étantes', 'furent', 'eu', 'moi', 'seriez', 'sa', 'avait', 'sera', 'étés', 'ayante', 'fus', 
               'eûtes', 'ma', 'ayantes', 'eusse', 'à', 'se', 'ton', 'en', 'au', 'serons', 'suis', 'ayant', 'ces', 'te', 
               'lui', 'nos', 'des', 'aux', 'eussiez', 'pour', 'eues', 'ne', 'aurons', 'que', 'fussiez', 'tu', 'eussions', 
               'd', 'étants', 'ce', 'étais', 'était', 'serais', 'étées', 'mais', 'eus', 'eût', 'ayez', 'votre', 'seraient', 
               'fusse', 'ait', 'de', 'c', 'la', 'soyons', 'aurai', 'vos', 'fûmes', 'pas', 'm', 'sont', 'aura', 'avons', 'eûmes', 
               'toi', 'ou', "être", "avoir","faire", "et", "de", "la", "le", "les","l","l'", "des", "un", "une", 
                "du", "en", "au","d","dans","à","par","pour","sur","sont","aux","au", "leur","leurs","qui","ou","il","elle","ils","elles",
                "je","tu","vous","nous","se","et","ce",'qui','que',"est","qu","avec","ont","ces",'celle','ceux','celles',
                'comme','afin','ne',"son",'ses',"none","nan","de","des",'la', "pouvoir"
            ]    
    # 转小写+去重
    stopwords = set(w.lower() for w in (stop_en + stop_fr))

    for opt in options:
        # if opt =="keyword_s":#关键词不清洗？
        #     df['keyword_s'] = df['keyword_s'].fillna('nan').apply(lambda x: [k.strip().lower() for k in x.split(';') if k.strip() and str(x).lower() not in ['nan',"none"]])
        #     #NaN 会被转换成str

        # elif opt=='abstract_s':
        #     df["abstract_s"]=df.apply(lambda row: preprocess_text(text=row["abstract_s"], stopwords=stopwords, lang=row["language_s"]),
        #                             axis=1
        #                               )
        #     #需保证x是str
        #     df["abstract_s"]=df['abstract_s'].apply(lambda x: [k.strip() for k in x.split() if k.strip()])
            
        # 多语言清洗：
        # keyword = unidecode(keyword.lower().strip())

        df[opt]=df.apply(lambda row: preprocess_text(text=row[opt], stopwords=stopwords, lang=row["language_s"]),
                                    axis=1
        )
        df[opt]=df[opt].apply(lambda x: [k.strip() for k in x.split() if k.strip()])



    # 取options上的list中的值，如果是list的话
    df["merged_list"] = df[options].apply(
        lambda row: [item for col in options for item in (row[col] or []) if isinstance(row[col], list)],
        axis=1
    )

    # 2️⃣ 统计每一条“作者–关键词”
    edges = []
    for _, row in df.iterrows():
        authors = row.get('authFullName_s', [])# 防止非list值
        keywords = row.get('merged_list', [])
        if not isinstance(authors, list) or not isinstance(keywords, list):
            continue
        for author in authors:
            for w in keywords:
                edges.append((author.strip(), w.strip()))

    # counter “作者–词”
    edge_weights = Counter(edges)

    # 把 Counter 的结果转成 {author: [(keyword, weight), ...]}
    author_keywords = defaultdict(list)
    for (author, keyword), weight in edge_weights.items():
        author_keywords[author].append((keyword, weight))
    
    
    # # 按权重排序并取前 n 个（且过滤掉权重太小的）    
    filtered_edges = []
    filtered_edge_weights = {}

    for author, kw_list in author_keywords.items():
        kw_list = sorted(kw_list, key=lambda x: x[1], reverse=True)#按照weight排序
        for kw, w in kw_list[:n]:
            if w >= min_freq:
                filtered_edges.append((author, kw))
                filtered_edge_weights[(author, kw)] = w


    # ------------------ 构建 NetworkX 图 ------------------
    G = nx.Graph()
    for (a, k), w in filtered_edge_weights.items():  # ⚠ 用筛选后的权重
        G.add_edge(a, k, weight=w)



    # 统计作者节点总权重，用于字体大小
    all_authors = {a for authors in df['authFullName_s'] for a in authors}
    author_freq = Counter()
    for u, v, data in G.edges(data=True):
        w = data.get('weight', 1)
        if u in all_authors:
            author_freq[u] += w
        if v in all_authors:
            author_freq[v] += w

    # ------------------ 创建 PyVis 图 ------------------
    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        notebook=False
    )

    net.from_nx(G)

    # ------------------ 设置节点样式 ------------------
    for node in net.nodes:
        node_id = node['id']
        if node_id in all_authors:
            # 作者节点：红色，字体大小随权重变化
            freq = author_freq.get(node_id, 1)
            node['color'] = 'firebrick'
            node['shape'] = 'text'
            node['font'] = {'size': min(freq,100), 'color': 'black'}#red :firebrick
            node['title'] = f"Connexions : {freq}"
        else:
            # 关键词节点：蓝色，字体大小固定
            node['color'] = 'royalblue'
            node['shape'] = 'text'
            node['font'] = {'size':30, 'color': 'royalblue'}
            # node['title'] = f"Mot-clé : {node_id}"

    # ------------------ 设置边样式 ------------------
    for edge in net.edges:
        src = edge['from']
        dst = edge['to']
        w = G[src][dst].get('weight', 1)
        edge['width'] = max(2, w*2)
        edge['color'] = 'lightgray'
        edge['title'] = f"Cooccurrence : {int(w)}"

    # ------------------ 渲染 ------------------
    net.force_atlas_2based()  # 力导向布局
    net.show_buttons(filter_=['physics'])  # 显示物理参数控制

    # Streamlit 显示
    html(net.generate_html(), height=700)
