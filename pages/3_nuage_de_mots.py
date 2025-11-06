
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
from utils.upload import load_external_json
from utils.preprocess import preprocess_text
from utils.preprocess import collect_clean_texts_by_col
from utils.wordcloud import generate_wc
from utils.wordcloud import generate_wc_param

from utils.preprocess import explode_by_col
from utils.wordcloud import create_time_slices
from utils.wordcloud import generate_keyness_wc


# #====================CACHE=========================#
# @st.cache_data 
# def get_stopwords():   
#     stopwords_nltk=load_external_json('json_data',"stopwords_nltk")
#     stopwords_nltk=list(stopwords_nltk.values())
#     return stopwords_nltk

# stopwords=get_stopwords()


# st.set_page_config(page_title="HAL insight", page_icon="🛸")
st.title("☁️ Nuage de mots global / évolutif")


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
   
    
    st.subheader("🔢 Modifier les paramètres")
    # ---------------文本范围-------------------
    WC_MAP={"keyword_s":"mots clés",
            "abstract_s":'résumés',
            "full_text":"texte intégral"}
    
    options = st.multiselect(
    "📑 Choisir le texte:",
    options=["keyword_s", "abstract_s","full_text"],
    default=["keyword_s","abstract_s"],  # 默认选择
    format_func=lambda x: WC_MAP[x]#只改变显示
    )
    st.write("Les textes sélectionnés sont nettoyés (suppression des espaces, ponctuations et mots grammaticaux courants), mis en minuscules et lemmatisés.")


    for col in options:
        missing_data_warning(df, col=col, map=WC_MAP,show_distribution=False)
    st.markdown("<br>", unsafe_allow_html=True)#不容易被 Markdown 渲染压缩掉

  # ------------gourpby-------------------
    #radio多选,checkbox单选
    COL_MAP = {
        "Global": "global",
        "Axe": "par axe",
        "Cl. FNEGE": "par classe FNEGE"
    }
    group_by = st.radio(
        "💾 Groupe des textes :",
        ["Global", "Axe"],#"Cl. FNEGE" 
        index=0,
        format_func=lambda x: COL_MAP.get(x, x), 
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    
    #---------------langue-------------------
    wc_par_lang = st.checkbox("Afficher par langue ?", value=False, key="wc_lang")#key用于储存在session state中
    st.write("(Si vous choisissez le nuage de mots évolutif, il n’est pas séparé par langue.)")
    missing_data_warning(df, col="language_s", map={"language_s":'langue'}, show_distribution=True)


    #--------------exclure nan--------------
    exclude_nan = st.checkbox("Exclure les lignes sans étiquette d'axe ? ", value=True, key="nan")
    st.divider()




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

                
        # # ---- 自动推荐时间粒度并设置 radio 默认选项 ----
        if period_m <= 12:#一年内，按月度或者季度显示
            suggestion = "Mensuel ou Trimestriel"
            default_index = 2
        elif period_m <= 60:#3/5年内，按年度显示
            suggestion = "Annuel"
            default_index = 3
        else:
            suggestion = "Tous les 3 ou 5 ans"
            default_index = 4

        if wc_par_lang :#若按照语言分，则选择全时间段
            default_index=0

        # ----radio ----
        granularity = st.radio(
            "🕒 Granularité temporelle :",
            ["Toute la période → wc global","Mensuel","Trimestriel", "Annuel", "Tous les 3 ans","Tous les 5 ans"],
            index=default_index,
            horizontal=True,
        )  
        if granularity!="Toute la période → wc global":
            time_slices=create_time_slices(df, granularity=granularity)
  
        st.info(f"Période couverte : {earliest_ym} → {latest_ym}  ({period_m} mois).\n\n"
                f"Granularité recommandée pour le nuage de mots évolutif: **{suggestion}**. \n\n"
                f"Le nuage de mots évolutif est calculé à l'aide de méthode de **keyness**, mettant en évidence les mots caractéristiques de chaque période.")
        
      
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ----------------- user stopwords ---------------
    user_stopwords = st_tags(
        label="🗷 Ajouter des mots à ignorer",
        text="Tapez un mot et appuyez sur Entrée",
        value=["management","gestion","marketing", "recherche",'research','study',"social","use","cas","article",'entreprise'],
        maxtags=50
    )
   
    st.markdown("<br>", unsafe_allow_html=True)

   
    # --------------- max words ------------------
    max_words = st.number_input(
        "⬆️ Nombre de mots maximum affichés:", 
        min_value=1, max_value=1000, value=50, step=1, key="max_words"
    )
    st.markdown("<br>", unsafe_allow_html=True)


    
    

    # 按钮生成+储存
    cols=st.columns([4,1])
    with cols[1]:   
        generate_button=st.button("Générer")      


    if generate_button :
        if granularity=="Toute la période → wc global":
            with st.spinner("Générer le nuage de mots global..."):
                try :
                    wc=generate_wc_param(df, options, group_by, wc_par_lang, exclude_nan, max_words, user_stopwords)
                    st.pyplot(wc)
                except Exception as e:
                        st.write(f"ERROR dans le nuage de mots global: {e}")

        elif generate_button and time_slices is not None:# granlarity → évolutif
            with st.spinner("Générer le nuage de mots évolutif..."):
                if group_by=="Global":
                    try:
                        evolutif_wc= generate_keyness_wc(df, options, exclude_nan, group_by, time_slices=time_slices, max_words=max_words, stopwords=user_stopwords, method="llr")
                        st.pyplot(evolutif_wc)
                    except Exception as e:
                        st.write(f"ERROR dans le nuage de mots évolutif global : {e}")

                # elif group_by=="Axe" or groupby=="":
                else:
                    #-----居中显示所有演变图的大标题------
                    df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
                    start_ym=df["submittedDate_s"].min().strftime("%Y-%m")
                    end_ym=df["submittedDate_s"].max().strftime("%Y-%m")  
                    
                    st.markdown(
                        f"<h3 style='text-align: center;'>Évolution du nuage de mots ({start_ym} ~ {end_ym})</h3>",
                        unsafe_allow_html=True
                    ) 

                    exploded_df=explode_by_col(df, col=group_by)#已fillna
                    if exclude_nan:
                        ctg=sorted([v for v in exploded_df[group_by].unique() if v !="nan"])
                    else :                
                        ctg=sorted(exploded_df[group_by].unique())

                    for col_val in ctg :
                        df_slice=exploded_df[exploded_df[group_by]==col_val]
                        try :
                            evolutif_wc_by_axe=generate_keyness_wc(df_slice, options, exclude_nan, group_by, time_slices=time_slices, col_val=col_val, max_words=max_words, stopwords=user_stopwords, method="llr")                                
                            st.pyplot(evolutif_wc_by_axe)
                        except Exception as e:
                            st.write(f"ERROR dans le nuage évolutif par axe: {e}")    
