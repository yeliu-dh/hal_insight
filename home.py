import streamlit as st
import sqlite3
from datetime import datetime

#--------DEF-----------
# 初始化数据库
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

def get_updates():
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("SELECT date, reply FROM feedback WHERE handled=1 AND reply IS NOT NULL ORDER BY date DESC LIMIT 5")
    updates = c.fetchall()
    conn.close()
    return updates



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

# st.markdown("""
# Pour tout problème ou question concernant l'utilisation de l'application,  
# veuillez me contacter : ye.liu@chartes.psl.eu
# """)

#---------------------------------------------------------#

#初始化数据库
init_db()

st.header("📬 留言板")
page = st.selectbox("选择有问题的页面", ["Page1:hal articles fetecher", "Page2:tendance repartition", "Page3: wordclouod", "其他"])
problem = st.text_area("请输入您的问题")

if st.button("提交反馈"):
    if problem.strip():
        insert_feedback(page, problem)
        st.success("✅ 感谢您的反馈！")
    else:
        st.warning("请输入问题描述！")


st.divider()
st.header("📢 最新更新")
updates = get_updates()
if updates:
    for u in updates:
        st.info(f"{u[0]} - {u[1]}")
else:
    st.write("暂无更新~")





#----------- 「留言系统 + 公告栏」------------*


#-------------update requirements-----------#
# pipreqs hal_insight --force --savepath hal_insight/requirements.txt


# emojis:

"""

🗂️
📑

📌
🌐
💾
⚠️

🧾

⌛
📅
🔬

✅

💡

"""