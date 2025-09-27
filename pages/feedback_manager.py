import streamlit as st
import sqlite3

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

st.title("🛠️ 反馈管理")

feedbacks = get_feedback()

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
