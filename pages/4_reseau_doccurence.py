import streamlit as st
from streamlit_tags import st_tags
import numpy as np
# import igraph as ig #非纯py，不适合安装在st cloud
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


#my utils
from utils.upload import data_uploader, missing_data_warning
# from utils.wordcloud import preprocess_text#clean keywords and abstracts
# from utils.wordcloud import collect_clean_texts_by_col#fr/en
# from utils.wordcloud import explode_by_col# authorsname, 
from utils.reseau import generate_network

st.set_page_config(page_title="HAL insight", page_icon="🛸",layout="wide")
st.title("🌐Réseau d'occurences ")

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
st.divider() 

if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    # 若df存在则视为开始
    st.session_state.started=True
    df = st.session_state.uploaded_df.copy()
        

#=======================================================================================#
    st.subheader("🔢 Modifier les paramètres")

    # ---------------TEXTE-------------------
    WC_MAP={"keyword_s":"mots clés",
            "abstract_s":'résumés'}
    
    options = st.multiselect(
    "📑 Choisir le texte:",
    options=["keyword_s", "abstract_s"],
    default=["keyword_s"],  # 默认选择
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

    
    # --------------- top N mots pour un auteur ------------------
    n = st.number_input(
        " ⬆️ Top N mots pour un auteur:", 
        min_value=1, max_value=100, value=10, step=1, key="top_n"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --------------- min_freq ------------------
    min_freq = st.number_input(
        "⬇️​ Fréquence minimale (>=):", 
        min_value=1, max_value=100, value=3, step=1, key="min_freq"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    

    # #----------------------------langue?----------------------
    # wc_par_lang = st.checkbox("Afficher par langue ?", value=False, key="wc_lang")#key用于储存在session state中
    # missing_data_warning(df, col="language_s", map={"language_s":'langue'}, show_distribution=True)



    #==========================générer================================
    cols=st.columns([4,1])
    with cols[1]:   
        button=st.button("Générer")  
    st.divider()

    if button:    
        with st.spinner("Générer..."):
            st.markdown(
                f"<h3 style='text-align: center;'>Réseau d'occurence auteurs-mots clés</h3>",
                unsafe_allow_html=True
            ) #居中显示大标题
            generate_network(df, options,n=n, stopwords=user_stopwords, min_freq=min_freq)

