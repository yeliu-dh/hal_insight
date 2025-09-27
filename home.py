import streamlit as st
import sqlite3
from datetime import datetime

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


#----------------------- 「留言系统 + 公告栏」-----------------------*
# ========== 数据库函数 ==========
def init_db():# 获取数据库
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  page TEXT,
                  problem TEXT,
                  date TEXT,
                  handled INTEGER DEFAULT 0,
                  reply TEXT,
                  published INTEGER DEFAULT 0)''')  # 新增 published 字段
    conn.commit()
    conn.close()


def insert_feedback(page, problem):
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("INSERT INTO feedback (page, problem, date) VALUES (?, ?, ?)",
              (page, problem, datetime.now().strftime("%d-%m-%Y")))
    conn.commit()
    conn.close()


def get_updates(limit=5):
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("""
        SELECT page, problem, date, reply 
        FROM feedback 
        WHERE handled=1 AND reply IS NOT NULL AND published=1
        ORDER BY date DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ========== 初始化数据库 ==========
init_db()

# --- 留言板 ---
st.subheader("📬 留言板")
page = st.selectbox("Page en question", ["Page1", "Page2", "Page3", "Autres pages"])
problem = st.text_area("Votre feedback:")

#右下角按钮
cols=st.columns([5,1])
with cols[1]:
    feedback_button=st.button("Soumettre")

if feedback_button:
    if problem.strip():
        insert_feedback(page, problem)
        st.success(f"✅ Merci pour votre feedback！")
    else:
        st.warning("Input obligatoire!")

st.divider()

# --- 更新展示区 ---
st.subheader("📢 公告栏 Updates")
updates = get_updates(limit=10)  # 可以显示更多条

if updates:
    for page, problem, date, reply in updates:
        # 使用卡片风格或者左右两栏
        with st.container():
            st.markdown("---")  # 分隔线
            col1, col2 = st.columns([1, 2])  # 左右比例可以调
            with col1:
                st.caption(f"页面: {page}")
                st.caption(f"提交时间: {date}")
                st.write("用户反馈:")
                st.info(problem)
            with col2:
                st.write("管理员回复:")
                st.success(reply)
else:
    st.write("暂无更新~")




#-------------update requirements-----------#
# pipreqs hal_insight --force --savepath hal_insight/requirements.txt


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
