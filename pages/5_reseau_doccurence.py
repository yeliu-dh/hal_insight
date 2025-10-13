import streamlit as st
import numpy as np
# import igraph as ig
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


#my utils
from utils.upload import data_uploader, missing_data_warning
from utils.wordcloud import preprocess_text#clean keywords and abstracts
from utils.wordcloud import collect_clean_texts_by_col#fr/en
from utils.wordcloud import explode_by_col# authorsname, 


st.set_page_config(page_title="HAL insight", page_icon="🛸",layout="wide")
st.title("☁️ Nuage de mots évolutif ")

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
data_uploader()# 调用上传器（会自动处理已有/新上传）
st.divider() 

if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    # 若df存在则视为开始
    st.session_state.started=True
    df = st.session_state.uploaded_df.copy()
        

#=======================================================================================#
    # ---------------TEXTE-------------------
    WC_MAP={"keyword_s":"mots clés",
            "abstract_s":'résumés'}
    
    options = st.multiselect(
    "📑 Choisir le texte:",
    options=["keyword_s", "abstract_s"],
    default=["keyword_s","abstract_s"],  # 默认选择
    format_func=lambda x: WC_MAP[x]#只改变显示
    )

    for col in options:
        missing_data_warning(df, col=col, map=WC_MAP)
    st.markdown("<br>", unsafe_allow_html=True)#不容易被 Markdown 渲染压缩掉

    # --------------- top K freq d'occurence ------------------
    k = st.number_input(
        "⬆️ Fréquence d'occurence top K:", 
        min_value=1, max_value=100, value=10, step=1, key="max_words"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    #----------------------------langue?----------------------
    wc_par_lang = st.checkbox("Afficher par langue ?", value=False, key="wc_lang")#key用于储存在session state中
    missing_data_warning(df, col="language_s", map={"language_s":'langue'}, show_distribution=True)
