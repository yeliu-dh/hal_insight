import sqlite3
import datetime
import os

# 使用 Streamlit 的持久化存储 /mnt/data
# Streamlit Cloud 提供了一个 持久化目录 /mnt/data，这里的文件可以在 App 重启和更新时保留。(只要不删除app都可以保存)
# DB_PATH = "/mnt/data/feedback.db"

# #删除
# DB_PATH="/home/appuser/app_data/feedback.bd"
# if os.path.exists(DB_PATH):
#     os.remove(DB_PATH)
#     print("旧数据库已删除!")
# else:
#     print('数据库不存在!')


DB_DIR = "/home/appuser/app_data"
os.makedirs(DB_DIR, exist_ok=True)  # 确保目录存在
DB_PATH = os.path.join(DB_DIR, "feedback1.db")



def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            page TEXT,
            problem TEXT,
            reply_date TEXT DEFAULT "",
            handled INTEGER DEFAULT 0,
            reply TEXT,
            published INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()



def append_feedback(page, problem):
    """用户提交反馈"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO feedback (page, problem, date) VALUES (?, ?, ?)", (page, problem, date))
    conn.commit()
    conn.close()

def get_feedback():
    """在manager中获取所有反馈，包括已回复"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM feedback ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def update_feedback(fid, reply_text, handled=True, published=False):
    """更新反馈状态、回复和回复时间"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if reply_text:  # 如果有回复
        reply_date = datetime.datetime.now().strftime("%d-%m-%Y")
    else:
        reply_date = ""  # 保持空字符串
    c.execute("""
        UPDATE feedback
        SET handled=?, reply=?, published=?, reply_date=?
        WHERE id=?
    """, (int(handled), reply_text, int(published), reply_date, fid))
    conn.commit()
    conn.close()


# def update_feedback(fid, reply_text, handled=True, published=False):
#     """更新反馈状态和回复"""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("UPDATE feedback SET handled=?, reply=?, published=? WHERE id=?", (int(handled), reply_text, int(published), fid))
#     conn.commit()
#     conn.close()


def set_published(fid, publish=True):
    """更新公告栏发布状态"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE feedback SET published=? WHERE id=?", (int(publish), fid))
    conn.commit()
    conn.close()

def get_updates(limit=5):
    """获取已处理并发布的公告"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, date, page, problem, reply_date, reply
        FROM feedback
        WHERE handled=1 AND published=1
        ORDER BY date DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


# def get_updates(limit=5):
#     """获取已处理并发布的公告"""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("SELECT page, problem, date, reply FROM feedback WHERE handled=1 AND published=1 ORDER BY date DESC LIMIT ?", (limit,))
#     rows = c.fetchall()
#     conn.close()
#     return rows
