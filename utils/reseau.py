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
from utils.preprocess import preprocess_text



def generate_network(df, options, stopwords, author_structure, n=10, min_freq=2):
    """
    df 必须包含两列：
    - 'authFullName_s': 字符串，如 'Annick Vignes; Julien Lefournier; Antoine Rieu'
    - 'keyword_s': 字符串，如 'Adjustment strategy; New form of employment'

    MAPPING DICT : author_structure :
    {authFullName_s:'id_authorprimarystructure'}

    """

    #=======================================1️⃣ texte==========================================
    COL_MAP={
            "authFullName_s":'authors',
             'keywords_s':"mots clés",
             "abstract_s":"résumés"
             }
    
    # 把col中的值变成list
    ## authors列填nan，按；拆成list，要求authors不为“nan”
    def clean_authors(x):
        if isinstance(x, str) and x.strip().lower() not in ['nan', 'none', '']:
            return [a.strip() for a in x.split(';') if a.strip()]
        return []  # 返回空 list
    df['authFullName_s'] = df['authFullName_s'].apply(clean_authors)
    
    
    # ##only_irg_authors?筛选df
    # IRG_IDS = {"1004418", "57129"}

    # if only_irg_authors:
    #     df = df[df["authFullName_s"].apply(
    #         lambda author_list: any(
    #             author_structure.get(a, None).split('_')[0] in IRG_IDS
    #             for a in author_list
    #         )
    #     )]


    # ⭐ 筛选options任何一列非空行：
    # st.write(f"len df AVANT filtrage {len(df)}")

    df = df[
    df[options].apply(
            lambda row: any(
                (isinstance(v, str) and v.strip() != '') or pd.notna(v)
                for v in row
            ),
            axis=1
        )
    ]
    # st.write(f"len df APRES filtrage {len(df)}")

    # 清洗options列上的值    
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

        df[opt]=df.apply(lambda row: preprocess_text(text=row[opt], user_stopwords=stopwords, lang=row.get("language_s", "fr")),
                                    axis=1
        ) #nan只返回""

        df[opt]=df[opt].apply(lambda x: [k.strip() for k in x.split() if k.strip()])


    # 取options上的list中的值，如果是list的话
    df["merged_list"] = df[options].apply(
        lambda row: [item for col in options for item in (row[col] or []) if isinstance(row[col], list)],
        axis=1
    )


    #==============================2️⃣compter les noeuds et lignes==================================
    #  统计每一条“作者–关键词”
    edges = []
    for _, row in df.iterrows():
        authors = row.get('authFullName_s', [])# 防止非list值
        keywords = row.get('merged_list', [])
        if not isinstance(authors, list) or not isinstance(keywords, list):
            continue
        for author in authors:
            for w in keywords:
                edges.append((author.strip(), w.strip()))
                # [(A, mot_a),(A_mot_b),(B, mot_a),...]


    # counter “作者–词”， 频率大于min freq
    edge_weights = Counter(edges)
    edge_weights = {pair: w for pair, w in edge_weights.items() if w >= min_freq}
    #{(A, mot_a):10,
    # (A, mot_b):20, 
    # ...}


    # DETOUR： 把 Counter 的结果转成 {author: [(keyword, weight), ...]}来筛选 top N
    author_keywords = defaultdict(list)
    for (author, keyword), weight in edge_weights.items():
        author_keywords[author].append((keyword, weight))
    # st.info(f"{len(author_keywords.keys())} auteurs, {len(author_keywords.values())} keywords more than {min_freq}!")


    filtered_edges = []
    filtered_edge_weights = {}
    for author, kw_list in author_keywords.items():
        kw_list = sorted(kw_list, key=lambda x: x[1], reverse=True)#按照weight排序
        for k, w in kw_list[:n]:
            filtered_edges.append((author, k))
            filtered_edge_weights[(author, k)] = w

    # valid_keywords = {kw for _, kw in filtered_edges}

    # for (a, k), w in filtered_edge_weights.items():
    #     st.write(f"author:{a}")#Philippe Lépinard
    #     st.write(f"keyword:{k}")#ludopédagogie
    #     st.write(f"weight:{w}")#11
    #     break 

    # st.write(filtered_edge_weights[0].items())
    # [
    #     0:[
    #         0:[
    #         0:"Philippe Lépinard"
    #         1:"ludopédagogie"
    #         ]
    #     1:11
    #     ],
    # ...
    # ]


    #==============================构建 NetworkX 图==================================
    # etworkX Graph 重复添加边会覆盖权重
    # 如果你用的是 nx.Graph()（无向图），重复添加同一条边时 weight 会被覆盖。

    # G = nx.Graph()
    # # input de G :{(author, keyword):weight}
    # for (a, k), w in filtered_edge_weights.items():  # ⚠ 用筛选后的权重
    #     G.add_edge(a, k, weight=w)

    G = nx.Graph() # NetworkX.Graph() 是无向图（undirected graph），所以 (a, b) 和 (b, a) 是同一条边。
    for (a, k), w in filtered_edge_weights.items():
        if G.has_edge(a, k):#之后增加w
            G[a][k]['weight'] += w  # 累加
        else:#第一次初始化
            G.add_edge(a, k, weight=w)


    # 移除孤立节点（没有任何连接）
    isolated_nodes = list(nx.isolates(G))
    G.remove_nodes_from(isolated_nodes)
  

    #==============================设置节点样式=======================================
    # # 统计作者节点总权重，用于字体大小
    # all_authors = {a for authors in df['authFullName_s'] for a in authors}
    # author_freq = Counter()
    # for u, v, data in G.edges(data=True):
    #     w = data.get('weight', 1)
    #     if u in all_authors:
    #         author_freq[u] += w
    #     if v in all_authors:
    #         author_freq[v] += w

    # ------------------ 创建 PyVis 图 ------------------
    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        notebook=False
    )

    net.from_nx(G)


    #=============================设置节点样式 ============================
    # ------------------ 动态归一化 ------------------
    node_freq = Counter()

    # 遍历边，统计每个节点的总连接权重
    for u, v, data in G.edges(data=True):
        w = data.get("weight", 1)
        node_freq[u] += w
        node_freq[v] += w

    # ------------------ 节点大小动态归一化 ------------------
    # min_size, max_size = 20, 80

    # 若节点词频统计存在：选择所有词频中最小值和最大值
    min_freq_val = min(node_freq.values()) if node_freq else 1
    max_freq_val = max(node_freq.values()) if node_freq else 1
    
    #把节点大小（按频率）映射到15~80之间
    def scale_size(freq, min_freq_val, max_freq_val, min_size=20, max_size=80):
        if max_freq_val == min_freq_val:
            return (min_size + max_size) / 2
        return min_size + (freq - min_freq_val) * (max_size - min_size) / (max_freq_val - min_freq_val)
    
    ## ------------------ 设置作者和关键词节点样式 ------------------
    # all_authors = {a for authors in df['authFullName_s'] for a in authors}

    # for node in net.nodes:
    #     node_id = node['id']
    #     freq = node_freq.get(node_id, 1)
    #     scaled = scale_size(freq, min_freq_val, max_freq_val) 

    #     if node_id in all_authors:
    #         node['shape'] = 'text'
    #         node['font'] = {'size': scaled, 'color': 'black'}
    #         node['title'] = f"Auteur : {node_id},Connexions : {freq}"
    #     else:
    #         node['shape'] = 'text'
    #         node['font'] = {'size': scaled, 'color': 'royalblue'}
    #         node['title'] = f"Mot-clé : {node_id}, Connexions : {freq}"
    
    
    # -------------- 参数设置 --------------
    IRG_IDS = {"1004418", "57129"}   # IRG 的两个 ID

    # -------------- 取出所有作者 --------------
    all_authors = {a for authors in df['authFullName_s'] for a in authors}

    # -------------- 设置节点样式 --------------
    for node in net.nodes:
        node_id = node["id"]
        freq = node_freq.get(node_id, 1)
        scaled = scale_size(freq, min_freq_val, max_freq_val)

        # =============================
        # CASE 1: 关键词节点（不是作者）
        # =============================
        if node_id not in all_authors:
            node["shape"] = "text"
            node["font"] = {"size": scaled, "color": "black"}
            node["title"] = f"Mot-clé : {node_id}<br>Connexions : {freq}"
            continue

        # =============================
        # CASE 2: 作者节点（需要根据机构染色）
        # =============================
        struct_raw = author_structure.get(node_id, "")

        # 提取结构 ID（以 "_" 前部分为 ID）
        struct_id = struct_raw.split("_")[0] if "_" in struct_raw else ""

        # ———— 根据结构 ID 判断颜色 ————
        if struct_id in IRG_IDS:
            color = "red"          # IRG 作者
        else:
            color = "royalblue"    # 其他机构作者

        node["shape"] = "text"
        node["font"] = {"size": scaled, "color": color}
        node["title"] = (
            f"Auteur : {node_id}<br>"
            f"Institution : {struct_raw}<br>"
            f"Connexions : {freq}"
        )


    # ------------------ 设置边样式 ------------------
    all_weights = filtered_edge_weights.values()
    min_w = min(all_weights) if all_weights else 1
    max_w = max(all_weights) if all_weights else 1

    # 设置边样式
    for edge in net.edges:
        src, dst = edge['from'], edge['to']
        if (src, dst) in filtered_edge_weights:
            w = filtered_edge_weights[(src, dst)]
        elif (dst, src) in filtered_edge_weights:
            w = filtered_edge_weights[(dst, src)]
        else:
            w = 1
            # st.warning(f"Edge {src}<->{dst} : weight not found")
        # st.write(src, dst, w)

        edge['width'] = scale_size(w, min_w, max_w, min_size=2, max_size=20)
        edge['color'] = 'lightgray'
        edge['title'] = f"Cooccurrence : {int(w)}"



    # ------------------ 渲染 ------------------
    net.force_atlas_2based()  # 力导向布局
    net.show_buttons(filter_=['physics'])  # 显示物理参数控制


    # # Streamlit 显示
    # html_code=net.generate_html()
    # html(html_code, height=700)

    # 生成原图 HTML
    html_code = net.generate_html()
    # 你的图例 HTML（绝对定位）
    legend_html = """
    <div style="
        position: absolute;
        top: 20px;
        right: 20px;
        background: rgba(255,255,255,0.9);
        padding: 10px 14px;
        border: 1px solid #ccc;
        border-radius: 6px;
        font-size: 14px;
        z-index: 9999;
    ">
    <span style="color:red;">■</span> Auteurs IRG (1004418, 57129)<br>
    <span style="color:royalblue;">■</span> Autres auteurs<br>
    <span style="color:black;">■</span> Mots-clés<br>
    <span style="color:gray;">■</span> Arêtes
    </div>
    """

    # 将图例注入 <body> 里面
    html_code = html_code.replace("<body>", "<body>" + legend_html)

    # Streamlit 展示（高度可以调整）
    html(html_code, height=700)


    #===================下载===================
    html_path = "reseau_auteurs_mots.html"
    # 服务器端（Streamlit Cloud 上）文件的存储路径。
    # 临时在服务器上生成并保存 HTML 文件，以便 st.download_button 可以读取它。
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_code)  
    
    # 添加下载按钮
    cols=st.columns([4,1])
    with cols[1]:    
        with open(html_path, "rb") as f:
            st.download_button(
                label="📥 Télécharger le graphique (HTML)",
                data=f,
                file_name="reseau_auteurs_mots.html",
                mime="text/html"
            )
        
