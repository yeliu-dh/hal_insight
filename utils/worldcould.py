from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import seaborn as sns    

import math
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

import re
import streamlit as st
import simplemma


def collect_texts_by_language(df, options, lang_col="language_s", langs=("en", "fr"))-> dict:
    """
    从 DataFrame 收集指定列的文本，并按语言分开。
    
    Parameters:
        df (pd.DataFrame): 数据
        columns (list): 要收集的列，例如 ["keyword_s", "abstract_s"]
        lang_col (str): 语言列名
        langs (tuple): 需要分开的语言
    
    Returns:
        dict: { "en": [文本], "fr": [文本] }
    """
    WC_MAP={"keyword_s":"mots clés",
            "abstract_s":'résumés'}
    
    texts = {lang: [] for lang in langs}

    for col in options:
        st.info(f"⚠️ Les {WC_MAP.get(col,'...')} sont manquants dans {df[col].isna().sum()}"
                f" ({df[col].isna().sum()*100/len(df):.2f}%) articles!")
        if col not in df.columns:
            continue
        for lang in langs:
            #选择莫语言+不为空的行：
            subset = df[(df[lang_col] == lang) & df[col].notna()]
            if not subset.empty:
                texts[lang].append(" ".join(subset[col].astype(str)).lower())# lang:['keyword_str','resume_str']
    for lang in texts:
        texts[lang] = " ".join(texts[lang])    

    return texts

def preprocess_text(text, stopwords, lang='fr'):
    """
    对文本列表做lemmatization和停用词过滤
    """

    # 确认输入的是str
    if isinstance(text, list):  # 如果传进来是list，先拼接
        text = " ".join(map(str, text))
    elif not isinstance(text, str):  # 如果是其他类型，转成字符串
        text = str(text)
    

    # 去除标点和非字母+lower()
    text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)
    text = text.lower().strip()

    # lemmatisation + enlever les stopwords
    clean_tokens=[simplemma.lemmatize(word, lang=lang) for word in text.split()]
    clean_text=" ".join([w for w in clean_tokens if w.isalpha() and w not in stopwords])

    return clean_text


    # lemmatisation + enlever les stopwords
    # all_tokens = []
    # for doc in texts:
    #     spacy_doc = nlp(doc)
    #     for token in spacy_doc:
    #         lemma = token.lemma_.lower()
    #         # 过滤停用词和标点
    #         if lemma.isalpha() and lemma not in stopwords:
    #             all_tokens.append(lemma)

# def preprocess_text(text, nlp_fr, nlp_en, stop_fr, stop_en):
#     # 去除标点和非字母
#     text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)
#     text = text.lower().strip()

#     # 使用 spacy 进行分词 + 词形还原
#     # 检测语言（简单用长度来区分，也可以用 langdetect）

#     doc_fr = nlp_fr(text)
#     doc_en = nlp_en(text)

#     #lemmatiser:
#     tokens = []
#     for token in doc_fr:
#         if token.lemma_ not in stop_fr and not token.is_punct and len(token.lemma_) > 2:
#             tokens.append(token.lemma_)
#     for token in doc_en:
#         if token.lemma_ not in stop_en and not token.is_punct and len(token.lemma_) > 2:
#             tokens.append(token.lemma_)

#     return " ".join(tokens)


def generate_wc(text, max_words, stopwords, title="Nuage de mots"):
    wc = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=max_words,
        stopwords=stopwords,
        colormap="viridis"
    ).generate(text)

    # 创建画布
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")  # 去掉坐标轴
    ax.set_title(title, fontsize=16)
    return fig


def compute_keyness(freq_slice, global_freq, method="llr"):
    """
    计算 keyness 值
    freq_slice: 当前子集词频 (pd.Series)
    global_freq: 全局词频 (pd.Series)
    method: "llr"=log-likelihood, "chi2"=chi-square
    """
    # 两个词表对齐
    all_words = set(freq_slice.index).union(global_freq.index)
    f_slice = freq_slice.reindex(all_words, fill_value=0)
    f_global = global_freq.reindex(all_words, fill_value=0)

    keyness_scores = {}
    N_slice = f_slice.sum()
    N_global = f_global.sum()

    for word in all_words:
        a = f_slice[word]       # 当前片段中该词频
        b = N_slice - a         # 当前片段中非该词频
        c = f_global[word]      # 全局该词频
        d = N_global - c        # 全局非该词频

        table = np.array([[a, b], [c, d]])

        if method == "chi2":
            chi2, _, _, _ = chi2_contingency(table, correction=False)
            score = chi2
        else:  # 默认 log-likelihood (G²)
            expected = table.sum(axis=1)[:, None] * table.sum(axis=0)[None, :] / table.sum()
            with np.errstate(divide="ignore", invalid="ignore"):
                ll = 2 * np.nansum(table * np.log((table + 1e-9) / expected))
            score = ll

        keyness_scores[word] = score

    return keyness_scores


def generate_keyness_wc(df, time_slices, max_words=100, stopwords=None, method="llr"):
    """
    根据时间片生成 keyness 演变词云
    """
    # --- 全局词频 ---
    texts_all = " ".join(df["keyword_s"].dropna().astype(str).str.lower())
    global_freq = pd.Series(texts_all.split()).value_counts()

    # --- 子图布局 ---
    n_cols = 3
    n_rows = math.ceil(len(time_slices) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 5))

    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = np.array([axes])
    elif n_cols == 1:
        axes = axes[:, None]

    # --- 遍历时间片 ---
    for idx, (y_start, y_end) in enumerate(time_slices):
        df_slice = df[(df["year"] >= y_start) & (df["year"] <= y_end)]
        text = " ".join(df_slice["keyword_s"].dropna().astype(str).str.lower())

        if text.strip():
            freq_slice = pd.Series(text.split()).value_counts()
            keyness = compute_keyness(freq_slice, global_freq, method=method)

            wc = WordCloud(
                width=400, height=400, background_color="white",
                max_words=max_words, stopwords=stopwords
            ).generate_from_frequencies(keyness)
        else:
            wc = None

        row, col = divmod(idx, n_cols)
        ax = axes[row, col]
        if wc:
            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(f"{y_start}-{y_end}", fontsize=12)#小图标题
        ax.axis("off")

    # --- 去掉多余子图 ---
    for j in range(idx + 1, n_rows * n_cols):
        row, col = divmod(j, n_cols)
        axes[row, col].axis("off")
    
    
    # --- 添加全图标题 ---
    start_year = time_slices[0][0]
    end_year = time_slices[-1][1]
    fig.suptitle(f"Évolution du nuage de mots ({start_year}-{end_year})", fontsize=16)


    plt.tight_layout()
    return fig
