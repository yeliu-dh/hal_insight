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

# # 把项目根目录 (/mount/src/hal_insight) 加入 Python 路径
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# #file 得出当前脚本所在文件夹（pages），join+".."表示回到上一级路径，abs表示绝对化，sys.append则为加入系统路径
# #=> ../mount/src/hal_insight


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)  # 插入到 sys.path 开头，优先查找


# my utils
# from utils.HAL_search_api import fetch_hal_articles
# from utils.mapping import load_mapping_json
# from utils.mapping import map_domains
# from utils.mapping import add_axe
# from utils.ranking import add_classement_fnege


# pages/1_hal_articles_fetcher.py
from init_imports import *


st.set_page_config(page_title="HAL insight", page_icon="🛸")
#必须是第一行命令

#====================CACHE=========================#
@st.cache_data 
# @st.cache_data 是装饰器，只能用在函数定义上，不能直接装饰一个变量
# 不能直接写# DOMAIN_MAP = load_json(domain_file)
def get_mappings():
    return {
        "DOMAIN_MAP": load_mapping_json("domain_map.json"),
        "LANG_MAP": load_mapping_json("lang_map.json"),
        "DOC_TYPE_MAP": load_mapping_json("doctype_map.json"),
        "CLASSEMENT": load_mapping_json("classement_fnege.json"),#/classement.json
    }

maps = get_mappings()
DOMAIN_MAP = maps["DOMAIN_MAP"]
LANG_MAP = maps["LANG_MAP"]
DOC_TYPE_MAP = maps["DOC_TYPE_MAP"]
CLASSEMENT=maps['CLASSEMENT']


st.title("Hal Articles Fetcher")


# 左右布局：左侧显示结果，右侧显示检索栏
# left_col, right_col = st.columns([2, 1])  # 左:右 = 3:1
# ----------------------- PARAM -----------------------
# with left_col:

st.subheader("Filtrer vos résultats")
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
    default=["ART","OUV","COUV"]
)

domains = st.multiselect(
    "Domaine",
    options=list(DOMAIN_MAP.keys()),
    format_func=lambda x: DOMAIN_MAP[x],
    default=[]
)

keywords = st_tags(
    label="Mots-clés",
    text="Tapez et 'Entrée'",
    value=[],
    suggestions=[],
    maxtags=10
)

st.markdown("Période (selon date du dépôt)")
now = datetime.now()
current_year, current_month = now.year, now.month
years = [None] + list(range(current_year, 1901, -1))
months = [None] + list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    start_year = st.selectbox("Année de début", years, index=years.index(2025))
with col2:
    start_month = st.selectbox("Mois de début", months, index=months.index(current_month))

col3, col4 = st.columns(2)
with col3:
    end_year = st.selectbox("Année de fin", years, index=years.index(current_year))
with col4:
    end_month = st.selectbox("Mois de fin", months, index=months.index(current_month))




# 日期校验
invalid_date = False
if start_year and start_month:#not None
    if (end_year, end_month) < (start_year, start_month):
        st.error("⚠️ Période invalide : la fin est antérieur au début!")
        invalid_date = True

if start_year is None:#无开始年份，选取过往所有文章
    start_month=None
if start_year and start_month is None:#没开始月份，默认从1月开始
    start_month=1


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

# 输出字段
options_fields = ['halId_s','uri_s',"docType_s", "title_s", "subTitle_s", "authFullName_s","labStructName_s","domain_s", 
                    "publicationDate_s","journalTitle_s","conferenceTitle_s","conferenceStartDate_s","country_s","city_s","audience_s",
                    "language_s", "keyword_s", "abstract_s","urlFulltextEsr_s","files_s",'page_s',"modifiedDate_s","submittedDate_s",
                     "openAccess_bool",'volume_s','conferenceStartDate_s',"conferenceOrganizer_s","classification_s",
                    
                ]

default_fields=['halId_s','uri_s', "docType_s", "title_s", "subTitle_s", "authFullName_s","labStructName_s","domain_s", 
                "openAccess_bool",'volume_s',"page_s","classification_s",
                "submittedDate_s","modifiedDate_s", "publicationDate_s","journalTitle_s","conferenceTitle_s","conferenceOrganizer_s","conferenceStartDate_s",
                "country_s", "language_s",
                "keyword_s", "abstract_s","files_s","urlFulltextEsr_s"
                ]


#⭐ check champs :https://api.archives-ouvertes.fr/docs/search/?schema=fields#fields

fields = st.multiselect(
    "Info à exporter",
    options=options_fields,
    default=default_fields
)

rows_range = list(range(0, 5001))
max_records = st.selectbox("Limite de requête une fois", rows_range, index=300)

st.markdown("<br>", unsafe_allow_html=True)


# ----------------------- RESULT -----------------------
# with right_col:

# st.subheader("Commencer la recherche")
st.markdown("<br>", unsafe_allow_html=True)

cols=st.columns([4,1])
with cols[1]:
    search_button = st.button("⚡ Chercher")

st.divider()
df = None#初始化

if search_button and not invalid_date:
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
            st.error(f"⚠️ {e}")
            st.stop()#==break


    # -----------处理 domain----------------
    if "domain_s" in df.columns:   
        df["domain_s"] = df["domain_s"].apply(lambda x : map_domains(x, map=DOMAIN_MAP))

    #----------处理axe----------------------
    if "classification_s" in df.columns:
        df=add_axe(df)

    #------------- 处理fnege----------------
    journal_col="journalTitle_s"
    cl_name = 'Cl. FNEGE'
    if "journalTitle_s" in df.columns:
        df= add_classement_fnege(df, journal_col='journalTitle_s', map=CLASSEMENT, cl_name=cl_name)

    #-------------SAVE TO SESSION-----------------
    # 保存结果到 session_state
    if not df.empty:
        st.session_state["uploaded_df"] = df  
        st.session_state["uploaded_df_source"] = "search"
        
    df = st.session_state.get("uploaded_df", None)

    # if df is None or df.empty:
    #     st.warning("0 résultat!")

    if not df.empty :
        #-------------show----------------------
        st.success(f"✅ {len(df)} articles trouvés!")
        st.success(f"💾 Résultat sauvegardé, vous pouvez l'utiliser directement dans les pages d'analyse!")
        
        st.dataframe(df)

        #  ----------------SAVE TO LOCAL----------------- 
        #file name 
        today_str = datetime.now().strftime("%d%m%Y")
        cols=st.columns(4)
        with cols[1]:
            # as CSV
            csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            
            st.download_button(
                label="Télécharger CSV",
                data=csv_data,
                file_name = f"{today_str}-ProductionScientifiqueIRG-{start_month}-{start_year}_{end_month}-{end_year}_{len(df)}art.csv",
                mime="text/csv"
            )

        with cols[3]:
            #as XLSX
            # XLSX → 需要用 io.BytesIO() 来缓存二进制数据，再传给 download_button。
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Articles")
            xlsx_data = xlsx_buffer.getvalue()

            st.download_button(
                label="Télécharger XLSX",
                data=xlsx_data,
                file_name=f"{today_str}-ProductionScientifiqueIRG-{start_month}-{start_year}_{end_month}-{end_year}_{len(df)}art.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 这是 XLSX 文件的 MIME 类型，告诉浏览器这是一个 Excel 文件，否则st button可能无法识别文件类型 


