import streamlit as st
from streamlit_tags import st_tags
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap #分行
import altair as alt
import plotly.express as px
from PIL import Image
import io, os, sys, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from PIL import Image


#my utils:
from utils.upload import data_uploader
from utils.HAL_search_api import save_file_csv_xlsx_by_filename


## axe
from utils.axe_classification import parse_axes, split_axe
from utils.axe_classification import filtrate_df_to_emb, emb_text, check_before_emb_text
from utils.axe_classification import to_df_long
from utils.axe_classification import load_predict_by_mlp_lr
from utils.axe_classification import gather_predicted_axes, merge_axes


# topics





# @st.cache_resource  # ✅ 缓存模型
# def load_embedding_model(model_name):
#     return SentenceTransformer(model_name)#向量化模型
# model_name="paraphrase-multilingual-MiniLM-L12-v2"
# embedding_model=load_embedding_model(model_name)

# ========= 1. 缓存 embedding 模型 =========
@st.cache_resource(show_spinner="🔄 Chargement du modèle d'embeddings...")
def load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-m3")

        
st.set_page_config(page_title="HAL insight", page_icon="🛸",layout="wide")
st.title("📃 Auto-classification des axes thématique")


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


st.subheader("📒 README")
st.markdown("""
| Code | Nom de l'axe |
| --- | --- |
| IRG_AXE1 | Performances et responsabilités |
| IRG_AXE2 | Société de services et services à la société |
| IRG_AXE3 | Innovations, transformations et résistances organisationnelles et sociétales |
| IRG_AXE4 | Ouvrages pédagogiques |
""")

st.markdown("👉Consulter [Entraînement du modèle MLP+LR  (notebook)](https://github.com/yeliu-dh/hal_insight/blob/main/notebooks/test_trainclf.ipynb)")


# with open("md\clf_training.md", "r", encoding="utf-8") as f:
#     md_text = f.read()
# st.markdown(md_text, unsafe_allow_html=True)


# st.markdown("**Statistiques de l'entraînement**")
# st.markdown("👉Consulter [Entraînement des modèles (notebook)](https://github.com/yeliu-dh/hal_insight/blob/main/notebooks/test_multiaxe_3emb.ipynb)")
# st.markdown(f"- Tous les **2734 articles** de type art, ouv, cov et comm d'IRG jusqu'au Dec.2025  \n"
#             f"- Parmi eux, **le titre, les mots-clés, le résumé** de 2117 articles sont séparement embeddés par le modèle **'BAAI/bge-m3'** (environ 30 mins).  \n"
#             f"- Entrainer un MLP (Multi-Layer Perceptron) avec **5139** embeddings d'un text, un vecteur de multi-label et un label de la source du text \n"
#             f"- Méthodes d'amélioration : **pondération et échantillongae des classes**, Adam optimizer, focal loss, early stopping  \n"
#             f"=> enregistrer le meuilleur f1 et le seuil correspondant, utilisé après pour la prédiction  \n\n"
#             f"   t_lr=0.25, t_lgb=0.95, t_ens=0.52  \n\n")

# st.markdown(f"**PB** :l'axe 4 est très sous-présent, déséquilibre entre les classe biaise le modèle.  \n"
#             f"**Solution** : entraîne d'autres modèles linéaires qui se concentrent sur la classification de l'axe 4:  'Logistic Regression' et 'LightGBM', et remplacer la prédiction de MLP sur l'axe par celle de LR et LGB.  \n"
#             f"**Resultat final** :   \n\n")

# st.markdown("""| Metric | Value |
# | --- | --- |
# | Micro F1 | 0.7879093198992443 |
# | Macro F1 | 0.700142039539857 |
# | Micro Precision | 0.7704433497536946 |
# | Micro Recall | 0.8061855670103093 |
# """)

# st.markdown("""| Class | Precision | Recall | F1-score | Support |
# | --- | --- | --- | --- | --- |
# | axe1 | 0.78 | 0.76 | 0.77 | 304 |
# | axe2 | 0.77 | 0.58 | 0.66 | 113 |
# | axe3 | 0.77 | 0.89 | 0.83 | 531 |
# | axe4 | 0.67 | 0.45 | 0.54 | 22 |
# """)
# matrix_image = Image.open("external_data\clf_classification_matrix.png")
# st.image(matrix_image, caption="matrice de confusion du classifieur")

st.divider()

if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
    # 若df存在则视为开始
    st.session_state.started=True
    
    st.subheader("🔢 Classification automatique")
    st.markdown("<br>", unsafe_allow_html=True)
  
 
    # préparation:
    df = st.session_state.uploaded_df.copy()
    df_all=df.copy()
    path_mlp="model/2024\mlp_3class.pt"
    path_lr="model/2024\model_lr_abstract_0.80.pt"
    df_all_emb_path="external_data/embeddings_all/df_all_3emb.parquet"
    
    # st.session_state.df_all=df_all.copy()
    # st.write(os.getcwd())# D:\Work\IRG\hal_insight

    #------------------------------------------read&filtrate-----------------------------------------------
    st.write(f"**[ETAPE1] Lire le CSV et sélectionner les lignes sans axes**  \n")
    # df_all = pd.read_csv(df_all_path)
    df_noaxe = df_all[(df_all['axe'].isna())|(df_all['axe']=="nan")]
    df_hasaxe = df_all[~df_all['halId_s'].isin(df_noaxe['halId_s'])]

    # st.write(f"- len df_all: {len(df_all)}")
    # st.write(f"- len df_noaxe: {len(df_noaxe)}")
    # st.write(f"- len df_hasaxe: {len(df_hasaxe)}")
    # st.text(f"[INFO] Répartition: {df_all.axe.value_counts(dropna=False)}\n")
    

    #------------------------------------------splitaxe-----------------------------------------------
    st.write(f"**[ETAPE2] Split axe en 4 colonnes 'axe1-4' et 'axes_vec'**  \n")
    df_noaxe = split_axe(df_noaxe)
    # st.session_state.df_noaxe=df_noaxe

    #------------------------------------------embeddings-----------------------------------------------
    st.write(f"**[ETAPE3] Embeddings des titres, mots-clés et résumés**")
   
    if 'df_noaxe_embedded' in st.session_state and st.session_state.df_noaxe_embedded['halId_s'].tolist()==df_noaxe['halId_s'].to_list():
        #确保是同一个df！
        st.write(f"[INFO] Embeddings déjà existants")

    else:
        st.write(f"[LOAD] Charge le modèle d'embeddings 'BAAI/bge-m3'...")
        embedding_model = load_embedding_model()

        # from sentence_transformers import SentenceTransformer
        # embedding_model = SentenceTransformer("BAAI/bge-m3")
        
        st.write(f"[INFO] Trouver des articles qui n'ont pas d'axes...")
        df_noaxe_embedded=check_before_emb_text(df=df_noaxe, embedding_model=embedding_model, 
                                               batch_size=32, 
                                               df_all_emb_path=df_all_emb_path)
        
        ## update df_all_emb :
        df_all_emb=pd.read_parquet(df_all_emb_path)
        df_all_emb_updated = (
            pd.concat([df_all_emb, df_noaxe_embedded], axis=0)
            .drop_duplicates(subset="halId_s")
            .reset_index(drop=True)
        )
        # 修复parquet无法保存cl_fnege中的none？
        df_all_emb_updated["cl_fnege"] = (
            df_all_emb_updated["cl_fnege"]
            .fillna("")        # NaN → 空字符串
            .astype(str)       # 强制字符串
        )
        df_all_emb_updated.to_parquet(df_all_emb_path)
        st.write(f"[INFO] Fichier d'embeddings mis à jour : +{len(df_all_emb_updated) - len(df_all_emb)} entrées")
        st.session_state['df_noaxe_embedded']=df_noaxe_embedded

    #------------------------------------------to df long-----------------------------------------------
    st.write(f"**[ETAPE4] Transformer df_noaxe en df_noaxe_long**  \n")
    if 'df_noaxe_embedded' in st.session_state:
        df_noaxe_embedded=st.session_state['df_noaxe_embedded']
        df_noaxe_long = to_df_long(df_noaxe_embedded, cols=['emb_title_s','emb_keyword_s','emb_abstract_s'],
                                pq_long_path=None)
       
    #------------------------------------------prediction-----------------------------------------------
    st.write(f"**[ETAPE5] Prédire les axes avec les modèles MLP+LR**  \n")
    
    df_long_predicted=load_predict_by_mlp_lr(
        df_noaxe_long, 
        path_mlp=path_mlp,
        path_lr=path_lr,
        t_lr=0.5,
        class_names_mlp=("axe1", "axe2", "axe3"),
        class_name_lr="axe4",
    )


    #------------------------------------------merge predictions----------------------------------------
    st.write(f"**[ETAPE6] Fusionner les prédictions avec le df original**  \n")
    # gather pred_axes by halId
    df_all=gather_predicted_axes(df_long_predicted=df_long_predicted,
                        df_all=df_all, 
                        groupby_col="halId_s")

    ## merge axe & predicted_axe to final_axe
    df_all['final_axe']=df_all.apply(merge_axes, axis=1)


    st.write(f"[INFO] Df de {len(df_all)} lignes avec des axes fusionnés:\n")
    # st.dataframe(df_all[['halId_s','title_s',"keyword_s",'abstract_s','axe','predicted_axe','final_axe']])
    st.dataframe(df_all)
    st.session_state['df_all_pred']=df_all

    
    
    #------------------save to local-------------------
    if "df_all_pred" in st.session_state:
        df_all_pred=st.session_state['df_all_pred']
        try :    
            filename=st.session_state['uploaded_df_filename'].split('.')[0]+"_final_axe"
            save_file_csv_xlsx_by_filename(df_all_pred, filename)
        except Exception as e:
            st.warning (f"ERROR in save_file_csv_xlsx :\n {e}")   
        st.divider()    
    
    #------------------check-------------------
    st.write(f"**[CHECK] vérification manuelle**")
    cols_kept = st.multiselect(
        "Type de documents",
        options=df_all.columns.to_list(),
        # format_func=lambda x: DOC_TYPE_MAP[x],
        default=["title_s","keyword_s","abstract_s","axe","predicted_axe","final_axe"]
    )
    st.markdown("<br>", unsafe_allow_html=True)

    show_pred = st.checkbox("Afficher que la prédiction ? ", value=True, key="nan")
    if show_pred:
        df_check=df_all[df_all["axe"].isna()][cols_kept]
    else :
        df_check=df_all[cols_kept]
    st.dataframe(df_check)
    st.divider()
    
    #------------------vis-------------------
    if "df_all_pred" in st.session_state:                
        st.subheader("🔢 Visualisation")
        st.markdown("<br>", unsafe_allow_html=True)
        cols=st.columns([4,1])
        with cols[1]:
            start_button = st.button("⚡ Commencer")
        if start_button:# and not invalid_date    

            from utils.topic_modeling import preprocess_df_for_topic_modeling, generate_force_scatterplot         
            df_predicted=st.session_state['df_all_pred']
            df_all_emb=pd.read_parquet(df_all_emb_path)
            emb=df_all_emb[df_all_emb["halId_s"].isin(df_predicted['halId_s'].to_list())][["halId_s","emb_title_s","emb_keyword_s","emb_abstract_s"]]
            df_predicted_emb=df_predicted.merge(emb, on='halId_s', how='left') 
                
            df_plot=preprocess_df_for_topic_modeling(df_predicted_emb)
            
            with st.spinner("🔄 Génération de la visualisation..."):
                fig=generate_force_scatterplot(df_plot)
                # st.pyplot(fig)
                st.pyplot(fig, use_container_width=True)

    




  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    



    # df_all_outpath="data_axe/20251201-ProductionScientifiqueIRG-__-202512_2734art_predaxe.csv",

    # # --------------- embedding_model ------------------
    # model_name = st_tags(
    #     label="Model name",
    #     text="Tapez et 'Entrée'",
    #     value=["paraphrase-multilingual-MiniLM-L12-v2"],
    #     maxtags=1
    # )
    # # model_name="paraphrase-multilingual-MiniLM-L12-v2"

        
    # # --------------- threshold sim pour axe ------------------

    # threshold = st.number_input(
    #         "⬆️ Threshold de similarité pour matcher un axe:", 
    #         min_value=0, max_value=1, value=0.4, step=0.05, key="threshold_sim"
    #     )
    # st.markdown("<br>", unsafe_allow_html=True)
    

    # st.subheader("🔢 Auto-completion des axes thématiques")
    # st.write(f" [README] L'auto-completion des axes thématique prend en compte des titres, des mots-clés et des résumés,  \n"
    #          f"embeddés par le model {model_name}")
    

    # # 重新计算按钮
    # cols=st.columns([4,1])
    # with cols[1]:
    #     complete_button = st.button("Auto-compléter")
    # if complete_button:
    #     st.session_state.recompute_completion = True

    # # 只有点击按钮或第一次进入才执行
    # if st.session_state.get("recompute_completion", True):
    #     try:
    #         df_exploded=auto_completion_by_sim(df, model_name, threshold=threshold)
    #         st.session_state['df_exploded']=df_exploded
    #     except Exception as e:
    #         st.error(f"ERROR in 'auto_completion_by_sim' : {e}")
        
    #     # 计算完成后关闭标志，下次不自动重新计算
    #     st.session_state.recompute_completion = False