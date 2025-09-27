import streamlit as st
from utils.feedback import init_db, get_feedback, update_feedback, set_published

st.title("🛠️ Feedback Manager")
init_db()  # 初始化数据库


#---------Secrets----------
# manage app, settings, secrets
# [admin]
# password = "你的管理员密码"


ADMIN_PASSWORD = st.secrets["admin"]["password"]

password = st.text_input("🔑 Password Admin:", type="password")
if password != ADMIN_PASSWORD:
    st.warning("请输入正确密码")
    st.stop()

st.success("✅ 已进入管理员后台")

feedbacks = get_feedback()
if not feedbacks:
    st.write("暂无留言")
else:
    for f in feedbacks:
        fid, page, problem, date, handled, reply, published = f
        with st.expander(f"📌 {date} | {page} | {'✅ 已处理' if handled else '❌ 未处理'}"):
            st.write(problem)
            if handled:
                st.success(f"回复：{reply}")
                publish_toggle = st.checkbox("发布到公告栏", value=bool(published), key=f"publish_{fid}")
                if publish_toggle != bool(published):
                    set_published(fid, publish_toggle)
                    st.info("✅ 公告栏已更新")
                    st.experimental_rerun()
            else:
                reply_text = st.text_input(f"回复（ID: {fid}）", key=f"reply_{fid}")
                if st.button(f"标记已处理 (ID: {fid})"):
                    update_feedback(fid, reply_text, handled=True, published=False)
                    st.success("处理完成 ✅")
                    st.experimental_rerun()
