import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score, multilabel_confusion_matrix



# my utils
from utils.upload import missing_data_warning
from utils.preprocess import load_external_json
from utils.preprocess import preprocess_text
from utils.preprocess import explode_by_col
from utils.plot import make_pie_chart

def auto_completion_by_sim(df, embedding_model):

    st.write("NB. L'auto-completion des axes thématique prend en compte des titres, des mots-clés et des résumés,\n"
             "embeddés par le model 'paraphrase-multilingual-MiniLM-L12-v2'.")
    model=embedding_model

    #=============================step1：clean text=================================
    def safe_get(val):
        return "" if pd.isna(val) else str(val)

    df["clean_text"] = df.apply(
        lambda r: preprocess_text(
            safe_get(r["title_s"]) + " " +
            safe_get(r["keyword_s"]) + " " +
            safe_get(r["abstract_s"]),
            user_stopwords=None,
            lang=r['language_s']
        ),
        axis=1
    )
     
    #=============================step2:embedding==================================
    # with st.spinner("Embedding..."):
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    df["embedding"] = df["clean_text"].apply(lambda x: model.encode(x))


    # =====================step3 :prediction by similarity between embeddings=====================

    df["original_axe"] = df["Axe"]#保留原值
    # missing_data_warning(df, col='Axe', show_distribution=False)

    df=explode_by_col(df, col="Axe")#fillna('nan')#原axe已经被exploded
    df["Axe"] = df["Axe"].replace("nan", np.nan)


    #计算每一个主题的平均向量：
    axe_means = df[df["Axe"].notna()].groupby("Axe")["embedding"].apply(
        lambda emb: np.mean(list(emb), axis=0)
    )

    def predict_axes_for_row(row, threshold=0.4):
        if pd.isna(row["Axe"]):
            sims = {axe: cosine_similarity([row["embedding"]], [axe_means[axe]])[0][0] for axe in axe_means.index}
            # 返回匹配的 Axe
            return [axe for axe, score in sims.items() if score >= threshold]
        else:
            return [row["Axe"]]

    df["predicted_axe"] = df.apply(lambda row: predict_axes_for_row(row, threshold=0.45), axis=1)

    # print(df.Axe.value_counts(dropna=False),'\n')
    # print(df.predicted_axe.value_counts(dropna=False),'\n')
    # missing_data_warning(df, col='original_axe', show_distribution=False)
    df_exploded = df.explode("predicted_axe")
    

    #==========================快速画图=======================
    
    st.write("Comparasion entrte les vrais axes et axes prédits")
    cols=st.columns(2)
    for i, col in enumerate(['Axe','predicted_axe']):  
        with cols[i]:
            counts=df[col].fillna('NaN').value_counts()
            cmap = cm.get_cmap('viridis')
            colors = [cmap(i / len(counts)) for i in range(len(counts))]

            fig, ax = plt.subplots(figsize=(6,6))
            ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.set_title(col)
            st.pyplot(fig)

    

    #=======================step 4: evaluate by metrics================================ 
    
    df_valid = df[df["Axe"].notna()].drop_duplicates(subset='halId_s')

    # 所有可能的Axe标签
    unique_labels = sorted(df_valid["Axe"].dropna().unique().tolist())
    #['1', '2', '3']

    # 转为多标签二进制格式
    def to_multilabel(row):# 把axe数字变成binary 2==[010]
        y_true = [int(x in row["original_axe"]) for x in unique_labels]
        y_pred = [int(x in row["predicted_axe"]) for x in unique_labels]
        return y_true, y_pred

    y_true, y_pred = zip(*df_valid.apply(to_multilabel, axis=1))
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    st.write("L'accuracy de la prediction :\n")
    # 微平均和宏平均的precision/recall/f1
    st.write("Precision (micro):", precision_score(y_true, y_pred, average="micro"))
    st.write("Recall (micro):", recall_score(y_true, y_pred, average="micro"))
    st.write("F1 (micro):", f1_score(y_true, y_pred, average="micro"))

    st.write("\nPrecision (macro):", precision_score(y_true, y_pred, average="macro"))
    st.write("Recall (macro):", recall_score(y_true, y_pred, average="macro"))
    st.write("F1 (macro):", f1_score(y_true, y_pred, average="macro"))

    ## precision==1,说明pred中的结果都在original中（pred都是正确的），但是还有一部分没有预测出来（还有部分标签没被包含!）
    return 



