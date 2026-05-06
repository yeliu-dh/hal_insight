
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


import streamlit as st

#my utils
from utils.preprocess import preprocess_text


# # axe
def parse_axes(x):
    if pd.isna(x):
        return []
    return [a.strip() for a in str(x).split(';')]


# def parse_axes(x):
#     if pd.isna(x):
#         return []
#     return [int(float(a.strip())) for a in str(x).split(';')]


# text
def build_text(row):
    """
    collect title, keywords, absatract
    """
    parts = []
    if pd.notna(row['title_s']):
        parts.append(row['title_s'])
        parts.append(row['title_s'])  # title 加权（重复一次）
    if pd.notna(row['keyword_s']):
        parts.append(row['keyword_s'])
    if pd.notna(row['abstract_s']):
        parts.append(row['abstract_s'])
    return " ".join(parts)


# # emb
# def combine_embeddings(row, w_title=1.0, w_kw=1.2, w_abs=1.5):# 给axe加权
#     vecs = []
#     weights = []

#     if isinstance(row['emb_title_s'], np.ndarray):
#         vecs.append(row['emb_title_s'])
#         weights.append(w_title)

#     if isinstance(row['emb_keyword_s'], np.ndarray):
#         vecs.append(row['emb_keyword_s'])
#         weights.append(w_kw)

#     if isinstance(row['emb_abstract_s'], np.ndarray):
#         vecs.append(row['emb_abstract_s'])
#         weights.append(w_abs)

#     if not vecs:
#         return None

#     return np.average(vecs, axis=0, weights=weights)



def combine_embeddings(row, w_title=1.0, w_kw=1.2, w_abs=1.5):
    vecs = []
    weights = []

    if 'emb_title_s' in row and isinstance(row['emb_title_s'], np.ndarray):
        vecs.append(row['emb_title_s'])
        weights.append(w_title)

    if 'emb_keyword_s' in row and isinstance(row['emb_keyword_s'], np.ndarray):
        vecs.append(row['emb_keyword_s'])
        weights.append(w_kw)

    if 'emb_abstract_s' in row and isinstance(row['emb_abstract_s'], np.ndarray):
        vecs.append(row['emb_abstract_s'])
        weights.append(w_abs)

    if not vecs:
        return None

    return np.average(vecs, axis=0, weights=weights)


        
def preprocess_df_for_topic_modeling(df_input, col_axe):
    ## FOR generate_topics_keywords_scatterplot
       
    df = df_input.copy()
    
    if col_axe in df.columns:
        st.write(f"[info] procéder selon {col_axe}!")
    else :
        st.write(f"[info] {col_axe} not found in df\nprocéder selon 'axe'!")
        col_axe="axe"
    
    df=df[df[col_axe].notna()]
    st.write(f"[info] filtrer les données par l'axe: {len(df_input)} => {len(df)}")
    # df=df[df[col_axe].notna()]
    
    
    df['axe_list'] = df[col_axe].apply(parse_axes)    
    df['true_axe_list'] = df["axe"].apply(parse_axes)#必然存在
    
    if 'predicted_axe' in df.columns:
        df['predicted_axe_list'] = df["predicted_axe"].apply(parse_axes)

    # 处理text
    df['text'] = df.apply(build_text, axis=1)# collect text
    df['clean_text'] = df['text'].apply(preprocess_text)# clean it
    
    #处理emb
    emb_cols=["emb_title_s","emb_keyword_s","emb_abstract_s"]
    if all(col in df.columns for col in emb_cols):#检查所有col_emb是否在df中
        df['combined_emb'] = df.apply(combine_embeddings, axis=1)
        mask_valid = df['combined_emb'].notna()
        X = np.vstack(df.loc[mask_valid, 'combined_emb'].values)
        df = df.loc[mask_valid].copy()

    return df


# def preprocess_df_for_topic_modeling(df):
#     df = df.copy()

#     # 处理axe
    
#     if 'axe' in df.columns:
#         df['axe_list'] = df["axe"].apply(parse_axes)
#     if 'predicted_axe' in df.columns:
#         df['predicted_axe_list'] = df["predicted_axe"].apply(parse_axes)

#     # else:
#     #     raise ValueError("Neither 'final_axe' nor 'axe' column found in dataframe")

#     # 处理text
#     df['text'] = df.apply(build_text, axis=1)
#     df['clean_text'] = df['text'].apply(preprocess_text)
    
#     #处理emb
#     emb_cols=["emb_title_s","emb_keyword_s","emb_abstract_s"]
#     if all(col in df.columns for col in emb_cols):#检查所有col_emb是否在df中
#         df['combined_emb'] = df.apply(combine_embeddings, axis=1)
#         mask_valid = df['combined_emb'].notna()
#         X = np.vstack(df.loc[mask_valid, 'combined_emb'].values)
#         df = df.loc[mask_valid].copy()

#     return df
        

def generate_force_scatterplot(df):
    
    ## PAGE555555
    
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
    
    
    # ------------------------plot--------------------------
    fig, ax = plt.subplots(figsize=(10, 10))
    
    colors = {1:'blue', 2:'orange', 3:'green', 4:'red'}
    
    s_size = 20
    alpha_val = 0.4

    for idx, row in df_plot.iterrows():
        x, y = pos[idx]

        real_axes = row.get('true_axe_list', [])
        pred_axes = row.get('predicted_axe_list', [])

        # ===== 情况 1：真实 axe → 彩色 =====
        if len(real_axes) > 0:
            if len(real_axes) == 1:
                ax.scatter(
                    x, y,
                    # c = colors[real_axes[0]],
                    c = colors[int(float(real_axes[0]))],
                    # c=colors[int(real_axes[0])],
                    s=s_size,
                    alpha=alpha_val
                )
            else:
                for axe in real_axes:
                    ax.scatter(
                        x, y,
                        c=colors[int(axe)],
                        s=s_size,
                        alpha=alpha_val
                    )

        # ===== 情况 2：预测 axe → 灰色数字 =====
        elif len(pred_axes) > 0:
            # 灰色小圆点
            ax.scatter(
                x, y,
                c='lightgrey',
                s=s_size,
                alpha=0.8,
                edgecolors='black',
                linewidth=0.3
            )

            # 在点上显示数字
            ax.text(
                x, y,
                str(pred_axes[0]),  # 如果只有一个预测
                fontsize=7,
                ha='center',
                va='center',
                color='black'
            )

        # ===== 情况 3：都没有 =====
        else:
            ax.scatter(
                x, y,
                c='whitesmoke',
                s=s_size,
                alpha=0.4
            )
            
    # fig, ax = plt.subplots(figsize=(10, 10))
    # # plt.figure(figsize=(10, 10))
    
    # colors = {1:'blue', 2:'orange', 3:'green', 4:'red'}
    # axe_label={"1":"Performances et responsabilités",
    #         "2":"Société de services et services à la société",
    #         "3":"Innovations, transformations et résistances organisationnelles et sociétales",
    #         "4":"Ouvrages pédagogiques"}

    # s_size = 20      # 点大小
    # alpha_val = 0.5  # 透明度

    # for idx, row in df_plot.iterrows():
    #     x, y = pos[idx]
    #     axes = row['axe_list']
    #     if len(axes) == 1:
    #         # 单轴文章 → 一个点
    #         plt.scatter(x, y, c=colors[int(axes[0])], s=s_size, alpha=alpha_val)
    #     else:
    #         # 多轴文章 → 同位置画多个颜色点
    #         for axe in axes:
    #             # plt.scatter
    #             ax.scatter(x, y, c=colors[int(axe)], s=s_size, alpha=alpha_val)


    # show legend ：只显示单轴颜色对应的 axe
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0],[0], marker='o', color='w', label=f"Axe {axe}",
                        markerfacecolor=color, markersize=10)
                    for axe, color in colors.items()]
    
    ax.legend(handles=legend_elements, loc='best')
    ax.set_title(
        "Scatterplot des axes thématiques",
        fontsize=14,
        pad=20
    )
    ax.axis('off')
    # plt.show()
    
    return fig


def filter_by_axe(df, axe_id=None, col="axe_list"):
    """
    根据 axe_id 过滤 dataframe

    axe_id:
        - None        → 不过滤，返回全部
        - str / int   → 单个 axe
        - list / set  → 多个 axe
    """
    if axe_id is None:
        return df.copy()

    # 统一成 list
    if not isinstance(axe_id, (list, set, tuple)):
        axe_id = [str(axe_id)]
    else:
        axe_id = [str(a) for a in axe_id]

    df_filtered= df[df[col].apply(
        lambda axes: any(a in axes for a in axe_id)
    )].copy()
        
    return df_filtered



def get_topics_per_axe(df, col_text="clean_text",min_topic_size=30):
    # filter
    axe_label={"1":"Performances et responsabilités",
            "2":"Société de services et services à la société",
            "3":"Innovations, transformations et résistances organisationnelles et sociétales",
            "4":"Ouvrages pédagogiques"}
    
    # 按照axe进行filter:
    # df_axe = df[df['axe_list'].apply(lambda x: axe_id in x)].copy()
    # if len(axe_id)>0:
    #     df_axe = filter_by_axe(df, axe_id=axe_id, col="axe_list")
    #     st.write(f"[INFO] axe {', '.join(axe_id) if len(axe_id)>1 else axe_id[0]}: {len(df_axe)} textes!")
    # else :
    #     df_axe=df.copy()
    #     st.write(f"[INFO] sur tous les {len(df_axe)} textes!")
        
    texts = df[col_text].tolist()

    # topic
    start_time=time.time()
    topic_model = BERTopic(
        language="multilingual",  
        calculate_probabilities=True,
        min_topic_size=min_topic_size,
        verbose=True, #
        low_memory=False,
        umap_model=UMAP(random_state=42)
    )
        #calculate_probabilities : probs[i, k] = 文档 i 属于 topic k 的概率
        # umap_model= umap_model #决定降维

    topics, probs = topic_model.fit_transform(texts)    
    topic_info = topic_model.get_topic_info()   
    end_time=time.time()

    # show
    topic_ids = topic_info['Topic'].tolist()

    print(f"[INFO] min_topic_size : {min_topic_size}\n"
        f"{len(texts)} texts => {len(topic_ids)} topics!\n"
        f"[RUNTIME]: {end_time-start_time:.2f} sec!")
    
    # rep_docs=topic_info['Representative_Docs'][0]
    # display(topic_info.head())
    return topic_model
    
    
    
    

    
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle

def generate_topics_keywords_scatterplot(
        topic_model, df, col_text="clean_text", 
        axe_id="1", N_WORDS = 5, date_field=None):
    
    # PAGE66666666666666666666666
    
    cmap = plt.get_cmap("tab20")  #Set2, tab20
    
    # 文本保持一致？
    if not 'axe_list' in df:
        df=preprocess_df_for_topic_modeling(df)
    texts = df[col_text].tolist()

    # 提取文本的emb和topic
    embeddings = topic_model.embedding_model.embed(texts)
    topics = topic_model.topics_#topics list

    ##umap降维
    umap_2d = UMAP(
        n_neighbors=15,
        n_components=2,
        min_dist=0.1,
        metric="cosine",
        random_state=42
    )

    ## ================== 文章坐标点
    coords = umap_2d.fit_transform(embeddings)
    df_vis = pd.DataFrame({
        "x": coords[:, 0],
        "y": coords[:, 1],
        "topic": topics
    })
    #加上predicted_axe的信息
    df_vis["true_axe_list"] = df["true_axe_list"].values
    if "predicted_axe_list" in df.columns:
        df_vis["predicted_axe_list"] = df["predicted_axe_list"].values

    ## ==================topics中心点
    topic_centers = (
        df_vis[df_vis.topic != -1]
        # df_vis
        .groupby("topic")[["x", "y"]]
        .mean()
    )
    #topic的关键词
    def topic_label(topic_id, n=5):
        return "\n".join([w for w, _ in topic_model.get_topic(topic_id)[:n]])
    topic_centers["label"] = topic_centers.index.map(topic_label)
    # print(topic_centers)

    # 关键词的权重
    def get_topic_words_with_weights(topic_id, n=8):
        return topic_model.get_topic(topic_id)[:n]


    # vis
    fig, ax = plt.subplots(figsize=(10, 8))
    ## ====================坐标点颜色
    # 1️⃣ outliers (-1)：灰色
    
    mask_outlier = df_vis.topic == -1
    ax.scatter(
        df_vis.loc[mask_outlier, "x"],
        df_vis.loc[mask_outlier, "y"],
        c="lightgrey",
        alpha=0.4,
        s=8,
        # label="Outliers (-1)"
    )

    # 2️⃣ 正常 topics点
    mask_topic = df_vis.topic != -1
    scatter = ax.scatter(
        df_vis.loc[mask_topic, "x"],
        df_vis.loc[mask_topic, "y"],
        c=df_vis.loc[mask_topic, "topic"],
        cmap=cmap,#"Set2",#tab20
        alpha=0.7,
        s=10
    )

    if "predicted_axe_list" in df_vis.columns:
        for i, row in df_vis.iterrows():
            if row["topic"] == -1:
                continue
            
            preds = row["predicted_axe_list"]
            if not preds:
                continue
            label = ",".join(map(str, preds)) #str(preds[0]) # 或仅显示第一个 
            ax.text(
                row["x"],
                row["y"],
                label,
                fontsize=6,
                alpha=0.6,
                color='black',
                ha='center',
                va='center',
                # bbox=dict(facecolor='white', alpha=0.6, edgecolor='none')
            )
            
        

    # ===== 参数=====
    # CIRCLE_RADIUS = 1      # ⭐ 固定半径（UMAP 空间）
    MIN_RADIUS = 0.5
    MAX_RADIUS = 2.0

    BASE_FONT = 10
    MAX_FONT = 25
    FONT_SCALE = 50          # 控制权重 → 字体大小

    # =======Layout keywords========
    for topic_id, row in topic_centers.iterrows():
        # 跳过 outliers（一般不画）
        if topic_id == -1:
            continue

        cx, cy = row.x, row.y
        # 取 topic count
        topic_info = topic_model.get_topic_info()
        topic_count = topic_info.loc[
            topic_info.Topic == topic_id, "Count"
        ].values[0]
        
        # ===== 计算圆半径（随 count 变化） =====
        # 线性缩放到 MIN_RADIUS ~ MAX_RADIUS
        # 可以根据 count 的全局最大最小值来缩放
        all_counts = topic_info[topic_info.Topic != -1]["Count"].values
        min_count, max_count = all_counts.min(), all_counts.max()

        # 防止 max_count == min_count
        if max_count == min_count:
            radius = (MIN_RADIUS + MAX_RADIUS) / 2
        else:
            radius = MIN_RADIUS + (topic_count - min_count) / (max_count - min_count) * (MAX_RADIUS - MIN_RADIUS)

        
        # ===== 画圆 =====
        circle = Circle(
            (cx, cy),
            radius=radius,
            edgecolor='black',
            facecolor="none",
            linestyle="--",
            linewidth=1,
            alpha=0.6,
        )
        plt.gca().add_patch(circle)

        # ===== 画关键词 =====
        words = sorted(
            get_topic_words_with_weights(topic_id, n=N_WORDS),
            key=lambda x: x[1],
            reverse=True
        )
        
        # topic ocunt 权重 ：假设fontscale = weight * topic_count 的某个比例
        all_counts = topic_info[topic_info.Topic != -1]["Count"].values
        min_count, max_count = all_counts.min(), all_counts.max()

        def compute_fontsize(topic_id, weight):
            # 先处理 topic count 归一化 0-1
            if topic_id == -1:
                count_factor = 0.5  # outliers
            else:
                topic_count = topic_info.loc[topic_info.Topic == topic_id, "Count"].values[0]
                if max_count == min_count:
                    count_factor = 1.0
                else:
                    count_factor = (topic_count - min_count) / (max_count - min_count)  # 0-1
            
            # 幂次放大
            count_factor = count_factor ** 2   #让count的权重更大。指数 >1，放大大值，压缩小值
            # 结合词权重，映射到字体大小
            fontsize = BASE_FONT + weight * FONT_SCALE * count_factor
            # 限制最大最小值
            fontsize = np.clip(fontsize, BASE_FONT, MAX_FONT)
            return fontsize
    
        for i, (word, weight) in enumerate(words):
            angle = 2 * np.pi * i / N_WORDS
            # 文字放在圆的  50% 半径处
            r_text = radius * 0.6
            # fontsize = 8 + (weight ** 0.5) * 35
            # fontsize=BASE_FONT + weight * FONT_SCALE
            # fontsize = np.clip(fontsize, 5, 15)
                   
            fontsize=compute_fontsize(topic_id, weight)
            x = cx + r_text * np.cos(angle)
            y = cy + r_text * np.sin(angle)

            plt.text(
                x,
                y,
                word,
                fontsize=fontsize,
                ha="center",
                va="center",
                alpha=0.9,
                # color='gray' if topic_id == -1 else 'black' 
            )
            
    #============================================================================
    # ---axe---
    axe_title=""
    if len(axe_id)>0:
        axe_title= "sous axe "+", ".join(axe_id) if len(axe_id)>=1 else axe_id[0]
    
    
    
    # ---date rang---
    date_title="entre "
    # st.warning(date_field)
    # st.warning(f'date_field in df.columns? :{date_field in df.columns}')
    df[date_field] = pd.to_datetime(df[date_field] , errors="coerce")
    date_min = df[date_field].min()
    date_max = df[date_field].max()
    date_title+=f"{date_min.strftime('%Y/%m')} et {date_max.strftime('%Y/%m')}"
    
    # st.write(
    #     f"{date_title}"
    #     # f"[info] Date de *{date_field}* entre "
    #     # f"**{date_min.strftime('%Y/%m/%d')} et {date_max.strftime('%Y/%m/%d')}**"
    # )

    # df[date_field] = pd.to_datetime(
    #         df[date_field],
    #         utc=True,
    #         errors='coerce'
    #     )
    # date_min,date_max = df[date_field].min(), df[date_field].max()
    # date_title=f"{date_min.strftime('%Y/%m')} - {date_max.strftime('%Y/%m')}"

    plt.title(f"Sujets et Mots clés {axe_title} {date_title}")
    
    # SHOW topics legend
    topics_sorted = sorted(df_vis.topic.unique())
    handles = []

    for idx, topic_id in enumerate(topics_sorted):
        mask = df_vis.topic == topic_id
        if topic_id == -1:
            color = "lightgrey"
            # label = "Topic (-1)"
            # continue
            
            
        else:
            color = cmap(idx % 20)  # 循环颜色
            plt.scatter(
                df_vis.loc[mask, "x"],
                df_vis.loc[mask, "y"],
                c=[color],
                alpha=0.5,
                s=10
            )

        # 获取前 N 个关键词
        top_words = [w for w, _ in get_topic_words_with_weights(topic_id, n=N_WORDS)]
        # 获取 topic count
        topic_count = topic_model.get_topic_info().loc[
            topic_model.get_topic_info().Topic == topic_id, "Count"
        ].values[0]

        label = f"Sujet {topic_id} (n={topic_count}) : {', '.join(top_words)}"
        handles.append(mpatches.Patch(color=color, label=label))


    # ===== 把 legend 放在图下方 =====
    fig.subplots_adjust(bottom=0.25)  # 给 legend 留空间

    ax.legend(
        handles=handles,
        # title="Sujets",
        loc="upper left",
        bbox_to_anchor=(0, -0.05),  # y小于0说明在图的下方
        fontsize=8,
        ncol=1,      # 每个 topic 一行（竖向）
        frameon=False
    )
    # loc 决定“legend 自己的哪个角”
    # bbox_to_anchor 决定“这个角要贴在图的哪个位置”
    ax.set_axis_off()

    # plt.show()    
    return fig






def plot_topics_wc(axe_id, topic_model, plot_color="viridis"):
    # axe_label={"1":"Performances et responsabilités",
    #         "2":"Société de services et services à la société",
    #         "3":"Innovations, transformations et résistances organisationnelles et sociétales",
    #         "4":"Ouvrages pédagogiques"}
    
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

    
    topic_info = topic_model.get_topic_info()

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

    fig.suptitle(f"'Axe {axe_id}", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    return fig