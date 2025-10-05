
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import io
import math
import re
# import spacy
# from nltk.corpus import stopwords
# import nltk
import simplemma

#my utils:
from utils.upload import data_uploader, missing_data_warning
from utils.worldcould import preprocess_text, collect_clean_texts_by_col
from utils.worldcould import preprocess_text
from utils.worldcould import generate_wc,generate_keyness_wc


st.set_page_config(page_title="HAL insight", page_icon="🛸")
st.title("☁️ Wordcloud ")


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

    st.subheader("Nuage de mots évolutif")

    # if "evolutif_wc" not in st.session_state:
    #     st.session_state["evolutif_wc"] = None
    # --------------文本选择---------------------


    
    # ----------------时间颗粒----------------
    if "submittedDate_s" in df.columns:
        df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
        latest_date = df["submittedDate_s"].max()
        latest_ym = latest_date.strftime("%Y-%m") if pd.notnull(latest_date) else "Aucune date valide"

        earliest_date=df["submittedDate_s"].min()
        earliest_ym = earliest_date.strftime("%Y-%m") if pd.notnull(latest_date) else "Aucune date valide"
    
        #time period in month 
        if pd.notnull(earliest_date) and pd.notnull(latest_date):
            period_m = (latest_date.year - earliest_date.year) * 12 + (latest_date.month - earliest_date.month)
        else:
            period_m = 0
        st.write(f"🕒 Période couverte : {earliest_ym} → {latest_ym}  ({period_m} mois)")
            
                
        # ---- 自动推荐时间粒度并设置 radio 默认选项 ----
        if period_m <= 12:#一年内，按月度或者季度显示
            suggestion = "Mensuel ou Trimestriel"
            default_index = 0
        elif period_m <= 60:#3/5年内，按年度显示
            suggestion = "Annuel"
            default_index = 1
        else:
            suggestion = "Tous les 3 ou 5 ans"
            default_index = 2
        st.info(f"💡 Recommandation automatique : nuage de mots évolutif **{suggestion}**.")

        # ---- Radio 选择 ----
        period_level = st.radio(
            "Sélectionnez la granularité temporelle :",
            ["Mensuel / Trimestriel (≤ 1 an)", "Annuel (3–5 ans)", "Tous les 3 ou 5 ans (> 5 ans)"],
            index=default_index,
            horizontal=True,
        )

        # COL_MAP = {
        #     "Global": "global",
        #     "Axe": "par axe",
        #     "Cl. FNEGE": "par classe FNEGE"
        # }
        # group_by = st.radio(
        #     "Afficher :",
        #     ["Global", "Axe","Cl. FNEGE"], 
        #     index=0,
        #     format_func=lambda x: COL_MAP.get(x, x), 
        #     horizontal=True
        # )

