import streamlit as st
import sqlite3
from datetime import datetime
from utils.feedback import init_db, append_feedback, get_updates
import gspread

#标签页：
st.set_page_config(page_title="HAL Insight",page_icon="🛸")
# , layout="wide"
#当前页标题
st.title("🏠 Accueil | HAL Insight")

st.markdown("""
Bienvenu-e sur le tableau de bord HAL Insight !

🔎 Ici vous pouvez :
- Récupérer les articles sur HAL
            
- Générer des plots :
    * Aperçu global des publications scientifiques
    * Répartitions par pays, langue, domaine,etc.
    * Tendances temporelles
    * Nuage des mots clés
    * Réseaux de cooccurrence
            
en consultant la barre latéral! 
""")
st.divider() #分割线


# -----------------初始化数据库 ----------------
init_db()

# --- 留言板 ---
st.subheader("📬 Feedbacks")
st.markdown("Merci de m'écrire ici ou par email (ye.liu@chartes.psl.eu)")
page = st.selectbox("App en question", ["articles fetcher", "tendance & répartition", "keywords", "Autres pages"])
problem = st.text_area("Votre feedback:")

#右下角按钮
cols=st.columns([5,1])
with cols[1]:
    feedback_button=st.button("Soumettre")

if feedback_button:
    if problem.strip():
        append_feedback(page, problem)
        st.success(f"✅ Merci pour votre feedback！")
    else:
        st.warning("Input obligatoire!")


# --- 更新展示区 ---
st.subheader("📢 Updates")
updates = get_updates(limit=10)  # 可以显示更多条
st.divider() #分割线

cols=st.columns(2)
with cols[0]:
    st.write("### feedbacks")
with cols[1]:
    st.write("### réponse")


if updates:
    for r in updates:
        # consistent with "get_updates":
        # SELECT id, date, page, problem, reply_date, reply
        id, date, page, problem, reply_date, reply=r
        with st.container():
            st.markdown("---")  # 分隔线

            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"{date} | {page}")
                st.write(problem)
                # st.info(f"Feedback:  \n {problem}")#两个空格 + 换行（Markdown 风格）
            with col2:
                st.caption(f"{reply_date}")
                st.write(reply)
                # st.success(reply)
                # st.success(f"Réponse:  \n {reply}")
                
# else:
#     st.write('\n')
#     st.write("Aucune mis à jour...")











#-------------update requirements-----------#
#  pipreqs hal_insight --force --savepath hal_insight/requirements.txt



# emojis:
# 🗂️
# 📑

# 📌
# 🌐
# 💾
# ⚠️

# 🧾
# ⬆️
# ⌛
# 📅
# 🔬

# ✅

# 💡


# #--------------structure----------------
# hal_insight/
# │
# ├── Home.py                          # 首页（总览+导航说明）
# ├── utils/                           # 公用函数/模块
# │   ├── __init__.py
# │   ├── charts.py                    # 通用画图函数
# │   ├── preprocess.py                 # 数据清洗函数
# │   └── fetch.py                     # HAL fetcher 公用逻辑
# │
# ├── pages/
# │   ├── facets
# │   ├── 1_hal_articles_fetcher       # 页面1：HAL 数据抓取
# │   ├── 2_tendances & repartiton/    # 页面2：科研产出趋势  │
# │   ├── 3_/               # 页面3：科研分布
# │   │   ├── __init__.py
# │   │   ├── Repartition.py
# │   │   └── repartition_utils.py
# │   │
# │   ├── 4_Mots_cles/                 # 页面4：词云
# │   │   ├── __init__.py
# │   │   ├── Mots_cles.py
# │   │   └── stopwords_fr.txt         # 本页用的法语停用词文件
# │   │
# │   └── 5_Cooccurrence/              # 页面5：共现网络
# │       ├── __init__.py
# │       ├── Cooccurrence.py
# │       └── network_utils.py
# │   └── feedback_manager

# │
# ├── requirements.txt
# └── README.md
