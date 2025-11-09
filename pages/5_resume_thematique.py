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
from transformers import T5Tokenizer, T5ForConditionalGeneration


#my utils:
from utils.upload import data_uploader
from utils.auto_completion import auto_completion_by_sim
from utils.summarization import extract_thema_chunks, generate_summaries


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


def load_tokenizer():
    return  T5Tokenizer.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#分词模型
tokenizer = load_tokenizer()


def load_summary_model():
    return T5ForConditionalGeneration.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#摘要模型
summary_model = load_summary_model()



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
    
    # st.subheader("🔢 Auto-completion des axes thématiques")
    
    # # 重新计算按钮

    # cols=st.columns([4,1])
    # with cols[1]:
    #     complete_button = st.button("Auto-compléter")
    # if complete_button:
    #     st.session_state.recompute = True

    # # 只有点击按钮或第一次进入才执行
    # if st.session_state.get("recompute", True):
    #     try:
    #         df_exploded=auto_completion_by_sim(df, embedding_model)
    #         # st.success("✅ SUCCES")
    #     except Exception as e:
    #         st.error(f"ERROR: {e}")
        
    #     # 计算完成后关闭标志，下次不自动重新计算
    #     st.session_state.recompute = False



    # st.subheader("🔢 Summarisation par axe thématique")
    # cols=st.columns([4,1])
    # with cols[1]:
    #     summary_button = st.button("Résumer")
    # if summary_button:
    #     st.session_state.recompute = True

    #     if st.session_state.get("recompute", True) and df_exploded:
    #         try:
    #            axe_groups=extract_thema_chunks(df_exploded,embedding_model)
    #            generate_summaries(axe_groups, tokenizer,summary_model)
    #         except Exception as e:
    #             st.error(f"ERROR: {e}")
            
    #         # 计算完成后关闭标志，下次不自动重新计算
    #         st.session_state.recompute = False



    st.subheader("🔢 Auto-completion des axes thématiques")

    # 创建重新计算标志
    if "recompute_auto" not in st.session_state:
        st.session_state.recompute_auto = False

    cols = st.columns([4, 1])
    with cols[1]:
        complete_button = st.button("Auto-compléter")

    # 点击按钮触发重新计算
    if complete_button:
        st.session_state.recompute_auto = True

    # 执行 auto_completion_by_sim，只在需要时
    if st.session_state.recompute_auto or "df_exploded" not in st.session_state:
        try:
            # 假设 df 已经存在 session_state 或其他变量
            df_exploded = auto_completion_by_sim(st.session_state.uploaded_df, embedding_model)

            # 保存到 session_state，方便下次直接使用
            st.session_state.df_exploded = df_exploded

            # 删除原始 df（可选，释放内存）
            # del st.session_state.uploaded_df

        except Exception as e:
            st.error(f"ERROR: {e}")

        # 重置标志
        st.session_state.recompute_auto = False
    else:
        df_exploded = st.session_state.df_exploded  # 直接复用 session_state

    # =================== 主题摘要部分 ===================
    st.subheader("🔢 Summarisation par axe thématique")

    if "recompute_summary" not in st.session_state:
        st.session_state.recompute_summary = False

    cols = st.columns([4, 1])
    with cols[1]:
        summary_button = st.button("Résumer")

    if summary_button:
        st.session_state.recompute_summary = True

    # 执行摘要，只在需要时
    if st.session_state.recompute_summary:
        if "df_exploded" in st.session_state:
            try:
                axe_groups = extract_thema_chunks(st.session_state.df_exploded, embedding_model)
                summaries = generate_summaries(axe_groups, tokenizer, summary_model)

                # 保存摘要结果到 session_state
                st.session_state.summaries = summaries

                # 如果想节省内存，可以删除中间对象
                # del axe_groups

            except Exception as e:
                st.error(f"ERROR: {e}")

        # 重置标志
        st.session_state.recompute_summary = False
