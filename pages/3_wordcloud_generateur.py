
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import io
import math

import re
import spacy
from nltk.corpus import stopwords
import nltk

#my utils:
from utils.upload import data_uploader
from utils.worldcould import collect_texts_by_language
from utils.worldcould import preprocess_text
from utils.worldcould import generate_wc
from utils.worldcould import generate_keyness_wc

#------------CACHE--------------

# 下载停用词 (只会运行一次，缓存)
# @st.cache_resource
# def load_nltk_resources():
#     nltk.download("stopwords")
#     stop_fr = set(stopwords.words("french"))
#     stop_en = set(stopwords.words("english"))
#     return stop_fr, stop_en


# 加载 spacy 语言模型
@st.cache_resource
def load_spacy_models():
    try:
        nlp_fr = spacy.load("fr_core_news_sm")
    except OSError:
        from spacy.cli import download
        download("fr_core_news_sm")
        nlp_fr = spacy.load("fr_core_news_sm")

    try:
        nlp_en = spacy.load("en_core_web_sm")
    except OSError:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp_en = spacy.load("en_core_web_sm")

    return nlp_fr, nlp_en


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

    # ---PART1 总体词云 ---
    st.subheader("Nuage de mots global")
    # param:
    if "overall_wc" not in st.session_state:
        st.session_state["overall_wc"] = None

   # ---------------文本范围-------------------
    WC_MAP={"keyword_s":"mots clés",
            "abstract_s":'résumés'}
    
    options = st.multiselect(
    "Choisir le texte:",
    options=["keyword_s", "abstract_s"],
    default=["keyword_s","abstract_s"],  # 默认选择
    format_func=lambda x: WC_MAP[x]#只改变显示
    )


    try:
        if options:
            text_en, text_fr=[],[]
            text_by_lang=collect_texts_by_language(df, options, lang_col="language_s", langs=("en", "fr"))
            text_en.append(text_by_lang.get('en',[]))
            text_fr.append(text_by_lang.get('en',[]))

        else:
            st.warning("⚠️ Aucune colonne sélectionnée ou inexistante dans le CSV.")
            text_en = ""
            text_fr = ""

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
        value=["management","gestion","marketing"],
        maxtags=50
    )

    #nltk stopwords
    stop_en={'won', 'an', 'having', "mightn't", 'the', "hasn't", 'more', 'in', 'only', 'under',
             'o', 'ain', 'can', 'some', 'with', 'these', 'had', 'they', 'me', 'its', 'such', "wouldn't", 
             'as', 'own', "they'd", 'weren', 'or', "shan't", 'don', 'him', 'yours', 'after', 'so', 
             "don't", 'down', 't', 'hadn', "she'll", 'been', 'y', 'whom', 'because', 'about', 'am',
             'my', 'there', 'here', 'up', 'on', 'those', 'once', 'hers', 'too', 'this', 'do', 'further',
             'not', 'at', 'any', 'for', 'haven', 'ours', 'then', 'we', 'each', 'than', "she's", 'herself', 
             "i'm", 's', 'did', 'didn', "i'd", 'shouldn', 'himself', 'you', 'other', 'why', "he'll", 'nor', 
             "needn't", 'couldn', 'needn', 'should', 'where', "haven't", 'i', 'being', "they'll", "he's", 'from',
             'mustn', "we'll", "wasn't", "should've", 'of', 'now', 'until', 'all', 'has', "shouldn't", 'his', 
             "you'll", "it'd", 'll', "they're", "it's", 'does', 'no', 'while', 'into', "that'll", 'itself', 
             'your', 'were', 'above', "it'll", 'ma', 'doing', "mustn't", 'between', 'them', 'and', "they've", 
             'are', 'our', 'off', "i've", 'most', 'out', "won't", 'before', 'will', 'shan', "we're", 'who', "you're",
             'doesn', 'hasn', 'have', 'against', 'just', 'yourselves', 'be', 'is', "isn't", 'a', "aren't", 
             'again', "you'd", "hadn't", 'that', 'but', 'when', "didn't", 'ourselves', "doesn't", 've', 'yourself', 
             'myself', "couldn't", 'd', 'was', "you've", 'both', 'themselves', 'if', 'over', "she'd", 'few', 'her', "he'd",
             'through', 'wouldn', "we'd", 'below', 'theirs', 'aren', 'to', "we've", 'same', 'mightn', 'isn', 'by', 'during',
               'what', 'he', "i'll", 'very', 'how', 'wasn', 'she', "weren't", 'm', 'their', 'which', 'it', 're'}
    

    stop_fr={'j', 'avions', 'avez', 'ta', 'son', 'avais', 'étaient', 'une', 'ai', 'seront', 'il', 'soient', 'étions',
              'sommes','serai', 'me', 'l', 'est', 'tes', 'aurez', 'ayons', 'as', 'elle', 'eusses', 'été', 'fût', 
              'par', 't', 'auraient', 'et', 'notre', 'y', 'aie', 'eux', 'leur', 'le', 'on', 'avaient', 'ont',
              'eue', 'aurait', 'aies', 'eussent', 'eut', 'soit', 'sur', 'avec', 'serions', 'ses', 'n', 'du', 
              'aurions', 'ils', 'es', 'un', 's', 'vous', 'dans', 'qui', 'étée', 'auriez', 'aient', 'je', 'étante',
             'étant', 'fusses', 'mon', 'eurent', 'nous', 'êtes', 'serez', 'auront', 'fut', 'ayants', 'aurais', 'même',
               'fussent', 'auras', 'qu', 'fûtes', 'étiez', 'seras', 'fussions', 'soyez', 'les', 'sois', 'aviez', 'mes', 
               'serait', 'étantes', 'furent', 'eu', 'moi', 'seriez', 'sa', 'avait', 'sera', 'étés', 'ayante', 'fus', 
               'eûtes', 'ma', 'ayantes', 'eusse', 'à', 'se', 'ton', 'en', 'au', 'serons', 'suis', 'ayant', 'ces', 'te', 
               'lui', 'nos', 'des', 'aux', 'eussiez', 'pour', 'eues', 'ne', 'aurons', 'que', 'fussiez', 'tu', 'eussions', 
               'd', 'étants', 'ce', 'étais', 'était', 'serais', 'étées', 'mais', 'eus', 'eût', 'ayez', 'votre', 'seraient', 
               'fusse', 'ait', 'de', 'c', 'la', 'soyons', 'aurai', 'vos', 'fûmes', 'pas', 'm', 'sont', 'aura', 'avons', 'eûmes', 
               'toi', 'ou'}

    #  = {"et", "de", "la", "le", "les","l","l'", "des", "un", "une", 
    #                     "du", "en", "au","d","dans","à","par","pour","sur","sont","aux","au",
    #                     "leur","leurs","qui","ou","il","elle","ils","elles","je","tu","vous","nous","se",
    #                     "et","ce",'qui','que',"est","qu","avec","ont","ces",'celle','ceux','celles',
    #                     'comme','afin','ne',"son",'ses'}
    
    stopwords=set(stop_en).union(stop_fr).union(user_stopwords)
    
    # 按钮生成+储存
    overall_button=st.button("Générer")
    if overall_button:
        with st.spinner("🔄 Charger le modèle pour la lemmatisation..."):
            nlp_fr, nlp_en = load_spacy_models()

        with st.spinner("🔄 Nettoyage et lemmatisation en cours..."):
            clean_text_en, clean_text_fr = "", ""
            if text_en:
                clean_text_en=" ".join(preprocess_text(text_en, nlp_en, stopwords))
            
            if text_fr:
                clean_text_fr=" ".join(preprocess_text(text_fr, nlp_fr, stopwords))
        
        with st.spinner("🔄 Générer le nuage de mots global:"):
            st.session_state["overall_wc"] = generate_wc(clean_text_en+clean_text_fr, max_words, stopwords, title="Nuage de mots global")

            # 渲染
            if st.session_state["overall_wc"] is not None:
                st.pyplot(st.session_state["overall_wc"])




    # # ------------------PART2 演变词云 --------------------------
    # st.subheader("Nuage de mots évolutif")
    # if "evolutif_wc" not in st.session_state:
    #     st.session_state["evolutif_wc"] = None
        
    # # param
    # df = st.session_state.uploaded_df.copy()
    # df["publicationDate_s"] = pd.to_datetime(df["publicationDate_s"], errors="coerce")
    # df["year"] = df["publicationDate_s"].dt.year

    # # ---------------文本范围-------------------
    # option = st.multiselect(
    # "Choisir la granularité temporelle",
    # ["keywords", "abstract"],
    # default=["keywords"]  # 默认选 keywords，你可以改成 []
    # )

    # try:
    #     texts = []
    #     if "keywords" in option and "keyword_s" in df.columns:
    #         st.info(f"⚠️ Les mots clés sont manquants dans {df.keyword_s.isna().sum()} "
    #                 f"({df.keyword_s.isna().sum()*100/len(df):.2f}%) articles!")
    #         texts.append(" ".join(df["keyword_s"].dropna().astype(str)).lower())

    #     if "abstract" in option and "abstract_s" in df.columns:
    #         st.info(f"⚠️ Les résumés sont manquants dans {df.abstract_s.isna().sum()} "
    #                 f"({df.abstract_s.isna().sum()*100/len(df):.2f}%) articles!")
    #         texts.append(" ".join(df["abstract_s"].dropna().astype(str)).lower())

    #     if texts:
    #         text = " ".join(texts)   # 拼接两个来源的文本
    #     else:
    #         st.warning("⚠️ Aucune colonne sélectionnée ou inexistante dans le CSV.")
    #         text = ""

    # except Exception as e:
    #     st.error(f"⚠️ {e}")


    # # ---------------- 用户输入 ----------------
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     start_year = st.number_input("Année de début", min_value=1900, max_value=2100, value=2010)
    # with col2:
    #     end_year = st.number_input("Année de fin", min_value=1900, max_value=2100, value=2020)
    # with col3:
    #     step_year = st.number_input("Intervalle de temps", min_value=1, max_value=20, value=3)

    # # ---------------- 时间段切片 ----------------
    # time_slices = [(y, min(y + step_year - 1, end_year)) for y in range(start_year, end_year+1, step_year)]

    # # --------------- max words ------------------
    # max_words = st.number_input(
    #     "max_words:", 
    #     min_value=1, max_value=1000, value=100, step=1, key="max_words"
    # )

    # # ----------------- stopwords ---------------
    # user_stopwords = st_tags(
    #     label="Ajouter des mots à ignorer",
    #     text="Tapez un mot et appuyez sur Entrée",
    #     value=[],
    #     maxtags=50
    # )
    # french_stopwords = {"et", "de", "la", "le", "les","l","l'", "des", "un", "une", 
    #                     "du", "en", "au","d","dans","à","par","pour","sur","sont","aux","au",
    #                     "leur","leurs","qui","ou","il","elle","ils","elles","je","tu","vous","nous","se",
    #                     "et","ce",'qui','que',"est","qu","avec","ont","ces",'celle','ceux','celles',
    #                     'comme','afin','ne',"son",'ses'}
    
    
    # stopwords = set(STOPWORDS).union(french_stopwords).union(user_stopwords)


    # # ---------------- 生成 keyness 词云 ----------------

    # # 按钮生成+储存
    # evolutif_button=st.button("Générer")
    # if evolutif_button:
    #     st.session_state["evolutif_wc"] = (generate_wc(text, max_words, stopwords, title="Nuage de mots global"))

    # # 渲染
    # if st.session_state["evolutif_wc"] is not None:
    #     st.pyplot(st.session_state["evolutif_wc"])


    # if st.button("Générer"):
    #     st.session_state["evolutif_wc"] = generate_keyness_wc(
    #     df,
    #     time_slices,
    #     max_words=max_words,
    #     stopwords=stopwords,
    #     method="llr"  # 或 "chi2"
    # )

    # if st.session_state["evolutif_wc"] is not None:
    #     st.pyplot(st.session_state["evolutif_wc"])


    # # # 这里示例用简单频率代替 keyness
    # # # 如果需要严格 keyness，可用 log-likelihood 或 chi-square

    # # texts_all = " ".join(df["keyword_s"].dropna().astype(str).str.lower())
    # # global_freq = pd.Series(texts_all.split()).value_counts()

    # # n_cols = 3
    # # n_rows = math.ceil(len(time_slices)/n_cols)
    # # fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols*5, n_rows*5))

    # # for idx, (y_start, y_end) in enumerate(time_slices):
    # #     df_slice = df[(df["year"] >= y_start) & (df["year"] <= y_end)]
    # #     if df_slice.empty:
    # #         text = ""
    # #     else:
    # #         text = " ".join(df_slice["keyword_s"].dropna().astype(str).str.lower())

    # #     # 简单 keyness：词频 / 全局词频
    # #     freq_slice = pd.Series(text.split()).value_counts()
    # #     keyness = (freq_slice / global_freq).fillna(0).to_dict()

    # #     wc = WordCloud(width=400, height=400, background_color="white").generate_from_frequencies(keyness)

    # #     row, col = divmod(idx, n_cols)
    # #     ax = axes[row, col] if n_rows>1 else axes[col]
    # #     ax.imshow(wc, interpolation="bilinear")
    # #     ax.set_title(f"{y_start}-{y_end}", fontsize=12)
    # #     ax.axis("off")

    # # # 删除多余子图
    # # for j in range(idx+1, n_rows*n_cols):
    # #     row, col = divmod(j, n_cols)
    # #     ax = axes[row, col] if n_rows>1 else axes[col]
    # #     ax.axis("off")

    # # st.pyplot(fig)













    # # -------------------------------
    # # # 3️⃣ 点击开始统计按钮
    # # # -------------------------------
    # # col1, col2, col3 = st.columns([4, 1, 1])  # 最右边一列放按钮
    # # with col2:
    # #     summary_button1 = st.button("Wordcloud global")
    
    # # with col3:
    # #     summary_button2 = st.button("Wordcloud évolutif")

    # # if not st.session_state.started:#未开始
    # #     if summary_button1 or summary_button2:#点击了开始按钮
    # #         # if st.session_state.uploaded_df is not None:#且已经上传数据
    # #         st.session_state.started = True#更新为“开始状态”，df储存在session中，数据不会在变化?            
        
    # # -------------------------------
    # # # 4️⃣ 分析界面
    # # # -------------------------------

    # # if st.session_state.started and summary_button1:
    # #     df = st.session_state.uploaded_df.copy()

    # #     # -------------------- 关键词词云 --------------------        
    # #     # 选择文章范围
    # #     option = st.radio("Choisir la granularité temporelle", ["keywords", "abstract"], horizontal=True)
        
    # #     try:
    # #         if option == "keywords" and "keyword_s" in df.columns:
    # #             st.info(f"⚠️ Les mots clés sont manquants dans {df.keyword_s.isna().sum()} "
    # #                     f"({df.keyword_s.isna().sum()*100/len(df):.2f}%) articles!")
    # #             text = " ".join(df["keyword_s"].dropna().astype(str)).lower()

    # #         elif option == "abstract" and "abstract_s" in df.columns:
    # #             st.info(f"⚠️ Les résumés sont manquants dans {df.abstract_s.isna().sum()} "
    # #                     f"({df.abstract_s.isna().sum()*100/len(df):.2f}%) articles!")
    # #             text = " ".join(df["abstract_s"].dropna().astype(str)).lower()

    # #         else:
    # #             st.warning("⚠️ La colonne sélectionnée n'existe pas dans le fichier CSV.")

    # #     except Exception as e:
    # #         st.error(f"⚠️ {e}")

    # #     # --------------- max words ------------------
    # #     max_words = st.number_input(
    # #         "max_words:", 
    # #         min_value=1, max_value=1000, value=100, step=1, key="max_words"
    # #     )

    # #     # ----------------- stopwords ---------------
    # #     user_stopwords = st_tags(
    # #         label="Ajouter des mots à ignorer",
    # #         text="Tapez un mot et appuyez sur Entrée",
    # #         value=[],
    # #         maxtags=50
    # #     )
    # #     french_stopwords = {"et", "de", "la", "le", "les","l","l'", "des", "un", "une", 
    # #                         "du", "en", "au","d","dans","à","par","pour","sur","sont","aux","au",
    # #                         "leur","leurs","qui","ou","il","elle","ils","elles","je","tu","vous","nous","se",
    # #                         "et","ce",'qui','que',"est","qu","avec","ont","ces",'celle','ceux','celles',
    # #                         'comme','afin','ne',"son",'ses'}
        
        
    # #     stopwords = set(STOPWORDS).union(french_stopwords).union(user_stopwords)

    # #     # ------------ wordcloud ---------------------------
    # #     wc = WordCloud(
    # #         width=800,
    # #         height=400,
    # #         background_color="white",
    # #         max_words=max_words,
    # #         stopwords=stopwords,
    # #         colormap="viridis"
    # #     ).generate(text)

    #     # st.image(wc.to_array(), use_container_width=True)#图变数组，自适应宽度，不能加标题

    #     # # ------------------ 下载 PNG ------------------
    #     # try:
    #     #     img = Image.fromarray(wc.to_array())
    #     #     buf = io.BytesIO()
    #     #     img.save(buf, format="PNG")
    #     #     buf.seek(0)

    #     #     cols = st.columns([5,1])  # 4:1 比例，右侧放按钮    
    #     #     with cols[1]:
    #     #         st.download_button(
    #     #             label="Télécharger",
    #     #             data=buf,
    #     #             file_name="worldcloud.png",
    #     #             mime="image/png"
    #     #         )
    #     # except Exception as e:
    #     #     st.error(f"ERROR :{e}")


