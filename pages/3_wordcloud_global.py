
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


#my utils:分行导入，不然容易失败
from utils.upload import data_uploader, missing_data_warning
from utils.wordcloud import preprocess_text
from utils.wordcloud import collect_clean_texts_by_col
from utils.wordcloud import generate_wc
from utils.wordcloud import generate_wc_param

# #------------CACHE--------------
# @st.cache_resource
# def load_spacy_models():
#     nlp_fr = spacy.load("fr_core_news_sm")
#     nlp_en = spacy.load("en_core_web_sm")
#     return nlp_fr, nlp_en


st.set_page_config(page_title="HAL insight", page_icon="🛸")
st.title("☁️ Nuage de mots global ")


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

    # -----------------PART1 总体词云 ----------------------------------
    # param:
    # if "overall_wc" not in st.session_state:
    #     st.session_state["overall_wc"] = None
    
    #--------period in years--------------------
    df = st.session_state.uploaded_df.copy()
    ## move to generate_wc_param:

    # if "submittedDate_s" in df.columns:
    #     df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
    #     latest_date = df["submittedDate_s"].max()
    #     latest_y = latest_date.strftime("%Y") if pd.notnull(latest_date) else "Aucune date valide"

    #     earliest_date=df["submittedDate_s"].min()
    #     earliest_y = earliest_date.strftime("%Y") if pd.notnull(latest_date) else "Aucune date valide"
    #     period_y=f"{earliest_y}~{latest_y}"#图标题


    # ---------------文本范围-------------------
    WC_MAP={"keyword_s":"mots clés",
            "abstract_s":'résumés'}
    
    options = st.multiselect(
    "📑 Choisir le texte:",
    options=["keyword_s", "abstract_s"],
    default=["keyword_s","abstract_s"],  # 默认选择
    format_func=lambda x: WC_MAP[x]#只改变显示
    )

    for col in options:
        missing_data_warning(df, col=col, map=WC_MAP,show_distribution=False)
    st.markdown("<br>", unsafe_allow_html=True)#不容易被 Markdown 渲染压缩掉


    # ----------------- user stopwords ---------------
    user_stopwords = st_tags(
        label="🗷 Ajouter des mots à ignorer",
        text="Tapez un mot et appuyez sur Entrée",
        value=["management","gestion","marketing", "recherche",'research','study',"social","use","cas"],
        maxtags=50
    )
    st.markdown("<br>", unsafe_allow_html=True)

    #-----------nltk stopwords----------------
    stop_en=['won', 'an', 'having', "mightn't", 'the', "hasn't", 'more', 'in', 'only', 'under',
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
            'what', 'he', "i'll", 'very', 'how', 'wasn', 'she', "weren't", 'm', 'their', 'which', 'it', 're', "article",
            'research']    

    stop_fr=['j', 'avions', 'avez', 'ta', 'son', 'avais', 'étaient', 'une', 'ai', 'seront', 'il', 'soient', 'étions',
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
               'toi', 'ou', "être", "avoir","faire", "et", "de", "la", "le", "les","l","l'", "des", "un", "une", 
                "du", "en", "au","d","dans","à","par","pour","sur","sont","aux","au", "leur","leurs","qui","ou","il","elle","ils","elles",
                "je","tu","vous","nous","se","et","ce",'qui','que',"est","qu","avec","ont","ces",'celle','ceux','celles',
                'comme','afin','ne',"son",'ses',"none","nan"
            ]    
    # 转小写+去重
    stopwords = set(w.lower() for w in (stop_en + stop_fr + user_stopwords))

    # --------------- max words ------------------
    max_words = st.number_input(
        "⬆️ Nombre de mots maximum affichés:", 
        min_value=1, max_value=1000, value=100, step=1, key="max_words"
    )
    st.markdown("<br>", unsafe_allow_html=True)


    # ------------ctg-------------------
    #radio多选,checkbox单选
    COL_MAP = {
        "Global": "global",
        "Axe": "par axe",
        "Cl. FNEGE": "par classe FNEGE"
    }
    group_by = st.radio(
        "☐ Group :",
        ["Global", "Axe","Cl. FNEGE"], 
        index=0,
        format_func=lambda x: COL_MAP.get(x, x), 
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    #-----------langue----------------------
    wc_par_lang = st.checkbox("Afficher par langue ?", value=False, key="wc_lang")#key用于储存在session state中
    missing_data_warning(df, col="language_s", map={"language_s":'langue'}, show_distribution=True)

    #--------------inclure nan--------------
    include_nan = st.checkbox("Inclure les valeurs Nan? ", value=False, key="nan")


    #------------------traiter les textes-------------------
    # if group_by == "Global":
    #     text_groups = collect_clean_texts_by_col(df, options, stopwords, col="Global")
    # elif group_by == "Axe":
    #     text_groups = collect_clean_texts_by_col(df, options,stopwords, col="Axe")
    # elif group_by == "Cl. FNEGE":
    #     text_groups = collect_clean_texts_by_col(df, options,stopwords, col="Cl. FNEGE")
  
    # group_by_readable=COL_MAP.get(group_by, group_by)


    # 按钮生成+储存
    cols=st.columns([4,1])
    with cols[1]:   
        overall_button=st.button("Générer")      

    if overall_button:
        with st.spinner("Générer..."):
            wc=generate_wc_param(df, options, group_by, wc_par_lang, include_nan, max_words, stopwords)
            st.pyplot(wc)

            # if not wc_par_lang:  # 不分语言 → 合并 EN + FR
            #     title=f"Nuage de mots {group_by_readable} entre {period_y}"
            #     for cat, langs in text_groups.items(): 
            #         combined_text = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
                    
            #         if group_by=="Global":
            #             title=" "
            #         else:
            #             title=f"{group_by} {cat}"

            #         if combined_text:
            #             global_wc = generate_wc(
            #                 langs.get("en", "") + " " + langs.get("fr", ""),  # lang 随便传一个
            #                 max_words,
            #                 stopwords,
            #                 title=title
            #             )
            #             st.pyplot(global_wc)
            # else:
            #     # 分语言 → EN/FR 左右列显示，每个类别单独一行
            #     st.subheader(f"Nuage de mots {group_by_readable} par langue entre {period_y}")
            #     for cat, langs in text_groups.items():
            #         cols = st.columns(2)
            #         for i, lang in enumerate(langs.keys()):
            #             with cols[i]:
            #                 if group_by=="Global":
            #                     title=lang
            #                 else:
            #                     title=f"{group_by} {cat}-{lang}"
                            
            #                 text = langs.get(lang, "").strip()
            #                 if text:
            #                     wc = generate_wc(text, max_words, stopwords, title=title)
            #                     st.pyplot(wc)
            #                 else :
            #                     st.warning(f"texte invalie dans la catégorie {cat}-{lang}!")
