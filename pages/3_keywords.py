
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import io

#my utils:
from utils.upload import csv_uploader

st.set_page_config(page_title="☁️ Keywords & Répartition", page_icon="🛸", layout="wide")
st.title("☁️ Keywords")


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
csv_uploader()# 调用上传器（会自动处理已有/新上传）
if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:

    # -------------------------------
    # 3️⃣ 点击开始统计按钮
    # -------------------------------
    col1, col2 = st.columns([5, 1])  # 最右边一列放按钮
    with col2:
        summary_button = st.button("Commencer")

    if not st.session_state.started:#未开始
        if summary_button:#点击了开始按钮
            # if st.session_state.uploaded_df is not None:#且已经上传数据
            st.session_state.started = True#更新为“开始状态”，df储存在session中，数据不会在变化?            
        
    # -------------------------------
    # # 4️⃣ 分析界面
    # # -------------------------------
        
    if st.session_state.started:
        df = st.session_state.uploaded_df.copy()

        # -------------------- 关键词词云 --------------------        
        # 选择文章范围
        option = st.radio("Choisir la granularité temporelle", ["keywords", "abstract"], horizontal=True)
        
        try:
            if option == "keywords" and "keyword_s" in df.columns:
                st.info(f"⚠️ Les mots clés sont manquants dans {df.keyword_s.isna().sum()} "
                        f"({df.keyword_s.isna().sum()*100/len(df):.2f}%) articles!")
                text = " ".join(df["keyword_s"].dropna().astype(str)).lower()

            elif option == "abstract" and "abstract_s" in df.columns:
                st.info(f"⚠️ Les résumés sont manquants dans {df.abstract_s.isna().sum()} "
                        f"({df.abstract_s.isna().sum()*100/len(df):.2f}%) articles!")
                text = " ".join(df["abstract_s"].dropna().astype(str)).lower()

            else:
                st.warning("⚠️ La colonne sélectionnée n'existe pas dans le fichier CSV.")

        except Exception as e:
            st.error(f"⚠️ {e}")

        # --------------- max words ------------------
        max_words = st.number_input(
            "max_words:", 
            min_value=1, max_value=1000, value=100, step=1, key="max_words"
        )

        # ----------------- stopwords ---------------
        user_stopwords = st_tags(
            label="Ajouter des mots à ignorer",
            text="Tapez un mot et appuyez sur Entrée",
            value=[],
            maxtags=50
        )
        french_stopwords = {"et", "de", "la", "le", "les", "des", "un", "une", "du", "en", "au"}
        stopwords = set(STOPWORDS).union(french_stopwords).union(user_stopwords)

        # ------------ wordcloud ---------------------------
        wc = WordCloud(
            width=800,
            height=400,
            background_color="white",
            max_words=max_words,
            stopwords=stopwords,
            colormap="viridis"
        ).generate(text)

        st.image(wc.to_array(), use_container_width=True)

        # ------------------ 下载 PNG ------------------
        try:
            img = Image.fromarray(wc.to_array())
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            cols = st.columns([4,1])  # 4:1 比例，右侧放按钮    
            with cols[1]:
                st.download_button(
                    label="Télécharger",
                    data=buf,
                    file_name="worldcloud.png",
                    mime="image/png"
                )
        except Exception as e:
            st.error(f"ERROR :{e}")
