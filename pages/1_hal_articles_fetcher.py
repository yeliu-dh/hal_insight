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
import logging


# # 把项目根目录 (/mount/src/hal_insight) 加入 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# #file 得出当前脚本所在文件夹（pages），join+".."表示回到上一级路径，abs表示绝对化，sys.append则为加入系统路径
# #=> ../mount/src/hal_insight


# my utils
# from utils.log import setup_logging 
from utils.upload import load_external_json
from utils.HAL_search_api import build_period, get_start_end_field, filter_par_date
from utils.HAL_search_api import fetch_hal_articles, process_df
from utils.HAL_search_api import generate_ref_apa, preview_and_download_references
from utils.download import save_file_csv_xlsx
from utils.upload import missing_data_warning
from utils.pdf2str import extract_text_from_pdf

st.set_page_config(page_title="HAL insight", page_icon="🛸",layout='wide')#必须是第一行命令
# setup_logging(save_log=True, log_file="../sandbox/run.log")
 

#====================CACHE=========================#
@st.cache_data 
# map_maps_filename={'DOMAIN_MAP':"domain_map",
#                    "LANG_MAP":"lang_map.json",
#                    "DOC_TYPE_MAP":"doctype_map.json",
#                    "AUTH_STRUCT_MAP":"auth_struct_map.json"}

def get_mappings_json(mapping_folder='external_data'):
    return {
        "DOMAIN_MAP": load_external_json(f"{mapping_folder}/domain_map.json"),
        "LANG_MAP": load_external_json(f"{mapping_folder}/lang_map.json"),
        "DOC_TYPE_MAP": load_external_json(f"{mapping_folder}/doctype_map.json"),
        # "AUTH_STRUCT_MAP":load_external_json(f"{mapping_folder}/auth_struct_map.json")
    }
    
maps = get_mappings_json()
DOMAIN_MAP = maps["DOMAIN_MAP"]
LANG_MAP = maps["LANG_MAP"]
DOC_TYPE_MAP = maps["DOC_TYPE_MAP"]


# -----------------------------------------------------
path_AUTH_STRUCT_MAP="external_data/auth_struct_map.json"


# AUTH_STRUCT_MAP=maps['AUTH_STRUCT_MAP']# map_auth_struct不能缓存加载，不然update之后无法马上存入？
# st.write(f"len map_auth_struct:{len(list(AUTH_STRUCT_MAP.keys()))}!")

## fnege 
def get_mappings_csv(mapping_folder='external_data'):
    data=pd.read_csv(f"{mapping_folder}/fnege_final_hal.csv")
    return data
FNEGE_MAP=get_mappings_csv()


st.title("Hal Articles Fetcher")
# st.markdown("HAL permet de chercher des articles scientifiques par le type de document, la structure, l'année de publication...  \n"
#             "cette application vise à compléter sa fonction, en permettant  \n"
#             "- filtrer par l'année, le mois, la date indiqué")


# 左右布局：左侧显示结果，右侧显示检索栏
# left_col, right_col = st.columns([2, 1])  # 左:右 = 3:1
# ----------------------- PARAM -----------------------
# with left_col:

st.subheader("🔢 Filtrer vos résultats")
st.markdown("<br>", unsafe_allow_html=True)


# ------------------------------------random text-----------------------------------------------
text = st_tags(
label="**🗟 Cherche un text dans tous les champs:**",
text="Tapez et 'Entrée' (chercher un texte dans tous les champs...)",
value=[],
suggestions=[],
maxtags=10
)
st.markdown("<br>", unsafe_allow_html=True)


#---------------------------------------doctype------------------------------------------------
# 控制初始化状态
if "select_all_doctypes" not in st.session_state:
    st.session_state.select_all_doctypes = False

doc_types = st.multiselect(
    "**📚 Type de document:**",
    options=list(DOC_TYPE_MAP.keys()),
    format_func=lambda x: DOC_TYPE_MAP[x],
    default=list(DOC_TYPE_MAP.keys()) if st.session_state.select_all_doctypes else ["ART","OUV","COUV","COMM"]
)
st.checkbox(
    "(De)sélectionner tous les types de document",
    key="select_all_doctypes"
)
st.markdown("<br>", unsafe_allow_html=True)


#----------------------------------authfullname-----------------------------------------------
auth_names = st_tags(
label="**👩‍🔬Nom complet des auteurs:**",
text="Tapez et 'Entrée' (chercher un texte dans tous les champs...)",
value=None,
suggestions=[],
maxtags=10,
key="auth_names",
)

# input names TO authFullName_s
if auth_names:
    from fuzzywuzzy import process
    def fuzzy_lookup(query, choices, cutoff=80):
        if query in choices:
            return query
        else :
            best_match, score = process.extractOne(query, choices)
            if score >= cutoff:
                return best_match
            return None
    
    with open(path_AUTH_STRUCT_MAP, 'r', encoding='utf-8')as f:
        map_auth_struct=json.load(f)
        
    choices=list(map_auth_struct.keys())
    # st.write(f"len choices:{len(choices)}")
    auth_names_valid=[fuzzy_lookup(query=name, choices=choices, cutoff=80) for name in auth_names]
    # st.write(f"[check] authFullName_s: {auth_names_valid}")
else :
    auth_names_valid=None
    
st.markdown("<br>", unsafe_allow_html=True)



# ----------------------------------------labsName/ID----------------------------------------------------
labs = st_tags(
    label="**🔬 Laboratoire**",
    text="Tapez et 'Entrée'",
    value=["Institut de Recherche en Gestion"],
    maxtags=10
)
labs_id=st_tags(
    label="**ID de laboratoire**",
    text="Tapez et 'Entrée'",
    value=['57129',"1004418"],
    maxtags=10
)
st.markdown("<br>", unsafe_allow_html=True)


#------------------------------------PEIODE DE REQUETE--------------------------------------------
start_year, start_month, end_year, end_month, date_field=get_start_end_field(key_prefix="search")

date_field_tdate_map={"soumission":"submittedDate_tdate", 
                    "modification":"modifiedDate_tdate",
                    "publication":"publicationDate_tdate"
                    }
date_field_tdate=date_field_tdate_map.get(date_field,None)


st.markdown("<br>", unsafe_allow_html=True)

# 语言、实验室
languages = st.multiselect(
    "**Langues**",
    options=list(LANG_MAP.keys()),
    format_func=lambda x: LANG_MAP[x],
    default=[]
)
st.markdown("<br>", unsafe_allow_html=True)


# ------------------------------------------other champs--------------------------------------------
domains = st.multiselect(
    "**Domaines**",
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

rows_range = list(range(0, 5001))
max_records = st.selectbox("**les premier X articles (valeur maximale:5000):**", rows_range, index=500)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# collcode = st_tags(
#     label="Collection par code",
#     text="Tapez et 'Entrée'",
#     value=["UPEC"],
#     maxtags=10
# )

# collname = st_tags(
#     label="Collection par name",
#     text="Tapez et 'Entrée'",
#     value=["Université Paris-Est Créteil Val-de-Marne"],
#     maxtags=10
# )




# ==========================================(OUTPUT) FIELD LIST====================================================
st.subheader("💾 Choisir les champs à exporter")
st.markdown("<br>", unsafe_allow_html=True)

# 可选输出字段
options_fields = ['halId_s','uri_s',"docType_s", "title_s", "subTitle_s", "authFullName_s","labStructName_s","domain_s", 
                    "publicationDate_s","journalTitle_s","conferenceTitle_s","conferenceStartDate_s","country_s","city_s","audience_s",
                    "language_s", "keyword_s", "abstract_s","urlFulltextEsr_s","files_s",'page_s',"modifiedDate_s","submittedDate_s",
                     "openAccess_bool",'volume_s','conferenceStartDate_s',"conferenceOrganizer_s","classification_s","collName_s","collCode_s",
                     "authIdHal_s","authLastNameFirstName_s","label_s","labStructIdName_fs",
                     "authIdHasPrimaryStructure_fs","inPress_bool","publicationDateY_i"     
]

# 默认输出字段
default_fields=['halId_s','uri_s', "docType_s", "title_s", "subTitle_s", "authFullName_s","labStructName_s",
                "domain_s","openAccess_bool",'volume_s',"page_s","classification_s",
                "submittedDate_s","modifiedDate_s", "publicationDate_s","publicationDateY_i",
                "journalTitle_s","conferenceTitle_s","conferenceOrganizer_s","conferenceStartDate_s",
                "country_s", "language_s",
                "keyword_s", "abstract_s","files_s","urlFulltextEsr_s","label_s", "inPress_bool",
]

fields = st.multiselect(
    "**Info à exporter**",
    options=options_fields,
    default=default_fields
)

# ========================================champs param============================================
st.markdown("<br>", unsafe_allow_html=True)
active_fuzzylookup = st.checkbox("**Pour le champs 'cl_fnege', active la recherche floue ?**", value=False, key="active_fuzzylookup")#key用于储存在session state中
cutoff_range= list(range(50, 101)) 
cutoff = st.selectbox("si oui, définir un **Cutoff%**",cutoff_range , index=cutoff_range.index(95))

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
    


# ============================================README=============================================
st.subheader("📒 README")
# st.markdown(f"HAL cherche des articles par publicationDateY_i")

st.markdown(
    "**cl_fnege** : Classement FNEGE du journal de l'année de la publication  \n"
    "Pour chaque article, nous déterminons automatiquement le classement FNEGE du *journalTitle_s* correspondant à son année de *publicationDate_s*.  \n"
    "Le nom de la revue est comparé aux listes FNEGE pour trouver le classement :  \n"
    "- la recherche flou désactivée (par défault):  \n"
    " Le classement sera attribué à l'article que son nom du journal correspond exactement celui sur la col 'journal_hal'.  \n"
    "- la recherche flou sactivée:  \n"
    "Le seuil de match (cutoff) est ajustable. Les résultats trouvés par recherche floue sont indiqués avec `rang_nom-journal-uncertain_nomRevue`.  \n"
    "- Si le range n'est pas disponible, on note NaN, que ce soit en recherche exacte ou floue.  \n"
    "👉 Consulter [le classement FNEGE (2011-2025)](https://github.com/yeliu-dh/hal_insight/blob/main/external_data/fnege_final_hal.csv)"
)
st.markdown("<br>", unsafe_allow_html=True)


st.markdown(
    f"**authPrimaryStructureIdName_s** : les structures primaires des auteurs de chaque article  \n"
    # f"**Structure primaire de l'auteur => author_primarystructure_s**:  \n"
    f"- Pour chaque article, nous identifions automatiquement l’institution principale de chaque auteur en utilisant la colonne *authFullName_s* pour retrouver les structures via *authIdHasPrimaryStructure_fs*.  \n"
    f"- L'info est structurée sous forme de *Nom complet de l'auteur_Identifiant de sa structure primaire_Nom de la structure  \n"
    f"- Par example, Anne-Claire Chêne_57129_Institut de Recherche en Gestion  \n\n"
    f"**authPrimaryStructure_hasIRG_bool**: si les identifiants *1004418* ou/et *57129* apparaît dans les structures primaires, cette colonne prend une valeur *True*  \n\n"    
    "👉 Consulter **le nom complet et l'ID des auteurs et leurs structure primaires** dans ce [Dictionnaire mis à jour en continu](https://github.com/yeliu-dh/hal_insight/blob/main/external_data/auth_struct_map.json)"
    # f"Les différentes institutions d’un même article sont concaténées avec un point-virgule ';'."
)
st.markdown("<br>", unsafe_allow_html=True)






# ======================================= GET RESULT=============================================

cols=st.columns([4,1])
with cols[1]:
    search_button = st.button("⚡ Chercher")
    
df = None#初始化
if search_button:# and not invalid_date
    st.divider()
    st.markdown("### 📑LOG ###")    
    with st.spinner("Chercher..."):
        try:
            df = fetch_hal_articles(
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month,
                date_field_col=date_field_tdate,
                doc_types=doc_types,
                auth_names_valid=auth_names_valid,
                domains=domains,
                keywords=keywords,
                languages=languages,
                labs=labs,
                labs_id=labs_id,
                text=text,
                fields=fields,
                rows=100,
                max_records=max_records
            )
            print(f"[RAW RESULT] {len(df)}")
            if df.empty:
                st.warning("Aucun résultat trouvé.")
                st.stop()    
        except Exception as e:
            st.error(f"⚠️ ERROR in fetch_hal_articles: \n {e}")
            st.stop()#==break

    #================处理domain, axe, fnenge, primarystructure================ 
    try :
        df =process_df(df, DOMAIN_MAP, 
            FNEGE_MAP, cutoff, active_fuzzylookup,
            #  start_year, start_month, end_year, end_month, filter_pubdate_by=None
            #   AUTH_STRUCT_MAP
            path_map_auth_struct=path_AUTH_STRUCT_MAP,
            
       )#***
        print(f"[PROCESSED RESULT] {len(df)}")

        # desired_order=[]
        st.success(f"✅ {len(df)} articles trouvés!\n\n"
                    f"💾 Résultat sauvegardé, vous pouvez l'utiliser directement dans les pages d'analyse!")    
        
        #----------------SAVE TO SESSION----------------
        st.session_state["uploaded_df"] = df  
        st.session_state["uploaded_df_source"] = "search"
    
    except Exception as e:
        st.warning (f"ERROR in process_df :\n {e}")   
st.divider()
    


df = st.session_state.get("uploaded_df", None)
if df is not None and not df.empty:
    st.markdown("### 🗂️Résultat ###")        

    #----------------------show----------------------
    st.dataframe(df)
    st.markdown("<br>", unsafe_allow_html=True)
    #----------------------save-----------------------
    save_file_csv_xlsx(df=df,start_year=start_year, start_month=start_month, end_year=end_year, 
                       end_month=end_month, key_filename="result")
    
    
    # #----------------------quick check-----------
    # st.write(f"**🔎Aperçu rapide des données:**")
    # cols= df.columns.tolist()
    # col_en_question = st.selectbox("colonne en question", cols, index=cols.index("axe"))
    # # show_distribution= st.checkbox("Afficher la répartition des valeurs ?", value=False, key="col_distribution")#key用于储存在session state中

    
    # show_way = st.radio(
    #     "Show la distribution ou le compte des valeurs ?",
    #     ["distribution", "compte"],
    #     horizontal=True, 
    #     # help=
    # )
    # show_distribution = show_way == "distribution"
    # show_count = show_way == "compte"
    # missing_data_warning(df, col=col_en_question, show_distribution=show_distribution, show_count=show_count)

    st.divider()

    
    st.markdown("### Filtrer le résultat par la date")
    start_year, start_month, end_year, end_month, date_field=get_start_end_field(key_prefix='filter')
        
    date_field_s_map={"soumission":"submittedDate_s", 
                        "modification":"modifiedDate_s",
                        "publication":"publicationDate_s"
                        }
    date_field_s=date_field_s_map.get(date_field,None)

    df_filtered=filter_par_date(df, 
                    start_year, start_month, 
                    end_year, end_month, 
                    date_field_col=date_field_s)
    # pub date在filter之前自动补全！没有月日的自动定位到01-01
        
    st.info(f"**Résultat filtré : {len(df)} lignes => {len(df_filtered)} lignes**")#  {start_month}/{start_year} ~ {end_month}/{end_year} par {date_col}
    st.dataframe(df_filtered)
    st.markdown("<br>", unsafe_allow_html=True)


    #--------------------save filtered df?----------------------
    save_file_csv_xlsx(df=df,start_year=None, start_month=None, 
                       end_year=None, end_month=None, key_filename="filtered_result")
    
    # -------------------update uploaded_df?-------------------
    update_df = st.checkbox("Mettre à jour le dataset pour l'analyse suivante? ", value=False, key="nan")
    if update_df==True:
        st.session_state["uploaded_df"] = df_filtered
        st.success("Continuez l'analyse avec le dataset mis à jour!")
    st.divider()
    


    # #------------------save to local-------------------
    # st.markdown("### 📥 Téléchargement du résultat ###")        
    # try :
    #     default_filename=get_default_filename(df,start_year, start_month, end_year, end_month)
    #     save_file_csv_xlsx(df,default_filename, key_filename="df")
        
    # except Exception as e:
    #     st.warning (f"ERROR in save_file_csv_xlsx :\n {e}")   
    # st.divider()   

    #-----------------save ref--------------------------
    preview_and_download_references(df)
    st.divider()
    




#============================PDF2STR=======================================    

df = st.session_state.get("uploaded_df", None)
if df is not None and not df.empty:
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
            #??
            default_filename=get_default_filename(df, start_year, start_month, end_year, end_month)
            save_file_csv_xlsx(df_text,default_filename, key_filename="pdf")
    
        except Exception as e:
            st.warning (f"ERROR in save_file_csv_xlsx 2: \n {e}")

    