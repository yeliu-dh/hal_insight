# basic:
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time, os, sys, importlib



# model 
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score, multilabel_confusion_matrix
from sklearn.metrics import classification_report, precision_recall_curve, confusion_matrix


# model:
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import random
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from lightgbm import LGBMClassifier
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
import lightgbm as lgb
import joblib
from sklearn.calibration import calibration_curve



# my utils
from utils.upload import missing_data_warning
from utils.preprocess import load_external_json
from utils.preprocess import preprocess_text
from utils.preprocess import explode_by_col
from utils.plot import make_pie_chart

## auto-completion :

from utils.auto_completion import parse_axes, split_axe, split_axe
from utils.auto_completion import filtrate_df_to_emb, emb_text, check_before_emb_text
from utils.auto_completion import to_df_long
from utils.auto_completion import load_predict, merge_axes



#===============================ST VERSION===========================================

def gather_predicted_axes_st(df_long_predicted, 
                       df_all,
                       groupby_col='halId_s'):
    
    axe_cols = ["pred_axe1", "pred_axe2", "pred_axe3", "pred_axe4"]
    # 按照id聚合：
    df_hal = df_long_predicted.groupby(groupby_col)[axe_cols].max().reset_index()

    def axes_to_str(row):
        axes = []
        for i, col in enumerate(axe_cols, start=1):
            if row[col] == 1:# pred_axeK 的值是0/1
                axes.append(str(i))

        return "; ".join(set(axes))     # 例如 "1; 2; 4"
    df_hal["pred_axes_str"] = df_hal.apply(axes_to_str, axis=1)
    
    # mapping_DICT {id:"axe;axe"}
    hal_axes_dict = dict(zip(df_hal["halId_s"], df_hal["pred_axes_str"]))
    
    # str merged back to df_all (insert):  predicted_axe : '1; 2; 3' 
    if "predicted_axe" in df_all.columns:
        df_all.drop(columns='predicted_axe', inplace=True)
    idx = df_all.columns.get_loc("axe")
    df_all.insert(idx + 1, "predicted_axe", df_all["halId_s"].map(hal_axes_dict))

    # no_pred_warning_st(df_long_predicted, df_all, groupby_col="halId_s")    
    # [CHECK] 检查df_long_predicted中在prediction之后是否还有没有axe的行:
    df_no_predaxe=df_hal[df_hal[axe_cols].sum(axis=1)==0]
    if len(df_no_predaxe)>0:
        st.write(f"[INFO] {len(df_no_predaxe)} lignes qui n'ont pas de prédictions: \n")
        st.dataframe(df_all[df_all['halId_s'].isin(df_no_predaxe['halId_s'].tolist())][['halId_s','title_s','keyword_s','abstract_s','axe',"predicted_axe"]].head())
    else :
        st.write(f"[INFO] Au moins une prédiction pour chaque ligne sans axe!")
   
    return df_all

 
def apply_auto_completion_axes_st(
        df_all, # df_all_path="data/20251201-ProductionScientifiqueIRG-__-202512_2734art.csv",
        df_all_emb_path="external_data/df_all_3emb.parquet",
        mlp_model_path="model/best_mlp_3emb_2.pt",
        lr_model_path="model/best_lr_3emb.pt",
        lgb_model_path="model/best_lgb_3emb.txt",
        t_lr=0.25, t_lgb=0.95, f1_lr=0.44, f1_lgb=0.35, t_ens=0.52
        
    ):
    import os
    import pandas as pd
    import numpy as np
    import streamlit as st
    st.session_state.df_all=df_all.copy()
    # st.write(os.getcwd())# D:\Work\IRG\hal_insight

    #------------------------------------------read&filtrate-----------------------------------------------
    st.write(f"**[ETAPE1] Lire le CSV et sélectionner les lignes sans axes**")
    # df_all = pd.read_csv(df_all_path)
    df_noaxe = df_all[(df_all['axe'].isna())|(df_all['axe']=="nan")]
    df_hasaxe = df_all[~df_all['halId_s'].isin(df_noaxe['halId_s'])]

    st.write(f"[INFO] Répartition des axes: \n{df_all.axe.value_counts(dropna=False)}")
    st.write(f"- len df_all: {len(df_all)}")
    st.write(f"- len df_noaxe: {len(df_noaxe)}")
    st.write(f"- len df_hasaxe: {len(df_hasaxe)}")

    #------------------------------------------splitaxe-----------------------------------------------
    st.write(f"**[ETAPE2] Split axe en 4 colonnes 'axe1-4' et 'axes_vec'**")
    df_noaxe = split_axe(df_noaxe)
    st.session_state.df_noaxe=df_noaxe

    #------------------------------------------embeddings-----------------------------------------------
    st.write(f"**[ETAPE3] Embeddings des titres, mots-clés et résumés**")
   
    if 'df_noaxe_embedded' in st.session_state:
        st.write(f"[INFO] Embeddings déjà existants")

    else:
        st.write(f"[LOAD] Charge le modèle d'embeddings 'BAAI/bge-m3'...")
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer("BAAI/bge-m3")
        
        st.write(f"[INFO] Trouver des articles qui n'ont pas d'axes...")
        df_noaxe_embedded=check_before_emb_text(df=df_noaxe, embedding_model=embedding_model, 
                                               batch_size=32, df_all_emb_path=df_all_emb_path)
        st.session_state['df_noaxe_embedded']=df_noaxe_embedded

    #------------------------------------------long df-----------------------------------------------
    st.write(f"**[ETAPE4] Transformer df_noaxe en df_noaxe_long**")
    if 'df_noaxe_embedded' in st.session_state:
        df_noaxe_embedded=st.session_state['df_noaxe_embedded']
        df_noaxe_long = to_df_long(df_noaxe_embedded, cols=['emb_title_s','emb_keyword_s','emb_abstract_s'],
                                pq_long_path=None)
       
    #------------------------------------------prediction-----------------------------------------------
    st.write(f"**[ETAPE5] Prédire les axes avec les modèles MLP/LR/LGB**")
    df_long_predicted = load_predict(df=df_noaxe_long,
                                     mlp_model_path=mlp_model_path,
                                     lr_model_path=lr_model_path,
                                     lgb_model_path=lgb_model_path,
                                     t_lr=t_lr, t_lgb=t_lgb, f1_lr=f1_lr, f1_lgb=f1_lgb, t_ens=t_ens)

    #------------------------------------------merge predictions----------------------------------------
    st.write(f"**[ETAPE6] Fusionner les prédictions avec le df original**")
    df_all=st.session_state.df_all
    df_all=gather_predicted_axes_st(df_long_predicted, df_all, groupby_col='halId_s')

    #final axe:
    df_all['final_axe'] = df_all.apply(merge_axes, axis=1)

    st.write(f"[INFO] Df de {len(df_all)} lignes avec des axes fusionnés:\n")
    st.dataframe(df_all[['halId_s','title_s',"keyword_s",'abstract_s','axe','predicted_axe','final_axe']])
    st.session_state['df_all_pred']=df_all


    return df_all


def evaluate_model_st(y_true, y_pred):
    import numpy as np
    import streamlit as st
    import matplotlib.pyplot as plt
    from sklearn.metrics import (
        f1_score, precision_score, recall_score,
        classification_report, hamming_loss,
        accuracy_score, confusion_matrix,
        ConfusionMatrixDisplay
    )
    # ------------------ Overall metrics ------------------
    f1_micro = f1_score(y_true, y_pred, average='micro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    precision_micro = precision_score(y_true, y_pred, average='micro', zero_division=0)
    recall_micro = recall_score(y_true, y_pred, average='micro', zero_division=0)
    hamming = hamming_loss(y_true, y_pred)
    subset_acc = accuracy_score(y_true, y_pred)

    st.write(f"- Micro  F1: {f1_micro:.4f}")
    st.write(f"- Macro  F1: {f1_macro:.4f}")
    st.write(f"- Micro Precision : {precision_micro:.4f}")
    st.write(f"- Micro Recall    : {recall_micro:.4f}")
    st.write(f"- Hamming Loss    : {hamming:.4f}")
    st.write(f"- Subset Accuracy : {subset_acc:.4f}\n")

    # ------------------ Per-class report ------------------
    st.write("- Per-class classification report:")
    st.text(classification_report(y_true, y_pred, target_names=['axe1','axe2','axe3','axe4']))

    # ------------------ Confusion matrices ------------------
    n_classes = y_true.shape[1]
    class_names = ['axe1','axe2','axe3','axe4']
    fig, axes = plt.subplots(1, n_classes, figsize=(4*n_classes, 4))

    for c in range(n_classes):
        cm = confusion_matrix(y_true[:, c], y_pred[:, c], labels=[0,1])
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
        disp.plot(ax=axes[c], cmap='Blues', colorbar=False)
        axes[c].set_title(class_names[c])

    plt.tight_layout()
    st.pyplot(fig)  # <-- 显式传入 figure
    return fig
    


def evaluate_auto_classification_axes(
        df_all,
        df_all_emb_path="external_data/df_all_3emb.parquet",
        mlp_model_path="model/best_mlp_3emb_2.pt",
        lr_model_path="model/best_lr_3emb.pt",
        lgb_model_path="model/best_lgb_3emb.txt",
        t_lr=0.25, t_lgb=0.95, f1_lr=0.44, f1_lgb=0.35, t_ens=0.52):
    import os
    import pandas as pd
    import numpy as np
    
    #------------------------------------------read&filtrate-----------------------------------------------
    df_noaxe = df_all[(df_all['axe'].isna())|(df_all['axe']=="nan")]
    df_hasaxe = df_all[~df_all['halId_s'].isin(df_noaxe['halId_s'])]
    st.write(f"[INFO] L'évaluation se fait sur {len(df_hasaxe)} lignes.")
    #------------------------------------------splitaxe-----------------------------------------------
    df_hasaxe = split_axe(df_hasaxe)
    # st.write(f'df_has_axe split: {len(df_hasaxe)} lignes')
    # st.dataframe(df_hasaxe.head())

    #------------------------------------------embeddings-----------------------------------------------
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("BAAI/bge-m3")
    # 
    df_hasaxe_embedded=check_before_emb_text(df=df_hasaxe, embedding_model=embedding_model, 
                                               batch_size=32, df_all_emb_path=df_all_emb_path)    
    # st.session_state['df_hasaxe_embedded']=df_hasaxe_embedded

    #-----------------------------------------df_long----------------------------------------------------
    df_hasaxe_long = to_df_long(df_hasaxe_embedded, cols=['emb_title_s','emb_keyword_s','emb_abstract_s'],
                                pq_long_path=None)
    # st.session_state['df_hasaxe_long']=df_hasaxe_long


    #----------------------------------------prediction-----------------------------------------------
    df_long_predicted = load_predict(df=df_hasaxe_long,
                                        mlp_model_path=mlp_model_path,
                                        lr_model_path=lr_model_path,
                                        lgb_model_path=lgb_model_path,
                                        t_lr=t_lr, t_lgb=t_lgb, f1_lr=f1_lr, f1_lgb=f1_lgb, t_ens=t_ens)
    

    # --------------------------------------merge back---------------------------------------------
    ## merge+no_pred_warning to df_hasaxe
    df_hasaxe_pred=gather_predicted_axes_st(df_long_predicted, df_all=df_hasaxe, groupby_col='halId_s')    
    # split but not long 

    # [INFO] def parse_axes(axe_str):
        # # map axe 字符到索引
        # axe_map = {"1": 0, "2": 1, "3": 2, "4": 3}

        # # 如果是 nan 或 "nan"，返回全 0
        # if pd.isna(axe_str) or str(axe_str).lower() == "nan":
        #     return [0, 0, 0, 0]
        # # 拆分并 strip
        # labels = [s.strip() for s in str(axe_str).split(";")]
        # vec = [0, 0, 0, 0]
        # for lbl in labels:
        #     if lbl in axe_map:
        #         vec[axe_map[lbl]] = 1
        # return vec

    df_hasaxe_pred['predicted_axes_vec'] = df_hasaxe_pred["predicted_axe"].apply(parse_axes)
    st.write(f"Df de {len(df_hasaxe_pred)} lignes avec des axes prédits \n")
    st.dataframe(df_hasaxe_pred.head())

    # np.stack!!!
    y_true = np.stack(df_hasaxe_pred['axes_vec'].values).astype(np.float32)
    y_pred = np.stack(df_hasaxe_pred['predicted_axes_vec'].values).astype(np.float32)
    # st.write(f"y_true/pred shape:{y_true.shape}, {y_pred.shape}")
    
    evaluate_model_st(y_true=y_true, y_pred=y_pred)
    
    return 

