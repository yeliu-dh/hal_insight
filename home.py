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
import streamlit as st
import sqlite3
from datetime import datetime

# ========== 配置 ==========
ADMIN_PASSWORD = "123"  # ⚠️ 记得换成你自己的密码

# ========== 数据库函数 ==========
def init_db():
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  page TEXT,
                  problem TEXT,
                  date TEXT,
                  handled INTEGER DEFAULT 0,
                  reply TEXT)''')
    conn.commit()
    conn.close()

def insert_feedback(page, problem):
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("INSERT INTO feedback (page, problem, date) VALUES (?, ?, ?)",
              (page, problem, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_feedback():
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("SELECT * FROM feedback ORDER BY handled, date DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def update_feedback(feedback_id, reply):
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("UPDATE feedback SET handled=1, reply=? WHERE id=?", (reply, feedback_id))
    conn.commit()
    conn.close()

def get_updates(limit=5):
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("SELECT date, reply FROM feedback WHERE handled=1 AND reply IS NOT NULL ORDER BY date DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ========== 初始化数据库 ==========
init_db()

# ========== 页面内容 ==========
st.title("🏠 Home Page")

# --- 用户留言区 ---
st.subheader("📬 留言板")
page = st.selectbox("选择有问题的页面", ["Page1", "Page2", "Page3", "其他"])
problem = st.text_area("请输入您的问题")

if st.button("提交反馈"):
    if problem.strip():
        insert_feedback(page, problem)
        st.success("✅ 感谢您的反馈！")
    else:
        st.warning("请输入问题描述！")

st.divider()

# --- 更新展示区 ---
st.subheader("📢 最新更新")
updates = get_updates()
if updates:
    for date, reply in updates:
        st.info(f"{date} - {reply}")
else:
    st.write("暂无更新~")

st.divider()

# --- 管理员后台 ---
st.subheader("🔑 管理员登录")
password = st.text_input("请输入管理员密码", type="password")

if password == ADMIN_PASSWORD:
    st.success("已进入管理员后台 ✅")

    feedbacks = get_feedback()
    if not feedbacks:
        st.write("暂无留言")
    else:
        for f in feedbacks:
            fid, page, problem, date, handled, reply = f
            with st.expander(f"📌 {date} | {page} | {'✅ 已处理' if handled else '❌ 未处理'}"):
                st.write(problem)
                if handled:
                    st.success(f"回复：{reply}")
                else:
                    reply_text = st.text_input(f"回复（ID: {fid}）", key=f"reply_{fid}")
                    if st.button(f"标记已处理 (ID: {fid})"):
                        update_feedback(fid, reply_text)
                        st.success("处理完成 ✅")
                        st.rerun()



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
