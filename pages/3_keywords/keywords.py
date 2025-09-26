import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt


st.title("☁️ Wordcloud")
st.markdown("Quels sont les mots clés les plus utilisés dans ce corpus ?")


        
        # # -------------------- 关键词词云 --------------------
        # st.header("☁️ Nuage des mots clés")
        # # -------------------------------
        #     # 4b. 选择文章范围
        #     # -------------------------------
        #     text = st.radio("Choisir la granularité temporelle", ["keywords", "abstract"], horizontal=True)
        #     if text == "keywords" :
        #         df["Period"] = df["publicationDate_s"].dt.to_period("M").astype(str)
        #     else:
        #         df["Period"] = df["publicationDate_s"].dt.to_period("Y").astype(str)


        # if "keyword_s" in df.columns:
        #     st.info(f"⚠️ Les mots clés sont manquants dans {df.keyword_s.isna().sum()} ({df.keyword_s.isna().sum()*100/len(df):.2f}%) articles!")
        #     keywords_text = " ".join(df["keyword_s"].dropna().astype(str)).lower()


        #     max_words = st.number_input(
        #         f"max_words:", 
        #         min_value=1, max_value=1000, value=100, step=1, key="max_words"
        #     )

        #     #-----------------stopwords---------------
        #     #自定义停用
        #     user_stopwords = st_tags(
        #         label="Ajouter des mots à ignorer",
        #         text="Tapez un mot et appuyez sur Entrée",
        #         value=[],
        #         maxtags=50
        #     )
        #     #法语停用词
        #     french_stopwords = {"et", "de", "la", "le", "les", "des", "un", "une", "du", "en", "au"}
        #     stopwords = set(STOPWORDS).union(french_stopwords).union(user_stopwords)

        #     wc = WordCloud(
        #         width=800,
        #         height=400,
        #         background_color="white",
        #         max_words=max_words,
        #         stopwords=stopwords,
        #         colormap="viridis"
        #     ).generate(keywords_text)

        #     st.image(wc.to_array(), use_container_width=True)

        #     # ------------------ 下载 PNG ------------------
        #     try:
        #         img = Image.fromarray(wc.to_array())
        #         buf = io.BytesIO()
        #         img.save(buf, format="PNG")
        #         buf.seek(0)

        #         cols = st.columns([4,1])  # 4:1 比例，右侧放按钮    
        #         with cols[1]:
        #             st.download_button(
        #                 label="Télécharger",
        #                 data=buf,
        #                 file_name=f"worldcloud.png",
        #                 mime="image/png"
        #             )

        #     except Exception as e:
        #         st.error(f"ERROR :{e}")
