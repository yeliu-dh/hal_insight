import igraph as ig
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import unidecode
from collections import Counter

import networkx as nx
from pyvis.network import Network
from streamlit.components.v1 import html #在st中显示


#my utils 
from utils.upload import missing_data_warning

def generate_network(df, options):
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
    ## authors 
    df['authFullName_s'] = df['authFullName_s'].fillna("nan").apply(lambda x: [a.strip() for a in x.split(';') if a.strip()])
    for opt in options:
        if opt =="keyword_s":#关键词不清洗？
            df['keyword_s'] = df['keyword_s'].fillna('nan').apply(lambda x: [k.strip() for k in x.split(';') if k.strip()])
    
        # elif opt=='abstract_s':

            
        # 多语言清洗：
        # keyword = unidecode(keyword.lower().strip())

    # 2️⃣ 统计每一条“作者–关键词”
    edges = []
    for _, row in df.iterrows():
        for author in row['authFullName_s']:
            for keyword in row['keyword_s']:
                edges.append((author, keyword))
    
    # counter“作者–关键词”
    edge_weights = Counter(edges)
    # edges = list(edge_weights.keys())
    edges = [e for e, w in edge_weights.items() if w > 1]#滤过权重过小的边
    weights = list(edge_weights.values())


    # === 3️⃣ PyVis 动态力导向图 ===
    G = nx.Graph()
    for (a, k), w in edge_weights.items():
        if w>1:# 滤过权重过小的边
            G.add_edge(a, k, weight=w, color="lightgray")

    # 创建 PyVis 力导向图
    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        notebook=False
    )

    # 把 networkx 图导入 pyvis
    net.from_nx(G)

    # 设置节点颜色：作者红色，关键词蓝色
    all_authors = {a for authors in df['authFullName_s'] for a in authors}
    for node in net.nodes:
        node['color'] = 'firebrick' if node['id'] in all_authors else 'royalblue'

    # 打开“physics”控制面板（用户可以调节力导向参数）
    net.show_buttons(filter_=['physics'])

    # 生成并显示图（Streamlit 环境) # st.pyplot仅适用于静态图
    html(net.generate_html(), height=700)



    # # 构建 igraph(静态图)
    # g = ig.Graph()
    # vertices = list(set([v for e in edges for v in e]))
    # g.add_vertices(vertices)
    # g.add_edges(edges)
    # g.es['weight'] = weights


    # # 分类节点
    # author_set = set([a for authors in df['authFullName_s'] for a in authors])
    # keyword_set = set([k for keywords in df['keyword_s'] for k in keywords])

    # # 样式：颜色 + 字体
    # label_colors = {v: "firebrick" if v in author_set else "royalblue" for v in g.vs["name"]}
    # label_sizes = {v: 8 + (weights[i]/3 if i < len(weights) else 0) for i, v in enumerate(g.vs["name"])}



    # # 4️⃣ 力导向布局
    # layout = g.layout_fruchterman_reingold(niter=3000, area=20000, repulserad=3000)
    # coords = np.array(layout.coords)
    # coords = coords * 2.5
    # coords = {v: layout[i] for i, v in enumerate(g.vs["name"])}

    # # 5️⃣ 绘图
    # fig, ax = plt.subplots(figsize=(16, 12))
    # for e, w in zip(edges, weights):
    #     x1, y1 = coords[e[0]]
    #     x2, y2 = coords[e[1]]
    #     ax.plot([x1, x2], [y1, y2], color="lightgray", linewidth=w/4, alpha=0.6)

    # for v in g.vs["name"]:
    #     x, y = coords[v]
    #     ax.text(x, y, v, fontsize=label_sizes.get(v, 6), color=label_colors[v],
    #             ha="center", va="center", fontweight="medium")

    # ax.axis("off")
    # ax.set_title("Author–Keyword Co-occurrence Network", fontsize=18, fontweight="bold")

    # legend_handles = [
    #     mpatches.Patch(color="firebrick", label="Author"),
    #     mpatches.Patch(color="royalblue", label="Keyword"),
    # ]
    # ax.legend(handles=legend_handles, loc="upper right")
    # # plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    # # plt.show()
