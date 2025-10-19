import requests
import io
import fitz  # PyMuPDF
import pandas as pd
import streamlit as st
import re
import math
import pandas as pd
import streamlit as st

def get_valid_pdf_url(value):
    """从 files_s 字段提取第一个有效的 PDF URL。"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (list, tuple)):
        # 如果是列表，取第一个 http 开头的元素
        for item in value:
            if isinstance(item, str) and item.strip().startswith("http"):
                return item.strip()
        return None
    if isinstance(value, str):
        v = value.strip()
        # 过滤掉无效字符串
        if v.startswith("http") and v.lower().endswith(".pdf"):
            return v
        elif v.startswith("http"):
            # 万一不是 .pdf 结尾，也可能是 pdf 下载链接，保留
            return v
        else:
            return None
    return None

def extract_clean_text(page):
    """去掉页眉页脚区域的文字"""
    blocks = page.get_text("blocks")  # 每个block是 (x0, y0, x1, y1, text, block_no, block_type)
    clean_text = []
    height = page.rect.height

    for b in blocks:
        x0, y0, x1, y1, text, *_ = b
        # 过滤掉上方5%和下方5%的区域（页眉页脚）
        if y0 > height * 0.05 and y1 < height * 0.95:
            clean_text.append(text.strip())

    return "\n".join(clean_text)


def clean_text(text):
    """去掉页码、图表编号、版权声明等"""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d+$", line):  # 纯数字页码
            continue
        if re.match(r"^(Figure|Table)\s+\d+", line, re.I):
            continue
        if re.search(r"(Copyright|©|All rights reserved)", line, re.I):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_text_from_pdf(url: str) -> str:
    """从本地或URL读取PDF，清理页眉页脚并拼接全文"""

    if not url:
        st.warning("URL vide")
        return

    # 判断是否是URL
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()# requests 库里的一个非常有用的安全检查语句，用来在请求失败（HTTP 错误码）时主动抛出异常。
        
        content_type = response.headers.get("content-type", "").lower()
        st.info(f"CODE [{response.status_code}]  | type : {content_type}\n\n"
                f"first bytes: {response.content[:8]}")
        
        # 若为 pdf
        if "pdf" in content_type:       
            pdf_bytes = io.BytesIO(response.content)#把下载的二进制内容包装成一个“文件对象”
            doc = fitz.open(stream=pdf_bytes)
   
    except Exception as e:
        st.warning (f" ⚠ {e}")

    page_texts = []
    for i, page in enumerate(doc):
        raw_text = extract_clean_text(page)  # ① 去页眉页脚
        cleaned = clean_text(raw_text)       # ② 清理无关行
        page_texts.append(cleaned)
        # print(f"✅ 已处理第 {i+1}/{len(doc)} 页 ({len(cleaned)} 字符)")

    doc.close()

    # 拼接所有页形成完整正文
    full_text = "\n".join(page_texts)
    st.write(#f"Page count: {doc.page_count}\n\n"
            f"Text preview{full_text[:100]}\n\n")
    # print(f"提取完成，共 {len(full_text)} 字符。")
    return full_text
    



# ---------------------------------
# 4️⃣ 本地调试
# ---------------------------------
if __name__ == "__main__":
    pdf_url = "https://hal.science/hal-05295655/file/J%20Supply%20Chain%20Manag%20-%202025%20-%20Le%20-%20Workers%20Responses%20to%20CSR%20Decoupling%20in%20Garment%20Supply%20Chains%20A%20Hirschmanian-1.pdf"
    text = extract_text_from_pdf(pdf_url)
    print("\n--- 文本前500字符预览 ---\n")
    print(text[:500])