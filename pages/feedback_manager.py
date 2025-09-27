import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="HAL Insight",page_icon="🛸", layout="wide")

st.title("🏠 AMDIN | feedback manager")



#--------配置---------
ADMIN_PASSWORD = "123"  # ⚠️ 记得换成你自己的密码


#------------DEF--------
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

def set_published(feedback_id, published):#更新数据库中published的值
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("UPDATE feedback SET published=? WHERE id=?", (published, feedback_id))
    conn.commit()
    conn.close()


# --- 管理员后台 ---
st.subheader("🔑 Admin Login")
password = st.text_input("请输入管理员密码", type="password")
"""
            👉 遍历数据库中的留言，解包出字段：
            fid → 留言 ID

            page → 用户选择的问题页面

            problem → 问题描述

            date → 留言时间

            handled → 是否已处理（0 = 未处理，1 = 已处理）

            reply → 管理员回复

            published → 是否更新到公告栏（默认为0，不发布）

"""

if password == ADMIN_PASSWORD:
    st.success("✅ 已进入管理员后台 ")

    feedbacks = get_feedback()
    if not feedbacks:
        st.write("暂无留言")
    else:
        for f in feedbacks:
            fid, page, problem, date, handled, reply, published = f

            with st.expander(f"📌 {date} | {page} | {'✅ 已处理' if handled else '❌ 未处理'}"):
                st.write(problem)

                if handled:#已回复，选择是否发布
                    st.success(f"回复：{reply}")
                    
                    # publish_toggle是 Streamlit st.checkbox() 的返回值，勾选则为1
                    publish_toggle = st.checkbox("更新到公告栏", value=bool(published), key=f"pub_{fid}")
                    
                    # 如果数据库中的publish值和页面不同，说明状态改变
                    if publish_toggle != bool(published):
                        set_published(fid, int(publish_toggle))
                        st.info("✅ 公告栏已更新")
                        st.rerun()

                else:
                    reply_text = st.text_input(f"回复（ID: {fid}）", key=f"reply_{fid}")
                    if st.button(f"标记已处理 (ID: {fid})"):
                        update_feedback(fid, reply_text)
                        st.success("✅ 处理完成")
                        st.rerun()# 刷新页面
                                  # 这条留言已经变成 handled=1，仍默认pub=0，再渲染的时候就会走到 if handled: 分支：
