
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import time
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from matplotlib.lines import Line2D




#my utils
from utils.preprocess import preprocess_text


# axe
def parse_axes(x):
    if pd.isna(x):
        return []
    return [a.strip() for a in str(x).split(';')]

# text
def build_text(row):
    parts = []
    if pd.notna(row['title_s']):
        parts.append(row['title_s'])
        parts.append(row['title_s'])  # title 加权（重复一次）
    if pd.notna(row['keyword_s']):
        parts.append(row['keyword_s'])
    if pd.notna(row['abstract_s']):
        parts.append(row['abstract_s'])
    return " ".join(parts)


# emb
def combine_embeddings(row, w_title=1.0, w_kw=1.2, w_abs=1.5):# 给axe加权
    vecs = []
    weights = []

    if isinstance(row['emb_title_s'], np.ndarray):
        vecs.append(row['emb_title_s'])
        weights.append(w_title)

    if isinstance(row['emb_keyword_s'], np.ndarray):
        vecs.append(row['emb_keyword_s'])
        weights.append(w_kw)

    if isinstance(row['emb_abstract_s'], np.ndarray):
        vecs.append(row['emb_abstract_s'])
        weights.append(w_abs)

    if not vecs:
        return None

    return np.average(vecs, axis=0, weights=weights)





def preprocess_df_for_topic_modeling(df):
    
    df['axe_list'] = df['final_axe'].apply(parse_axes)
        
    df['text'] = df.apply(build_text, axis=1)

    df['clean_text']=df["text"].apply(preprocess_text)
    
    df['combined_emb'] = df.apply(combine_embeddings, axis=1)
    X = np.vstack(df['combined_emb'].dropna().values)
    df = df.loc[df['combined_emb'].notna()].copy()

    return df
        
        

def generate_force_scatterplot(df):
    df_plot=df.copy()
    
    # init
    G = nx.Graph()
    for idx, row in df_plot.iterrows():
        G.add_node(
            idx,
            axes=row['axe_list'],          # 保留完整列表
            emb=row['combined_emb'],       # embedding
            n_axes=len(row['axe_list'])    # 用于可视化大小或透明度
        )

    #相似吸引力 1：语义相似 → 吸引（弱）# 加强最近的10且sim大于0,85的文章之间的力？
    X = np.vstack(df_plot['combined_emb'])
    S = cosine_similarity(X)

    K = 10 # 每个点只连最近的 K 个
    sim_thresh = 0.85

    for i in range(len(df_plot)):
        topk_idx = np.argpartition(-S[i], K+1)[:K+1]
        for j in topk_idx:
            if i < j and S[i,j] > sim_thresh:
                G.add_edge(i, j, weight=0.3)


    # axe聚集力：axe 虚拟节点 (弱吸引)===
    # 先假设一个axe的虚拟节点，让文章与axe节点项链，历遍所有文章时候，layout会自动拉拢同一axe下的所有文章
    for idx, row in df_plot.iterrows():
        for axe in row['axe_list']:
            axe_node = f"AXE_{axe}"  
            if axe_node not in G:
                G.add_node(axe_node, type='axe') 
            G.add_edge(idx, axe_node, weight=0.1)  

    # layout points+force
    pos = nx.spring_layout(
        G,
        weight='weight',
        iterations=100,
        seed=42,
        # k=2, # k 越大，节点之间的自然间距越大，k 不是在“增加真实结构”，而是在给结构一个“能展开的空间”。
    )
    
    
    # plot
    plt.figure(figsize=(10, 10))
    colors = {1:'blue', 2:'orange', 3:'green', 4:'red'}
    axe_label={"1":"Performances et responsabilités",
            "2":"Société de services et services à la société",
            "3":"Innovations, transformations et résistances organisationnelles et sociétales",
            "4":"Ouvrages pédagogiques"}

    s_size = 20      # 点大小
    alpha_val = 0.5  # 透明度

    for idx, row in df_plot.iterrows():
        x, y = pos[idx]
        axes = row['axe_list']
        if len(axes) == 1:
            # 单轴文章 → 一个点
            plt.scatter(x, y, c=colors[int(axes[0])], s=s_size, alpha=alpha_val)
        else:
            # 多轴文章 → 同位置画多个颜色点
            for axe in axes:
                plt.scatter(x, y, c=colors[int(axe)], s=s_size, alpha=alpha_val)

    # show legend ：只显示单轴颜色对应的 axe
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0],[0], marker='o', color='w', label=f"Axe {axe}",
                        markerfacecolor=color, markersize=10)
                    for axe, color in colors.items()]
    plt.legend(handles=legend_elements, loc='best')

    plt.axis('off')
    # plt.show()
    
    return









def get_topics_per_axe(df, axe_id, min_topic_size=30):
    # filter
    axe_label={"1":"Performances et responsabilités",
            "2":"Société de services et services à la société",
            "3":"Innovations, transformations et résistances organisationnelles et sociétales",
            "4":"Ouvrages pédagogiques"}
    
    df_axe = df[df['axe_list'].apply(lambda x: axe_id in x)].copy()
    texts = df_axe['clean_text'].tolist()
    print(f"[INFO] axe{axe_id} : {axe_label.get(axe_id)}, {len(df_axe)} texts!")

    # topic
    start_time=time.time()
    topic_model = BERTopic(
        language="multilingual",  # 如果是法文 / 多语言
        calculate_probabilities=True,#probs[i, k] = 文档 i 属于 topic k 的概率
        min_topic_size=min_topic_size,
        verbose=True, #
        low_memory=False,
        umap_model=UMAP(random_state=42)
        # umap_model= umap_model #决定降维
    )
    topics, probs = topic_model.fit_transform(texts)    
    topic_info = topic_model.get_topic_info()   
    end_time=time.time()

    # show
    topic_ids = topic_info['Topic'].tolist()
    print(f"[INFO] min_topic_size : {min_topic_size}\n"
        f"{len(texts)} texts => {len(topic_ids)} topics!\n"
        f"[RUNTIME]: {end_time-start_time:.2f} sec!")
    
    rep_docs=topic_info['Representative_Docs'][0]

    display(topic_info.head())
    
    
    return topic_model, topic_info
    
    

    
def plot_topics_wc(axe_id, topic_model, plot_color="viridis"):
    topic_info = topic_model.get_topic_info()
    axe_label={"1":"Performances et responsabilités",
            "2":"Société de services et services à la société",
            "3":"Innovations, transformations et résistances organisationnelles et sociétales",
            "4":"Ouvrages pédagogiques"}
    
    # # filter    
    # df_axe = df[df['axe_list'].apply(lambda x: axe_id in x)].copy()
    # texts = df_axe['clean_text'].tolist()
    # print(f"[INFO] axe{axe_id} : {axe_label.get(axe_id)}, {len(df_axe)} texts!")

    # # topic
    # start_time=time.time()
    # topic_model = BERTopic(
    #     language="multilingual",  # 如果是法文 / 多语言
    #     calculate_probabilities=True,#probs[i, k] = 文档 i 属于 topic k 的概率
    #     min_topic_size=min_topic_size,
    #     verbose=True, #
    #     low_memory=False,
    #     umap_model=UMAP(random_state=42)
    #     # umap_model= umap_model #决定降维
    # )
    # topics, probs = topic_model.fit_transform(texts)    
    # topic_info = topic_model.get_topic_info()
    # display(topic_info.head())
    
    # end_time=time.time()

    # # show
    # topic_ids = topic_info['Topic'].tolist()
    # print(f"[INFO] min_topic_size : {min_topic_size}\n"
    #     f"{len(texts)} texts => {len(topic_ids)} topics!\n"
    #     f"[RUNTIME]: {end_time-start_time:.2f} sec!")
    
    
    # color:
    topic_ids = topic_info['Topic'].tolist()    
    cmap = cm.get_cmap(plot_color, len(topic_ids))  # len(topic_ids) 个颜色
    topic_colors = {topic_id: cmap(i) for i, topic_id in enumerate(topic_ids)}

    # plot
    fig, axes = plt.subplots(1, len(topic_ids), figsize=(16,4))
    for ax, topic_id in zip(axes, topic_ids):
        words = dict(topic_model.get_topic(topic_id))#{word:weight}    
        count = topic_info.loc[topic_info.Topic==topic_id, 'Count'].values[0]# showed in title
        
        wc = WordCloud(
            background_color="white",
            colormap=cm.colors.ListedColormap([topic_colors[topic_id]]),  # 每个 topic 单色
            width=400,
            height=400
        ).generate_from_frequencies(words)

        ax.imshow(wc, interpolation='bilinear')
        # ax.set_title(f"Topic {topic_id}", fontsize=12)
        ax.set_title(f"Topic {topic_id} (n={count})", fontsize=12)

        ax.axis("off")

    fig.suptitle(f"Axe {axe_id} – {axe_label.get(axe_id)}", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    # plt.show()

    return