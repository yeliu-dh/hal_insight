# app.py
import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import json
from datetime import datetime
import re
from pathlib import Path
import io
import sys
import os
import math
import time


# # 把项目根目录 (/mount/src/hal_insight) 加入 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# #file 得出当前脚本所在文件夹（pages），join+".."表示回到上一级路径，abs表示绝对化，sys.append则为加入系统路径
# #=> ../mount/src/hal_insight

# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# if ROOT_DIR not in sys.path:
#     sys.path.insert(0, ROOT_DIR)  # 插入到 sys.path 开头，优先查找


# my utils
from utils.upload import load_external_json
from utils.HAL_search_api import fetch_hal_articles
from utils.HAL_search_api import process_df
from utils.HAL_search_api import save_file_csv_xlsx
from utils.upload import missing_data_warning
from utils.pdf2str import extract_text_from_pdf


# pages/1_hal_articles_fetcher.py
# from init_imports import *

st.set_page_config(page_title="HAL insight", page_icon="🛸",layout='wide')
#必须是第一行命令

#====================CACHE=========================#
@st.cache_data 
def get_mappings_json(mapping_folder='external_data'):
    return {
        "DOMAIN_MAP": load_external_json(f"{mapping_folder}/domain_map.json"),
        "LANG_MAP": load_external_json(f"{mapping_folder}/lang_map.json"),
        "DOC_TYPE_MAP": load_external_json(f"{mapping_folder}/doctype_map.json"),
    }
maps = get_mappings_json()
DOMAIN_MAP = maps["DOMAIN_MAP"]
LANG_MAP = maps["LANG_MAP"]
DOC_TYPE_MAP = maps["DOC_TYPE_MAP"]


def get_mappings_csv(mapping_folder='external_data'):
    data=pd.read_csv(f"{mapping_folder}/fnege_final_clean.csv")
    return data
FNEGE_MAP=get_mappings_csv()


st.title("Hal Articles Fetcher")


# 左右布局：左侧显示结果，右侧显示检索栏
# left_col, right_col = st.columns([2, 1])  # 左:右 = 3:1
# ----------------------- PARAM -----------------------
# with left_col:

st.subheader("🔢 Filtrer vos résultats")
st.markdown("<br>", unsafe_allow_html=True)

text = st_tags(
label="Text",
text="Tapez et 'Entrée' (chercher un texte dans tous les champs...)",
value=[],
suggestions=[],
maxtags=10
)

# 文档类型
doc_types = st.multiselect(
    "Type de documents",
    options=list(DOC_TYPE_MAP.keys()),
    format_func=lambda x: DOC_TYPE_MAP[x],
    default=["ART","OUV","COUV","COMM"]
)

domains = st.multiselect(
    "**Domaine**",
    options=list(DOMAIN_MAP.keys()),
    format_func=lambda x: DOMAIN_MAP[x],
    default=[]
)

keywords = st_tags(
    label="**Mots-clés**",
    text="Tapez et 'Entrée'",
    value=[],
    suggestions=[],
    maxtags=10
)

st.markdown(f"**Période (selon date du dépôt)**  \n"
            f"- si vous ne voulez pas définir la date de début, choisisssez '*' dans l'année de début' *ou/et* 'mois de début';  \n"
            f"- si vous ne voulez pas définir la date de fin, choisisssez 'aujourd'hui' dans 'années de fin' *ou/et* 'mois de fin'.")
now = datetime.now()
current_year, current_month = now.year, now.month

start_years = ["*"] + list(range(current_year, 1901, -1))
start_months= ["*"] + list(range(1, 13)) 
end_years = ["aujourh'dui"] + list(range(current_year, 1901, -1))
end_months = ["aujourd'hui"] + list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    start_year = st.selectbox("Année de début", start_years, index=start_years.index(2025))
with col2:
    start_month = st.selectbox("Mois de début", start_months, index=start_months.index(current_month-1))

col3, col4 = st.columns(2)
with col3:
    end_year = st.selectbox("Année de fin", end_years, index=end_years.index(current_year))
with col4:
    end_month = st.selectbox("Mois de fin", end_months, index=end_months.index("aujourd'hui"))



# # 日期校验
# invalid_date = False
# if start_year and start_month:#not None
#     if (end_year, end_month) < (start_year, start_month):
#         st.error("⚠️ Période invalide : la fin est antérieur au début!")
#         invalid_date = True

# if start_year is None:#无开始年份，选取过往所有文章
#     start_month=None
# if start_year and start_month is None:#没开始月份，默认从1月开始
#     start_month=1




# 语言、实验室
languages = st.multiselect(
    "Langues",
    options=list(LANG_MAP.keys()),
    format_func=lambda x: LANG_MAP[x],
    default=[]
)

labs = st_tags(
    label="Laboratoire",
    text="Tapez et 'Entrée'",
    value=["Institut de Recherche en Gestion"],
    maxtags=10
)

   
collcode = st_tags(
    label="Collection par code",
    text="Tapez et 'Entrée'",
    value=["UPEC"],
    maxtags=10
)


collname = st_tags(
    label="Collection par name",
    text="Tapez et 'Entrée'",
    value=["Université Paris-Est Créteil Val-de-Marne"],
    maxtags=10
)



# 输出字段
options_fields = ['halId_s','uri_s',"docType_s", "title_s", "subTitle_s", "authFullName_s","labStructName_s","domain_s", 
                    "publicationDate_s","journalTitle_s","conferenceTitle_s","conferenceStartDate_s","country_s","city_s","audience_s",
                    "language_s", "keyword_s", "abstract_s","urlFulltextEsr_s","files_s",'page_s',"modifiedDate_s","submittedDate_s",
                     "openAccess_bool",'volume_s','conferenceStartDate_s',"conferenceOrganizer_s","classification_s","collName_s","collCode_s",
                     "authIdHal_s","authLastNameFirstName_s"	
                     #"authIdHasPrimaryStructure_fs"
                    
                ]

default_fields=['halId_s','uri_s', "docType_s", "title_s", "subTitle_s", "authFullName_s","authIdHal_s","labStructName_s",
                "collName_s","collCode_s",
                "domain_s","openAccess_bool",'volume_s',"page_s","classification_s",
                "submittedDate_s","modifiedDate_s", "publicationDate_s","journalTitle_s","conferenceTitle_s","conferenceOrganizer_s","conferenceStartDate_s",
                "country_s", "language_s",
                "keyword_s", "abstract_s","files_s","urlFulltextEsr_s",

                ]


#⭐ check champs :https://api.archives-ouvertes.fr/docs/search/?schema=fields#fields

fields = st.multiselect(
    "Info à exporter",
    options=options_fields,
    default=default_fields
)

rows_range = list(range(0, 5001))
max_records = st.selectbox("les premier X articles:", rows_range, index=500)

cutoff_range= list(range(50, 101)) 
cutoff = st.selectbox("**Cutoff** pour matcher le classement FNEGE",cutoff_range , index=cutoff_range.index(80))
st.write(f"Cutoff (80 par défaut):  \n"
         f"seuil de similarité pour matcher le titre du journal dans le résultat d'HAL et le classement FNEGE.")
st.markdown("<br>", unsafe_allow_html=True)




# ----------------------- RESULT -----------------------

# st.subheader("Commencer la recherche")
st.markdown("<br>", unsafe_allow_html=True)

cols=st.columns([4,1])
with cols[1]:
    search_button = st.button("⚡ Chercher")

# st.divider()
df = None#初始化
if search_button:# and not invalid_date
    with st.spinner("Chercher..."):
        try:
            df = fetch_hal_articles(
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month,
                doc_types=doc_types,
                domains=domains,
                keywords=keywords,
                languages=languages,
                labs=labs,
                text=text,
                fields=fields,
                rows=100,
                max_records=max_records
            )
            if df.empty:
                st.warning("Aucun résultat trouvé.")
                st.stop()    
        except Exception as e:
            st.error(f"⚠️ ERROR in fetch_hal_articles: \n {e}")
            st.stop()#==break



    #================处理domain, axe, fnenge, primarystructure================ 
    try :
        df= process_df(df, DOMAIN_MAP, FNEGE_MAP, cutoff)
    except Exception as e:
        st.warning (f"ERROR in process_df :\n {e}")   
    st.divider()
    

    if not df.empty:
        #----------------------show----------------------
        st.success(f"✅ {len(df)} articles trouvés!\n\n"
                    f"💾 Résultat sauvegardé, vous pouvez l'utiliser directement dans les pages d'analyse!")    
        st.dataframe(df)
        st.write()

        #---------------- SAVE TO SESSION----------------
        st.session_state["uploaded_df"] = df  
        st.session_state["uploaded_df_source"] = "search"
        
        #------------------save to local-------------------
        try :
            save_file_csv_xlsx(df,start_year, start_month, end_year, end_month)
        except Exception as e:
            st.warning (f"ERROR in save_file_csv_xlsx :\n {e}")   

        
        st.divider()        












#============================PDF2STR=======================================    

df = st.session_state.get("uploaded_df", None)
if df is not None and not df.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    st.subheader("📄 Extraire le texte intégral")
    missing_data_warning(df, col='files_s',map={"files_s":"PDF liens"})

    st.write("Attention : tous les URLs ne permettent pas forcément d'extraire le texte intégral. "
            "Certaines URLs peuvent être invalides ou ne pas pointer vers un PDF."
            )

                
    cols=st.columns([4,1])
    with cols[1]:
        pdf_button = st.button(f"Extraire")

    if pdf_button:       
        st.session_state['uploaded_df_text']=st.session_state["uploaded_df"]
        df_text=st.session_state['uploaded_df_text'].copy()

        start_time=time.time()
        with st.spinner("Extraction des textes intégraux en cours..."):
            full_texts = []
            if "full_text" not in df_text.columns:
                df_text["full_text"] = " "            
            
            total=len(df_text[df_text['files_s'].notna()])
            processed =0
                
            # 初始化进度条和状态文本
            progress_bar = st.progress(0)
            status_text = st.empty()


            for i, row in df_text.iterrows():
                # if pd.notnull(df_text.loc[i, "full_text"]) and isinstance(df_text.loc[i, "full_text"], str) and len(df_text.loc[i, "full_text"]) > 20:
                #     continue #若存在，值为str，大于20字符，跳过

                url =row.get("files_s", None)
                if not url:
                    df_text.at[i, "full_text"] = None
                    continue

                try:
                    text = extract_text_from_pdf(url)
                    df_text.at[i, "full_text"] = text

                except Exception as e:
                    # st.warning(f"⚠️ Erreur ligne {i+1}: {e}")
                    df_text.at[i, "full_text"] = None

                # ✅ 每处理一行都更新状态
                processed += 1
                progress_bar.progress(processed / total)
                status_text.text(f"📄 Processus du traitement {processed}/{total} ...")

                # 每次更新一行，就立即保存到 session（确保断掉后能恢复）
                st.session_state["uploaded_df_text"] = df_text

            end_time=time.time()
            progress_bar.empty()

            num_text=len(df_text[df_text['full_text'].notna()])
            st.success(f"✅ Extraction des textes ({num_text}/{total}) terminée en {end_time-start_time:.2f} secondes !")
   

    #================DISPLAY====================
    df_text = st.session_state.get("uploaded_df_text", None)
    if df_text is not None and not df_text.empty and "full_text" in df_text.columns:
        st.dataframe(df_text)

        # -------------------update uploaded_df?-------------------
        update_df = st.checkbox("Mettre à jour le dataset ? ", value=False, key="nan")
        if update_df==True:
            st.session_state["uploaded_df"] = df_text
            st.success("Continuez l'analyse avec le dataset mis à jour!")

        # ======================SAVE===========================
        try :    
            save_file_csv_xlsx(df_text,start_year, start_month, end_year, end_month)        
        except Exception as e:
            st.warning (f"ERROR in save_file_csv_xlsx 2: \n {e}")

    