import sqlite3
import datetime
import os

# 使用 Streamlit 的持久化存储 /mnt/data
# Streamlit Cloud 提供了一个 持久化目录 /mnt/data，这里的文件可以在 App 重启和更新时保留。(只要不删除app都可以保存)
# DB_PATH = "/mnt/data/feedback.db"


DB_DIR = "/home/appuser/app_data"
os.makedirs(DB_DIR, exist_ok=True)  # 确保目录存在
DB_PATH = os.path.join(DB_DIR, "test_usage_log.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page TEXT,
    timestamp TEXT
)
""")
conn.commit()
conn.close()


def log_usage(page, action):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO usage_log (page, action, timestamp) VALUES (?, ?, ?)", (page, action, timestamp))
    conn.commit()
    conn.close()
