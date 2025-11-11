import streamlit as st
import pandas as pd
import re
from sentence_transformers import SentenceTransformer
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import pipeline
from langdetect import detect

import hdbscan
import numpy as np
import time

def simple_sentence_split(text, min_words=5):
    """
    简单分句函数：
    - 根据句号、问号、感叹号、换行符分句
    - 过滤掉过短的句子（词数 < min_words）
    """
    # 正则分割：句末标点 [.?!] 或换行 \n，后面可有空格
    pattern = r'[.?!]\s+|\n+'
    sentences = re.split(pattern, text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) >= min_words]

    return sentences


def cluster_sentences_hdbscan(sentences, embedding_model, min_cluster_size=5, top_k_per_cluster=5, min_words_threshold=20, max_tokens=512):
    """
    用 HDBSCAN 自动聚类句子并选出每簇的代表句。
    自动控制每个簇的 tokens 数不超过模型容量。
    
    参数:
    - sentences: list[str]
    - tokenizer: 与生成模型对应的 tokenizer:默认为T5
    - min_cluster_size: 每个簇的最小大小
    - top_k_per_cluster: 每个簇最多选几句
    - max_tokens: 模型最大 token 长度
    """
    tokenizer = T5Tokenizer.from_pretrained("plguillou/t5-base-fr-sum-cnndm")#分词模型

    if not sentences:
        return []

    # 1️⃣ 向量化
    embeddings = embedding_model.encode(sentences)

    # 2️⃣ 聚类
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric='euclidean'
    ).fit(embeddings)

    labels = clusterer.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"🌀 HDBSCAN identifie {n_clusters} clusters sous l'axe!")

    clusters = []

    # 3️⃣ 遍历每个簇
    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue  # 跳过噪声点

        cluster_idx = np.where(labels == cluster_id)[0]
        cluster_emb = embeddings[cluster_idx]
        center = cluster_emb.mean(axis=0)
        distances = np.linalg.norm(cluster_emb - center, axis=1)

        # 选距离中心最近的句子
        sorted_idx = cluster_idx[np.argsort(distances)]
        
        # 参数：长度/完整度阈值
        selected_sentences = []
        total_tokens = 0

        for j in sorted_idx:
            sent = sentences[j]
            n_tokens = len(tokenizer.encode(sent, add_special_tokens=False))
            n_words = len(sent.split())

            # 只选较长、较完整的句子
            if n_words < min_words_threshold:
                continue

            if total_tokens + n_tokens > max_tokens:
                # print(f"⚠️ Cluster {cluster_id}: dépasse la limite ({max_tokens}) tokens, tronqué!")
                break

            selected_sentences.append(sent)
            total_tokens += n_tokens

            # 达到 top_k_per_cluster 则停止
            if len(selected_sentences) >= top_k_per_cluster:
                break

        print(f'{total_tokens} tokens in cluster {cluster_id} with {len(selected_sentences)} sentences!')

        # 按原顺序排列
        selected_sentences = sorted(selected_sentences, key=lambda s: sentences.index(s))
        clusters.append(selected_sentences)
    return clusters




def t5summarize(text, user_prompt, tokenizer, model, max_length=100, min_length=50, warn_threshold=500):
    # 输入：
    input_text = f"summarize:" + user_prompt+ text
    # input_text=prompt+text

    # 估算输入 token 长度
    tokens = tokenizer.encode(input_text, truncation=False, add_special_tokens=False)
    n_tokens = len(tokens)
    # print(f"Input length (tokens): {n_tokens}")

    if n_tokens > warn_threshold:
        print(f"⚠️ ALERT :  {n_tokens} tokens，proche de la limite du model (512)，risque de troncation!")
    # 
    # 编码：
    inputs = tokenizer(
        input_text, return_tensors="pt", max_length=512, truncation=True
    )
    # 生成：
    summary_ids = model.generate(
        **inputs,
        max_length=max_length,
        min_length=min_length,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary




# translator_en = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
# translator_es = pipeline("translation", model="Helsinki-NLP/opus-mt-es-fr")


def translate_to_fr(text,translator_en, translator_es):
    def detect_language(text):
        try:
            return detect(text)
        except:
            return "fr"  # 默认法语
    
    lang = detect_language(text) 
    if lang == "en":
        return translator_en(text, max_length=512)[0]['translation_text']
    elif lang == "es":
        return translator_es(text, max_length=512)[0]['translation_text']
    else:
        return text  # already fr or unknown
    

def extract_thema_chunks(df_exploded, embedding_model,translator_en, translator_es):
    axe_map = {
            "nan":"nan",
            "1": "Performances et responsabilités",
            "2": "Société de services et services à la société",
            "3": "Innovations, transformations et résistances organisationnelles et sociétales",
            "4": "Ouvrages pédagogiques"
        }

    df_summary=df_exploded.dropna(subset='predicted_axe')

    df_summary["text_for_summary"] = (
        df_summary["abstract_s"].fillna('')
    )

    axe_groups = df_summary.groupby('predicted_axe')['text_for_summary'].apply(" ".join).reset_index(name='sentences')
    axe_groups['axe']=axe_groups['predicted_axe'].map(axe_map)#map

    axe_groups['sentences']=axe_groups['sentences'].apply(simple_sentence_split)
    axe_groups['chunks']=axe_groups['sentences'].apply(lambda x : cluster_sentences_hdbscan(x, embedding_model))
    axe_groups['chunks'] = axe_groups['chunks'].apply(
        lambda chunk_list: [
            [translate_to_fr(sent,translator_en, translator_es) for sent in chunk]  # 翻译每个句子1
            for chunk in chunk_list                    # 遍历每个 chunk
        ]
    )
    return axe_groups



# def generate_summaries(axe_groups, tokenizer, model, translator_en, translator_es, max_length=100,min_length=20):
#     axe_representative={r['axe']:r['chunks'] for i,r in axe_groups.iterrows()}

#     axe_summary = {}
#     for axe_name, chunks in axe_representative.items():
#         #按chunk生成summaries，并拼接
#         summaries=" "
#         for i, chunk in enumerate(chunks):
#             user_prompt="introduire la problématique de l'axe {axe_name}"
#             summary=t5summarize(" ".join(chunk), user_prompt, tokenizer, model, max_length=max_length, min_length=min_length)
            
#             # 若有非法语，翻译
#             summary_fr=translate_to_fr(summary, translator_en, translator_es)
#             summaries+=f"sous-thème {i+1}:{summary_fr}.\n"

#         st.write(f"🔹 Axe {axe_name} Résumé:\n{summaries}\n")
#         axe_summary[axe_name] = summaries
#     return axe_summary

def generate_summaries(
        axe_groups,
        tokenizer,
        model,
        translator_en=None,
        translator_es=None,
        max_length=100,
        min_length=20
    ):
        """
        Génère des résumés par axe thématique.
        
        Params:
        - axe_groups: DataFrame avec colonnes ['axe', 'chunks']
        - tokenizer: tokenizer HuggingFace pour le modèle de summarization
        - model: modèle HuggingFace pour le summarization
        - translator_en, translator_es: pipelines de traduction (optionnel)
        - max_length, min_length: longueur max/min du résumé
        """
        
        axe_summary = {}
        axe_representative = {r['axe']: r['chunks'] for i, r in axe_groups.iterrows()}

        for axe_name, chunks in axe_representative.items():
            summaries = ""

            for i, chunk in enumerate(chunks):
                # Prompt personnalisé
                user_prompt = f"introduire la problématique de l'axe {axe_name}: "

                # Génération du résumé
                summary = t5summarize(
                    " ".join(chunk),
                    user_prompt,
                    tokenizer,
                    model,
                    max_length=max_length,
                    min_length=min_length
                )

                # Traduction si nécessaire
                if translator_en is not None and translator_es is not None:
                    summary_fr = translate_to_fr(summary, translator_en, translator_es)
                else:
                    summary_fr = summary

                summaries += f"\n -sous-thème {i+1}: {summary_fr}.\n"

            st.write(f"\n🔹**Axe {axe_name}** :\n")
            st.write(f"{summaries}\n\n")
            axe_summary[axe_name] = summaries

        # Stockage dans session_state pour éviter recalcul
        st.session_state['axe_summary'] = axe_summary

        return axe_summary
