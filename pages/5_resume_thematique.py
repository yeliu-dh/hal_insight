import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap #分行
import altair as alt
import plotly.express as px
from PIL import Image
import io
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


#RESUME : 
from transformers import pipeline


#my utils:
from utils.upload import data_uploader
from utils.upload import missing_data_warning
from utils.preprocess import load_external_json
from utils.preprocess import preprocess_text




# @st.cache_resource  # ✅ 缓存模型
# def load_model():  
    # return pipeline(
    #     "summarization",
    #     model="plguillou/t5-base-fr-sum-cnndm",
    #     tokenizer="plguillou/t5-base-fr-sum-cnndm",
    #     use_fast=False
    # )
# summarizer = load_summarizer()




# #====================CACHE=========================#
# @st.cache_data 
# def get_stopwords():   
#     stopwords_nltk=load_external_json('json_data',"stopwords_nltk")
#     stopwords_nltk=list(stopwords_nltk.values())
#     return stopwords_nltk
# stopwords=get_stopwords()
# st.set_page_config(page_title="HAL insight", page_icon="🛸")
st.title("Résumé thématique")


# -------------------------------
# 1️⃣ 初始化 Session State
# -------------------------------
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "started" not in st.session_state:
    st.session_state.started = False

# -------------------------------
# 2️⃣ 检查/上传 CSV
# -------------------------------
st.markdown("<br>", unsafe_allow_html=True)#不容易被 Markdown 渲染压缩掉
data_uploader()# 调用上传器（会自动处理已有/新上传）
st.markdown("<br>", unsafe_allow_html=True)
st.divider() 


if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    # 若df存在则视为开始
    st.session_state.started=True
    df = st.session_state.uploaded_df.copy()
    
    st.subheader("🔢 auto-completion des axes thématiques")
        

    def safe_get(val):
        return "" if pd.isna(val) else str(val)

    df["clean_text"] = df.apply(
        lambda r: preprocess_text(
            safe_get(r["title_s"]) + " " +
            safe_get(r["keyword_s"]) + " " +
            safe_get(r["abstract_s"]),
            user_stopwords=None,
            lang=r['language_s']
        ),
        axis=1
    )
