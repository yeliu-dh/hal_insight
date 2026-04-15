import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

#my utils:
from utils.upload import data_uploader
from utils.download import save_file_csv_xlsx_by_filename
from utils.HAL_search_api import get_start_end_field, filter_par_tdate # 筛选日期条件输入模块和筛选def #  filter_by_publicationdate

from utils.topic_modeling import preprocess_df_for_topic_modeling, filter_by_axe, get_topics_per_axe
from utils.topic_modeling import generate_topics_keywords_scatterplot
from utils.upload import missing_data_warning

st.set_page_config(page_title="HAL insight", page_icon="🛸",layout="wide")
st.title("📃 Topic modeling")


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
# st.markdown("NB.assurez vous les colonnes d'axe' sont disponibles")
st.markdown("<br>", unsafe_allow_html=True)

st.divider() 

st.subheader("📒 README")
st.write(f"**Model de topic modeling:** BERTopic")
st.write(f"**Model de réduction de dimension:** UMAP")

st.divider() 

if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    # 若df存在则视为开始
    st.session_state.started=True  
    st.subheader("🔢 Topic modeling sous axe")
    st.markdown("<br>", unsafe_allow_html=True)
  
    # 给输入df加上对应 emb ？
    df_predicted = st.session_state.uploaded_df.copy()
    
    
    
    
    # 重新生成emb？不需要原来的emb
    # df_all_emb_path="external_data/embeddings_all/df_all_3emb.parquet"
    # df_all_emb=pd.read_parquet(df_all_emb_path)
    # emb=df_all_emb[df_all_emb["halId_s"].isin(df['halId_s'].to_list())][["halId_s","emb_title_s","emb_keyword_s","emb_abstract_s"]]
    # df_emb=df.merge(emb, on='halId_s', how='left') 


    # ======================= PARAMETRES===========================
    # 时间范围？
    # axe_id="1"
    # min_topic_size=5
    # N_WORDS=5
    from datetime import date



    # ----------------------période----------------------
    # st.markdown("**Filtrer le résultat par la date**")
    # 仅输入!  
    filter = st.checkbox("**Active le filtrage de date ?**", value=False, key="nan")
         
    start_year, start_month, end_year, end_month, date_field=get_start_end_field(key_prefix='filter')
    date_field_col_map={"soumission":"submittedDate_tdate", 
                        "modification":"modifiedDate_tdate",
                        "publication":"publicationDate_tdate"
                        }
    date_field_col=date_field_col_map.get(date_field,None)
    if date_field_col not in df_predicted.columns:
        date_field_col=date_field_col.split('_')[0]+"_s"

    # ---date rang---
    df_predicted[date_field_col] = pd.to_datetime(
        df_predicted[date_field_col], errors="coerce"
    )
    date_min = df_predicted[date_field_col].min()
    date_max = df_predicted[date_field_col].max()

    st.write(
        f"[INFO] Date de *{date_field}* entre : "
        f"**{date_min.strftime('%Y/%m/%d')} → {date_max.strftime('%Y/%m/%d')}**"
    )


    
    # 起止日期不超过df中最早最晚日期
    # if  start_year, start_month, end_year, end_month,
        # st.warning()
        
    # st.markdown("<br>", unsafe_allow_html=True)
    # min_date = date(date_min.year, date_min.month, 1)
    # max_date = date(date_max.year, date_max.month, 1)
    
    # start_years =end_years= ["*"] + list(range(date_min.year, date_max.year+1, 1))
    # start_months=end_months= ["*"] + list(range(1, 13)) 
    
    # col1, col2 = st.columns(2)
    # with col1:
    #     start_year = st.selectbox("Année de début", start_years, index=start_years.index(date_min.year))
    # with col2:
    #     start_month = st.selectbox("Mois de début", start_months, index=start_months.index(1))#JAN!
        
    # col3, col4 = st.columns(2)
    # with col3:
    #     end_year = st.selectbox("Année de fin", end_years, index=end_years.index(date_max.year))
    # with col4:
    #     end_month = st.selectbox("Mois de fin", end_months, index=end_months.index(12))
    # st.markdown("<br>", unsafe_allow_html=True)

    
    #------------------sous un seul axe-----------------
    st.divider()    
    # true col: show
    AXE_COL_MAP={
        "axe":"Axe original",
        "predicted_axe":"Axe prédit",
        "final_axe":"Axe original + prédit"
    } 
    
    col_axe = st.selectbox("**Sur quels axes ?**", 
            options=AXE_COL_MAP.keys(), 
            index=list(AXE_COL_MAP.keys()).index('final_axe'), 
            format_func=lambda x: AXE_COL_MAP[x],
            key=f"col_axe")#JAN!

    # col_axe = st.multiselect(
    #     "Sur quels axes ?",
    #     options=AXE_COL_MAP.keys(),#["Axe original","Axe prédit","Axe original + prédit"],
    #     format_func=lambda x: AXE_COL_MAP[x],
    #     default=["final_axe"]
    # )
    for col in ["axe",'final_axe']:
        # col_en_question="final_axe" if 'final_axe' in df_predicted.columns else 'axe'
        # show_count= st.checkbox("Afficher le compte des classes ?", value=True, key="show_count")#key用于储存在session state中
        show_count=True
        missing_data_warning(df=df_predicted, col=col, show_count=show_count)
    st.markdown("<br>", unsafe_allow_html=True)
    
    
    
    axe_id = st.multiselect(
        "**Choisir l'axe thématique:**",
        options=["1","2","3","4"],
        default=["1"]
    )
    st.divider()
    # # 按照axe，predicted_axe, final_axe？
    
    
    #-------------------topic size----------------------
    range_topic_size = list(range(0,100))
    min_topic_size = st.selectbox("**Définir la taille minimale d'articles pour former un sujet:**", range_topic_size, index=30)#整除
    # st.markdown("Moins de nombre d'articles à analyse!")
        
    #------------------top n keywords-------------------
    range_top_kw = list(range(1, 11))
    N_WORDS = st.selectbox("**Afficher les premier N mots clés:**",range_top_kw, index=4)
     
    st.markdown("<br>", unsafe_allow_html=True)

    
    
    
    # ==========================START==============================
    cols=st.columns([4,1])
    with cols[1]:
        start_button = st.button("⚡ Commencer")
    if start_button:# and not invalid_date             
        ## 输入任意axe_id(str/lst)处理
        with st.spinner("🔄 Topic modeling..."):
            
            # df_filtered_key=f"df_filtered_{'_'.join(axe_id)}"
            # col_axe='final_axe' if 'final_axe' in df_predicted.columns else 'axe'
            df_axe_key=f"df_{col_axe}_{'_'.join(axe_id)}"
            date_key=f"{start_year}_{start_month}-{end_year}_{end_month}"
            topic_model_key=f"topic_model_{date_key}-axe{'_'.join(axe_id)}-{min_topic_size}"
            # st.write(f"[KEYS] {topic_model_key}")
            
            if not topic_model_key in st.session_state:
                #------- filter by date---------
                if filter:                
                    df_filtered=filter_par_tdate(df_predicted, 
                        start_year, start_month, 
                        end_year, end_month, 
                        date_field_col=date_field_col)
                    st.write(f"[INFO] Filtrer selon la date de '{date_field_col}': {len(df_predicted)}=>{len(df_filtered)} lignes restent.  \n")    
                else :
                    df_filtered=df_predicted.copy()
                    st.write(f'[INFO] pas de filtrage de date appliqué!')
                    
                    
                #------- preprocess+filter by axe--------
                
                df=preprocess_df_for_topic_modeling(df_filtered, col_axe=col_axe)#get 'axe_list'
                df_axe= filter_by_axe(df, axe_id=axe_id, col="axe_list")
                st.write(f"[INFO] filtrer selon {col_axe} {','.join(axe_id)}: {len(df_filtered)}=>{len(df_axe)} lignes restent.  \n")    
                st.session_state[df_axe_key]=df_axe
                
                # topic modeling
                topic_model=get_topics_per_axe(df=df_axe, col_text='clean_text', min_topic_size=min_topic_size)
                st.session_state[topic_model_key]=topic_model
            else :   
                topic_model=st.session_state[topic_model_key]
            topic_info = topic_model.get_topic_info()   
            st.dataframe(topic_info)
        
        with st.spinner("🔄 Visualiser scatterplot..."):
            if df_axe_key in st.session_state and topic_model_key in st.session_state :
                df_axe=st.session_state[df_axe_key]
                topic_model=st.session_state[topic_model_key]
                
                fig=generate_topics_keywords_scatterplot(topic_model, df=df_axe, col_text="clean_text", 
                                                         axe_id=axe_id, N_WORDS = N_WORDS,
                                                         date_field=date_field_col)
                st.pyplot(fig)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f"sujet -1 : articles non classés/généraux  \n"
                    f"les points coloré: les articles classé dans un sujet  \n"
                    f"les chiffres : les articles dont l'axe est prédit  \n"
                    )
                
                
                
                
                
                
                
                
                