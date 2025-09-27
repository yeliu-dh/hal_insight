# pages/feedback_manager.py
import streamlit as st
from utils.feedback import get_sheet, ensure_header, fetch_all_feedbacks, update_feedback_by_row


SPREADSHEET_NAME = "FeedbackDB"

# 管理密码 - 推荐从 secrets 读取
ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password", "123456")

ws = get_sheet(SPREADSHEET_NAME)
ensure_header(ws)

st.title("🛠️ Feedback Manager")

password = st.text_input("请输入管理员密码", type="password")
if password != ADMIN_PASSWORD:
    st.warning("请输入正确的管理员密码")
    st.stop()

st.success("✅ 已进入管理员后台")

records = fetch_all_feedbacks(ws)
if not records:
    st.write("暂无留言")
else:
    for rec in records[::-1]:  # 倒序显示（可选）
        row = rec["_row"]
        handled = int(rec.get("handled", 0) or 0)
        published = int(rec.get("published", 0) or 0)

        with st.expander(f"{rec.get('date')} | {rec.get('page')} | {'✅ 已处理' if handled else '❌ 未处理'}"):
            st.write(rec.get("problem"))

            if handled:
                st.success(f"回复：{rec.get('reply')}")
                st.caption(f"回复时间: {rec.get('reply_date', '')}")

                publish_toggle = st.checkbox("是否公开到公告栏", value=bool(published), key=f"pub_{row}")
                if publish_toggle != bool(published):
                    update_feedback_by_row(ws, row, published=int(publish_toggle))
                    st.info("✅ 公告栏状态已更新")
                    st.experimental_rerun()

                # 可撤销处理（恢复为未处理）
                if st.button("撤销处理（设为未处理）", key=f"undo_{row}"):
                    update_feedback_by_row(ws, row, handled=0, published=0)
                    st.info("已撤销处理并取消公开")
                    st.experimental_rerun()

            else:
                reply_text = st.text_input(f"回复（行 {row}）", key=f"reply_{row}")
                if st.button("标记已处理并保存回复", key=f"handle_{row}"):
                    update_feedback_by_row(ws, row, reply=reply_text, handled=1)
                    st.success("处理完成 ✅")
                    st.experimental_rerun()
