import streamlit as st
import sqlite3
from datetime import datetime
from utils.feedback import init_db, append_feedback, get_updates
import gspread

st.set_page_config(page_title="HAL Insight",page_icon="🛸", layout="wide")

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


# #----初始化数据库------
# init_db()  

# # --- 用户反馈表单 ---
# st.subheader("📬 Feedbacks")
# page = st.selectbox("Page en question", ["Page1", "Page2", "Page3", "Autres pages"])
# problem = st.text_area("请描述问题")
# if st.button("提交反馈"):
#     if page and problem:
#         append_feedback(page, problem)
#         st.success("✅ 反馈已提交")
#     else:
#         st.warning("请填写页面和问题描述")

# st.divider()

# st.subheader("📢 Updates")
# updates = get_updates(limit=10)
# if updates:
#     for r in updates:
#         col1, col2 = st.columns([1, 2])
#         with col1:
#             st.caption(f"页面: {r.get('page')}")
#             st.caption(f"提交时间: {r.get('date')}")
#             st.write("用户反馈:")
#             st.info(r.get("problem"))
#         with col2:
#             st.write("管理员回复:")
#             st.success(r.get("reply"))
#             st.caption(f"回复时间: {r.get('reply_date', '')}")
# else:
#     st.write("暂无更新~")



# ========== 初始化数据库 ==========
init_db()

# --- 留言板 ---
st.subheader("📬 Feedbacks")
page = st.selectbox("Page en question", ["Page1", "Page2", "Page3", "Autres pages"])
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

st.divider()

# --- 更新展示区 ---
st.subheader("📢 Updates")
updates = get_updates(limit=10)  # 可以显示更多条

# SELECT id, date, page, problem, reply_date, reply

if updates:
    for r in updates:
        id, date, page, problem, reply_date, reply=r
        with st.container():
            st.markdown("---")  # 分隔线

            col1, col2 = st.columns([1, 2])
            with col1:
                st.caption(f"Date de soumission: {date}")
                st.caption(f"Page: {page}")
                st.write("Feedback:")
                st.info(problem)
            with col2:
                st.caption(f"Date de réponse: {reply_date}")
                st.write("Réponse:")
                st.success(reply)
else:
    st.write("Aucune mis à jour...")



# if updates:
#     for page, problem, date, reply in updates:
#         # 使用卡片风格或者左右两栏
#         with st.container():
#             st.markdown("---")  # 分隔线
#             col1, col2 = st.columns([1, 2])  # 左右比例可以调
#             with col1:
#                 st.caption(f"Page: {page}")
#                 st.caption(f"Date de soumission: {date}")
#                 st.write("Feedback:")
#                 st.info(problem)
#             with col2:
#                 st.write("Réponse:")
#                 st.success(reply)
# else:
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
