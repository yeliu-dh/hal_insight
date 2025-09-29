from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import seaborn as sns    

import math
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency


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




# def generate_wc(text, max_words, stopwords):
#     wc = WordCloud(
#             width=800,
#             height=400,
#             background_color="white",
#             max_words=max_words,
#             stopwords=stopwords,
#             colormap="viridis"
#         ).generate(text)



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
