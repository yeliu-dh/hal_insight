import streamlit as st
from utils.feedback import init_db, get_feedback, update_feedback, set_published



st.set_page_config(page_title="HAL Insight",page_icon="🛸", layout="wide")
st.title("🛠️ Feedback Manager")
init_db()  # 初始化数据库

#---------Secrets----------
# manage app, settings, secrets
# [admin]
# password = "你的管理员密码"


ADMIN_PASSWORD = st.secrets["admin"]["password"]

password = st.text_input("🔑 Password Admin:", type="password")
if password != ADMIN_PASSWORD:
    st.warning("Password invalid!")
    st.stop()

st.success("✅ 已进入管理员后台")

feedbacks = get_feedback()
# #字段顺序 f：
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             date TEXT,
#             page TEXT,
#             problem TEXT,
#             reply_date TEXT DEFAULT "",
#             handled INTEGER DEFAULT 0,
#             reply TEXT,
#             published INTEGER DEFAULT 0


if not feedbacks:
    st.write("No feedbacks")
else:
    for f in feedbacks: 
        fid, date, page, problem, reply_date, handled, reply, published = f
        with st.expander(f"📌{fid} | {date} | {'✅ 已处理' if handled else '❌ 未处理'}"):
            st.write(problem)
            if handled:
                st.success(f"回复：{reply}")
                publish_toggle = st.checkbox("发布到公告栏", value=bool(published), key=f"publish_{fid}")
                if publish_toggle != bool(published):
                    set_published(fid, publish_toggle)
                    st.info("🔄 公告栏已更新")
                    st.rerun()
            else:
                reply_text = st.text_input(f"Reply to id {fid}:", key=f"reply_{fid}")
                if st.button(f"标记已处理 id {fid}"):
                    update_feedback(fid, reply_text, handled=True, published=False)#自动获取时间
                    st.success("✅ 处理完成 ")
                    st.rerun()



# for page, problem, date, reply, reply_date in updates:
#     st.info(f"{date} | {page} | {problem}\n➡️ 回复({reply_date}): {reply}")
