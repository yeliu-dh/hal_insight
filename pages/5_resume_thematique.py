import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap #分行
import altair as alt
import plotly.express as px
from PIL import Image
import io
import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



#RESUME : 
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from transformers import T5Tokenizer, T5ForConditionalGeneration


#my utils:
from utils.upload import data_uploader
from utils.auto_completion import auto_completion_by_sim
from utils.summarization import extract_thema_chunks, generate_summaries


# from utils.upload import missing_data_warning
# from utils.preprocess import load_external_json
# from utils.preprocess import preprocess_text
# from utils.preprocess import explode_by_col


@st.cache_resource  # ✅ 缓存模型

def load_models():
    embedding_model=SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")#向量化模型
    tokenizer=T5Tokenizer.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#分词模型
    summary_model=T5ForConditionalGeneration.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#摘要模型
    translator_en = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
    translator_es = pipeline("translation", model="Helsinki-NLP/opus-mt-es-fr")
    return embedding_model, tokenizer, summary_model, translator_en, translator_es

embedding_model, tokenizer, summary_model, translator_en, translator_es=load_models()


# def load_embedding_model():  
#     return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
# embedding_model =load_embedding_model()

# def load_tokenizer():
#     return  T5Tokenizer.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#分词模型
# tokenizer = load_tokenizer()

# def load_summary_model():
#     return T5ForConditionalGeneration.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#摘要模型
# summary_model = load_summary_model()

# def load_translator_en():
#     return pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
# translator_en=load_translator_en()

# def load_translator_es():
#     return pipeline("translation", model="Helsinki-NLP/opus-mt-es-fr")
# translator_es=load_translator_es()


st.title("📃 Résumé thématique")

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
    
    st.subheader("🔢 Auto-completion des axes thématiques")
    
    # 重新计算按钮
    cols=st.columns([4,1])
    with cols[1]:
        complete_button = st.button("Auto-compléter")
    if complete_button:
        st.session_state.recompute_completion = True

    # 只有点击按钮或第一次进入才执行
    if st.session_state.get("recompute_completion", True):
        try:
            df_exploded=auto_completion_by_sim(df, embedding_model)
            st.session_state['df_exploded']=df_exploded
        except Exception as e:
            st.error(f"ERROR in 'auto_completion_by_sim' : {e}")
        
        # 计算完成后关闭标志，下次不自动重新计算
        st.session_state.recompute_completion = False

    #===========save df_exploded===============
    #记得按照original_axe去重先
    # df = st.session_state.get("uploaded_df", None)
    # if df is not None and not df.empty:
    #     #-------------show----------------------
    #     st.success(f"✅ {len(df)} articles trouvés!\n\n"
    #                 f"💾 Résultat sauvegardé, vous pouvez l'utiliser directement dans les pages d'analyse!")    
    #     st.dataframe(df)

    #     missing_data_warning(df, col='files_s',map={"files_s":"PDF liens"})

    #     #  ----------------SAVE TO LOCAL----------------- 
    #     #file name 
    #     today_str = datetime.now().strftime("%d%m%Y")
    #     cols=st.columns(4)
    #     with cols[1]:
    #         # as CSV
    #         csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    #         st.download_button(
    #             label="Télécharger CSV",
    #             data=csv_data,
    #             file_name = f"{today_str}-ProductionScientifiqueIRG-{start_month}-{start_year}_{end_month}-{end_year}_{len(df)}art.csv",
    #             mime="text/csv"
    #         )

    #     with cols[3]:
    #         #as XLSX
    #         # XLSX → 需要用 io.BytesIO() 来缓存二进制数据，再传给 download_button。
    #         xlsx_buffer = io.BytesIO()
    #         with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
    #             df.to_excel(writer, index=False, sheet_name="Articles")
    #         xlsx_data = xlsx_buffer.getvalue()

    #         st.download_button(
    #             label="Télécharger XLSX",
    #             data=xlsx_data,
    #             file_name=f"{today_str}-ProductionScientifiqueIRG-{start_month}-{start_year}_{end_month}-{end_year}_{len(df)}art.xlsx",
    #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #         )

    #         # 这是 XLSX 文件的 MIME 类型，告诉浏览器这是一个 Excel 文件，否则st button可能无法识别文件类型 









    st.subheader("📑 Summarisation par axe thématique")
    cols=st.columns([4,1])
    with cols[1]:
        summary_button = st.button("Résumer")
    if summary_button:
        st.session_state.recompute_summary = True #==开始开关

        if st.session_state.get("recompute_summary", True) and "df_exploded" in st.session_state :
            #=========================step1=====================================
            df_exploded=st.session_state.df_exploded
            with st.spinner("Extraire les phrases clés sous un axe..."):
                start_time=time.time()
                try:
                    axe_groups=extract_thema_chunks(df_exploded, embedding_model,translator_en, translator_es)
                    st.session_state['axe_groups']=axe_groups
                except Exception as e:
                    st.warning(f"ERROR in 'extract_thema_chunks' :{e}")
                end_time=time.time()
                st.write(f"✅​ Extraction finie en {end_time-start_time:.2f} sec.")
                print(f'axe groups:\n {axe_groups}')           

            #=========================step2=====================================
            with st.spinner("Résumer les phrases clés ..."):
                start_time = time.time()
                try:
                    axe_summary = generate_summaries(
                        axe_groups=axe_groups,
                        tokenizer=tokenizer,
                        model=summary_model,
                        translator_en=translator_en,
                        translator_es=translator_es,
                        max_length=100,
                        min_length=20
                    )
                except Exception as e:
                    st.warning(f"ERROR in 'generate_summaries' : {e}")
                end_time = time.time()
                st.write(f"✅​ Génération des résumés en {end_time-start_time:.2f} sec.")

            # 计算完成后关闭标志，下次不自动重新计算
            st.session_state.recompute_summary = False


