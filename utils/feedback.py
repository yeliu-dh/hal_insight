# utils/feedback.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
from typing import List, Dict

# 表头 —— 我把 reply_date (管理员回复时间) 一并加入
DEFAULT_HEADER = ["page", "problem", "date", "reply", "reply_date", "handled", "published"]

def _load_credentials_dict():
    """
    从 st.secrets 读取 GCP service account JSON。
    支持几种常见的 secret 存法（见下面的 secrets 示范）。
    """
    secret = st.secrets.get("gcp_service_account")
    if secret is None:
        raise RuntimeError("找不到 st.secrets['gcp_service_account']，请按文档将 GCP 凭证放入 Secrets。")

    # case A: secret 是一个 dict，且含有 credentials 字段（json 字符串）
    if isinstance(secret, dict) and "credentials" in secret:
        cred_field = secret["credentials"]
        if isinstance(cred_field, str):
            return json.loads(cred_field)
        elif isinstance(cred_field, dict):
            return cred_field

    # case B: secret 是一个字符串（直接把 JSON 放在一个 secret 字段里）
    if isinstance(secret, str):
        return json.loads(secret)

    # case C: 直接把 JSON 的 key:value 放在 [gcp_service_account] 下（不常见但支持）
    if isinstance(secret, dict):
        return secret

    raise RuntimeError("未能解析 gcp_service_account 的格式，请参考 README 设置 Secrets。")


def get_client():
    creds = _load_credentials_dict()
    # gspread 提供从 dict 创建 service account 的方法
    return gspread.service_account_from_dict(creds)


def get_sheet(spreadsheet_name_or_key: str, worksheet_index: int = 0):
    """
    打开 Spreadsheet -> 返回 worksheet 对象（默认第一个表单）。
    参数 spreadsheet_name_or_key 可以是表名也可以是 spreadsheet id。
    """
    client = get_client()
    try:
        sh = client.open(spreadsheet_name_or_key)
    except Exception:
        sh = client.open_by_key(spreadsheet_name_or_key)
    ws = sh.get_worksheet(worksheet_index)
    if ws is None:
        ws = sh.sheet1
    return ws


def ensure_header(ws, header=DEFAULT_HEADER):
    """
    确保第一行是我们需要的表头（如果不是，会覆盖第一行）。
    （注意：覆盖 header 会改变表头，但不会改变已有数据行）
    """
    first_row = ws.row_values(1)
    if not first_row or first_row[: len(header)] != header:
        ws.update("A1", [header])


def append_feedback(ws, page: str, problem: str):
    """
    新增一条用户反馈（reply/reply_date/handled/published 使用默认空/0）
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = [page, problem, now, "", "", 0, 0]
    ws.append_row(row, value_input_option="USER_ENTERED")


def fetch_all_feedbacks(ws) -> List[Dict]:
    """
    把 sheet 转成 records（list of dict），并附加 '_row' 字段表示真实的 sheet 行号（从1开始）。
    get_all_records() 会把第一行当 header，返回的数据第一条对应 sheet 的第2行 -> 所以 _row = i + 2
    """
    records = ws.get_all_records()
    for i, rec in enumerate(records):
        rec["_row"] = i + 2
    return records


def update_feedback_by_row(ws, row_number: int, reply=None, handled=None, published=None):
    """
    更新指定行（sheet 的真实行号），只更新非 None 的字段。
    列序：1 page | 2 problem | 3 date | 4 reply | 5 reply_date | 6 handled | 7 published
    如果传入 reply，会同时写 reply_date 为当前时间。
    """
    if reply is not None:
        ws.update_cell(row_number, 4, reply)
        ws.update_cell(row_number, 5, datetime.now().strftime("%Y-%m-%d %H:%M"))
    if handled is not None:
        ws.update_cell(row_number, 6, handled)
    if published is not None:
        ws.update_cell(row_number, 7, published)


def get_updates(ws, limit: int = 5) -> List[Dict]:
    """
    返回要展示在公告栏的记录（handled=1, reply 非空, published=1），按 date 降序。
    返回的记录包含原有字段与 '_row'。
    """
    records = fetch_all_feedbacks(ws)
    # 为确保按提交时间降序，尝试解析 'date'
    def parse_date(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M")
        except Exception:
            return datetime.min

    filtered = []
    for rec in records:
        try:
            handled = int(rec.get("handled", 0))
            published = int(rec.get("published", 0))
            reply = rec.get("reply", "")
        except Exception:
            handled = 1 if str(rec.get("handled")).strip() in ("1", "True", "true") else 0
            published = 1 if str(rec.get("published")).strip() in ("1", "True", "true") else 0
            reply = rec.get("reply", "")

        if handled == 1 and reply and published == 1:
            filtered.append(rec)

    # 按用户提交时间排序（最新在前）
    filtered.sort(key=lambda r: parse_date(r.get("date", "")), reverse=True)
    return filtered[:limit]





















#----------------------------sandbox------------------------------
# credentials_json = st.secrets["gcp_service_account"]["credentials"]
# credentials_dict = json.loads(credentials_json)


# # ----------------- Google Sheets 授权 -----------------
# def get_gsheet():
#     # 这里使用 Streamlit Secrets 管理 JSON
#     credentials_json = st.secrets["gcp_service_account"]  # JSON 内容
#     credentials_dict = json.loads(credentials_json)

#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
#     client = gspread.authorize(creds)

#     sheet = client.open("FeedbackDB").sheet1
#     return sheet

# # 获取 Google API 凭证

# # 打开 Google Cloud Console
# # ，创建项目

# # 启用 Google Sheets API

# # 创建 服务账户（Service Account），下载 JSON 凭证文件

# # 在 Streamlit Cloud 部署时，把 JSON 内容保存为 Secrets（安全存储，不直接放在代码里）




# # 添加一条反馈
# def insert_feedback(page, problem):
#     date = datetime.now().strftime("%Y-%m-%d %H:%M")
#     sheet.append_row([page, problem, date, "", 0, 0])  # reply="", handled=0, published=0

# # 获取所有反馈
# def get_feedback():
#     records = sheet.get_all_records()
#     return records

# # 更新反馈
# def update_feedback(row_index, reply=None, handled=None, published=None):
#     if reply is not None:
#         sheet.update_cell(row_index + 2, 4, reply)  # 第4列 = reply
#     if handled is not None:
#         sheet.update_cell(row_index + 2, 5, handled)  # 第5列 = handled
#     if published is not None:
#         sheet.update_cell(row_index + 2, 6, published)  # 第6列 = published

# # 获取公告栏显示内容
# def get_updates(limit=5):
#     records = sheet.get_all_records()
#     updates = [r for r in records if r["handled"]==1 and r["reply"]!="" and r["published"]==1]
#     return updates[:limit]









#----------------------------Google Sheets API -------------------------------------#
"""
在Google Cloud，获取 Google Sheets API 的凭证。以下是详细步骤：

1️⃣ 打开 Google Cloud Console 并创建项目

访问 Google Cloud Console

点击顶部 项目选择器 → 新建项目

给项目起一个名字，例如 StreamlitFeedback

点击 创建，等待项目创建完成

注意：新项目创建后，你在控制台右上角可以切换当前项目

2️⃣ 启用 Google Sheets API

在左侧菜单搜索框输入 “Google Sheets API”

点击搜索结果进入 API 页面

点击 启用

这一步允许你的应用程序通过 API 访问 Google Sheet

3️⃣ 创建服务账户（Service Account）

在左侧菜单选择 IAM 与管理员 → 服务账户

点击 创建服务账户

名称：例如 streamlit-feedback

描述可以写 用于 Streamlit Feedback 系统

点击 创建并继续

权限部分可以跳过（默认即可）

点击 完成

4️⃣ 创建 JSON 密钥

在服务账户列表里找到刚才创建的账户，点击 管理密钥 → 添加密钥 → 创建新密钥

选择 JSON 格式

点击 创建，浏览器会自动下载一个 JSON 文件

这个 JSON 就是你在代码中使用的凭证

注意不要公开它，属于敏感信息

5️⃣ 将凭证内容存到 Streamlit Cloud Secrets

打开 Streamlit Cloud
 → 你的应用 → Manage app → Secrets

添加一个新的 Secret，例如：

[gcp_service_account]
{
  "type": "...",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  ...
}


JSON 内容就是你下载的服务账户 JSON 文件的全部内容

在streamlit cloud中点击某个app后的三个点，settings，secrets，按照该格式粘贴json内容
[gcp_service_account] #gcp :Google Cloud Platform（谷歌云平台）
credentials = """
{
  "type": "service_account",
  "project_id": "your_project_id",
  "private_key_id": "your_private_key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your_service_account_email",
  "client_id": "your_client_id",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
"""


在代码里使用 st.secrets["gcp_service_account"] 就可以获取到

完成以上步骤，你就可以在 Streamlit Cloud 中通过 Google Sheets API 访问你的 Sheet 了 ✅

NB. 开通 Google Sheets API 本身是免费的，Google 给了免费额度。
免费额度:
Sheets API 属于 Google Drive API 套餐的一部分

免费用户每天可以调用 50 万次请求（Quota 会根据账号类型不同略有差异）

对绝大多数 Streamlit 小应用完全够用


"""