
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
from utils.wordcloud import explode_by_col
from utils.wordcloud import collect_clean_texts_by_col
from utils.wordcloud import create_time_slices
from utils.wordcloud import generate_keyness_wc



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

    # st.subheader("Nuage de mots évolutif")
    # if "evolutif_wc" not in st.session_state:
    #     st.session_state["evolutif_wc"] = None


    
        
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
        missing_data_warning(df, col=col, map=WC_MAP)
    # st.write("\n\n\n")
    st.markdown("<br>", unsafe_allow_html=True)#不容易被 Markdown 渲染压缩掉


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

                
        # ---- 自动推荐时间粒度并设置 radio 默认选项 ----
        if period_m <= 12:#一年内，按月度或者季度显示
            suggestion = "Mensuel ou Trimestriel"
            default_index = 1

        elif period_m <= 60:#3/5年内，按年度显示
            suggestion = "Annuel"
            default_index = 2
        else:
            suggestion = "Tous les 3 ou 5 ans"
            default_index = 3

        # ---- Radio 选择 ----
        granularity = st.radio(
            "🕒 Sélectionnez la granularité temporelle :",
            ["Mensuel","Trimestriel", "Annuel", "Tous les 3 ans","Tous les 5 ans"],
            index=default_index,
            horizontal=True,
        )        
        st.info(f"Période couverte : {earliest_ym} → {latest_ym}  ({period_m} mois). Granularité recommandée: **{suggestion}**.")
        

        time_slices=create_time_slices(df, granularity=granularity)
    st.markdown("<br>", unsafe_allow_html=True)



   # ----------------- user stopwords ---------------
    user_stopwords = st_tags(
        label="🗷 Ajouter des mots à ignorer",
        text="Tapez un mot et appuyez sur Entrée",
        value=["management","gestion","marketing", "recherche",'research','study',"social","use","cas"],
        maxtags=50
    )        
    st.markdown("<br><br>", unsafe_allow_html=True)
    # st.write("\n\n\n")


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
                'comme','afin','ne',"son",'ses',"none","nan","de","des",'la', "pouvoir"
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
        "💾 Group :",
        ["Global", "Axe"], #"Cl. FNEGE"
        index=0,
        format_func=lambda x: COL_MAP.get(x, x), 
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    #--------------exclure nan--------------
    exclude_nan = st.checkbox("Exclure les lignes sans étiquette (dropna)? ", value=False, key="nan")# 默认保留nan
    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------WC-------------------------
    # 按钮生成+储存
    cols=st.columns([4,1])
    with cols[1]:   
        button=st.button("Générer")  
    st.divider()

    if button:    
        with st.spinner("Générer..."):
            if group_by=="Global":
                evolutif_wc= generate_keyness_wc(df, options, exclude_nan, group_by, time_slices, max_words=max_words, stopwords=stopwords, method="llr")
                st.pyplot(evolutif_wc)
            
            # elif group_by=="Axe" or groupby=="":
            else:
                #---所有演变图的大标题----
                df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
                start_ym=df["submittedDate_s"].min().strftime("%Y-%m")
                end_ym=df["submittedDate_s"].max().strftime("%Y-%m")  
                # st.subheader(f"Évolution du nuage de mots ({start_ym} ~ {end_ym})")
                
                st.markdown(
                    f"<h3 style='text-align: center;'>Évolution du nuage de mots ({start_ym} ~ {end_ym})</h3>",
                    unsafe_allow_html=True
                ) #居中显示大标题

                exploded_df=explode_by_col(df, col=group_by)   
                ctg=sorted(exploded_df[group_by].unique())
                for col_val in ctg:
                    df_slice=exploded_df[exploded_df[group_by]==col_val]

                    # evolutif_wc_by_axe= generate_keyness_wc(df, options, exclude_nan, group_by, time_slices, col=None, max_words=100, stopwords=None, method="llr"):
                    evolutif_wc_by_axe=generate_keyness_wc(df_slice, options, exclude_nan, group_by, time_slices, col_val=col_val, max_words=max_words, stopwords=stopwords, method="llr")                                
                    st.pyplot(evolutif_wc_by_axe)
           

            # # elif group_by=="Axe":
            # else:
            #     #---所有演变图的大标题----
            #     df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
            #     start_ym=df["submittedDate_s"].min().strftime("%Y-%m")
            #     end_ym=df["submittedDate_s"].max().strftime("%Y-%m")  
            #     st.subheader(f"Évolution du nuage de mots ({start_ym} ~ {end_ym})")
        
            #     axe_map = {
            #         "1": "Performances et responsabilités",
            #         "2": "Société de services et services à la société",
            #         "3": "Innovations, transformations et résistances organisationnelles et sociétales",
            #         "4": "Ouvrages pédagogiques",
            #         "nan":'nan'
            #     }
            #     exploded_df=explode_by_col(df, col='Axe')   
            #     for axe in axe_map.keys():
            #         df_slice=exploded_df[exploded_df['Axe']==axe]
            #         # evolutif_wc_by_axe= generate_keyness_wc(df, options, exclude_nan, group_by, time_slices, col=None, max_words=100, stopwords=None, method="llr"):
            #         evolutif_wc_by_axe=generate_keyness_wc(df_slice, options, exclude_nan, group_by, time_slices, col_val=axe, max_words=max_words, stopwords=stopwords, method="llr")                                
            #         st.pyplot(evolutif_wc_by_axe)
