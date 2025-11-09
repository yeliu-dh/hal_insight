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
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



#RESUME : 
from transformers import pipeline
from sentence_transformers import SentenceTransformer


#my utils:
from utils.upload import data_uploader
from utils.auto_completion import auto_completion_by_sim
# from utils.upload import missing_data_warning
# from utils.preprocess import load_external_json
# from utils.preprocess import preprocess_text
# from utils.preprocess import explode_by_col




@st.cache_resource  # ✅ 缓存模型
def load_embedding_model():  
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # return pipeline(
    #     "summarization",
    #     model="plguillou/t5-base-fr-sum-cnndm",
    #     tokenizer="plguillou/t5-base-fr-sum-cnndm",
    #     use_fast=False
    # )
embedding_model =load_embedding_model()




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
    
    # 重新计算按钮

    cols=st.columns([4,1])
    with cols[1]:
        complete_button = st.button("Auto-compléter")
    if complete_button:
        st.session_state.recompute = True

    # 只有点击按钮或第一次进入才执行
    if st.session_state.get("recompute", True):
        try:
            auto_completion_by_sim(df, embedding_model)
            st.success("✅ SUCCES")
        except Exception as e:
            st.error(f"ERROR: {e}")
        
        # 计算完成后关闭标志，下次不自动重新计算
        st.session_state.recompute = False



