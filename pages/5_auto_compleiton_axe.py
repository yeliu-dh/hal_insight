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
from sentence_transformers import SentenceTransformer


#my utils:
from utils.upload import data_uploader
from utils.auto_completion import auto_completion_by_sim


# @st.cache_resource  # ✅ 缓存模型
# def load_embedding_model(model_name):
#     return SentenceTransformer(model_name)#向量化模型

# model_name="paraphrase-multilingual-MiniLM-L12-v2"
# embedding_model=load_embedding_model(model_name)

st.set_page_config(page_title="HAL insight", page_icon="🛸",layout="wide")
st.title("📃 Auto-completion des axes")


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

    model_name = st_tags(
        label="Model name",
        text="Tapez et 'Entrée'",
        value=["paraphrase-multilingual-MiniLM-L12-v2"],
        maxtags=1
    )
    # model_name="paraphrase-multilingual-MiniLM-L12-v2"

    st.subheader("🔢 Auto-completion des axes thématiques")
    st.write(f" [README] L'auto-completion des axes thématique prend en compte des titres, des mots-clés et des résumés,  \n"
             f"embeddés par le model {model_name}")
    

    # 重新计算按钮
    cols=st.columns([4,1])
    with cols[1]:
        complete_button = st.button("Auto-compléter")
    if complete_button:
        st.session_state.recompute_completion = True

    # 只有点击按钮或第一次进入才执行
    if st.session_state.get("recompute_completion", True):
        try:
            df_exploded=auto_completion_by_sim(df, model_name)
            st.session_state['df_exploded']=df_exploded
        except Exception as e:
            st.error(f"ERROR in 'auto_completion_by_sim' : {e}")
        
        # 计算完成后关闭标志，下次不自动重新计算
        st.session_state.recompute_completion = False