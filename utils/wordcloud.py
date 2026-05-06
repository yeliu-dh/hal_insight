from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import seaborn as sns    
import math
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
import re
import streamlit as st
from collections import defaultdict

#my utils:
from utils.preprocess import wrap_text, collect_clean_texts_by_col
from utils.upload import load_external_json, read_json
 
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
    fig, ax = plt.subplots(figsize=(8,6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")  # 去掉坐标轴
    ax.set_title(title, fontsize=16)
    return fig


def generate_wc_param(df, options, group_by, wc_par_lang, exclude_nan, max_words, stopwords, date_field_col):
    #1. collect:
    text_groups=collect_clean_texts_by_col(df, options, stopwords, exclude_nan, col=group_by, lang_col="language_s")
    # text_groups={
    #   "(axe)1": {"en": "clean text", "fr": "..."},
    #   "(axe)2": {"en": "...", "fr": "..."}
    # }

    #2.a title
    COL_MAP = {
        "Global": "global",
        "axe": "par axe",
        # "Cl. FNEGE": "par classe FNEGE"#去除
    }    
    group_by_readable=COL_MAP.get(group_by, group_by)
    
    
    # 2.b date
    if date_field_col in df.columns:
        # df[date_field_col] = pd.to_datetime(df[date_field_col], errors="coerce")
        latest_date = df[date_field_col].max()
        latest_y = latest_date.strftime("%Y") if pd.notnull(latest_date) else "Aucune date valide"

        earliest_date=df[date_field_col].min()
        earliest_y = earliest_date.strftime("%Y") if pd.notnull(latest_date) else "Aucune date valide"
        period_y=f"{earliest_y}~{latest_y}"#图标题


    # wc : 先分语言，再分global/axe
    if not wc_par_lang:  # 不分语言 → 合并 EN + FR
        suptitle=f"Nuage de mots {group_by_readable} entre {period_y}"
        st.markdown(
            f"<h3 style='text-align: center;'> {suptitle} </h3>",
            unsafe_allow_html=True
        )#居中显示

        for cat, langs in text_groups.items():#global则只循环一次，axe循环多次，但没有keyness对比             
            #小图标题
            if group_by=="Global":
                title=" "
                
            elif group_by=='axe': # axe
                axe_map = {
                    "1": "Performances et responsabilités",
                    "2": "Société de services et services à la société",
                    "3": "Innovations, transformations et résistances organisationnelles et sociétales",
                    "4": "Ouvrages pédagogiques",
                    "nan":'nan'
                }
                title_raw = f"{group_by} {cat} - {axe_map.get(cat, '?')}"
                title = wrap_text(title_raw, max_len=50, html=False)

            #画图：
            combined_text = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
            # st.write(f"{cat}: len(en)={len(langs.get('en',''))}, len(fr)={len(langs.get('fr',''))}")
            # st.write(f"Sample text (fr) for {cat}:", langs.get('fr', '')[:300])
                        
            if combined_text:
                fig = generate_wc(
                    langs.get("en", "") + " " + langs.get("fr", ""),  # lang 随便传一个
                    max_words,
                    stopwords,
                    title=title
                )
            ###
            fig.tight_layout(rect=[0, 0, 1, 0.95])  # 顶部留 5% 给 suptitle
            # fig.suptitle(suptitle, fontsize=10, ha="center")#每张图又加上一个大标题XXX
            st.pyplot(fig)#***
            
            ###不能输出显示，否则只能输出一个!?
            

    else: # 分语言 → EN/FR 左右列显示，每个类别单独一行
        suptitle=f"Nuage de mots {group_by_readable} et par langue entre {period_y}"
        st.markdown(
            f"<h3 style='text-align: center;'> Nuage de mots {group_by_readable} par langue entre {period_y}</h3>",
            unsafe_allow_html=True
        )
        for cat, langs in text_groups.items():
            cols = st.columns(2)
            for i, lang in enumerate(langs.keys()):
                with cols[i]:
                    if group_by=="Global":
                        title=lang
                    else:
                        title=f"{group_by} {cat}-{lang}"
                    
                    text = langs.get(lang, "").strip()
                    if text:
                        fig = generate_wc(text, max_words, stopwords, title=title)
                        st.pyplot(fig) #*?????
                    
                    else :
                        st.warning(f"Texte invalide dans la catégorie {cat}-{lang}!")
    return 






#==========================================================================================#
#==========================================================================================#
#==========================================================================================#

# def create_time_slices(df, granularity, date_field_col):
#     """
#     根据颗粒度生成时间切片
#     granularity: "month" | "quarter" | "year" | "3year" | "5year"
#     """
#     df = df.copy()
#     # df[date_field_col] = pd.to_datetime(df[date_field_col], errors="coerce")

#     # 提取年月
#     df["year"] = df[date_field_col].dt.year
#     df["month"] = df[date_field_col].dt.month

#     start_year, end_year = df["year"].min(), df["year"].max()

#     if granularity == "Mensuel":
#         # 逐月
#         months = pd.period_range(df[date_field_col].min().to_period("M"),
#                                  df[date_field_col].max().to_period("M"), freq="M")
#         # time_slices = [
#         #     (p.start_time.tz_localize("UTC"), p.end_time.tz_localize("UTC"))
#         #     for p in months
#         # ]
#         time_slices = [(p.start_time, p.end_time) for p in months]

#     elif granularity == "Trimestriel":
#         # 逐季度
#         quarters = pd.period_range(df[date_field_col].min().to_period("Q"),
#                                    df[date_field_col].max().to_period("Q"), freq="Q")
#         time_slices = [(p.start_time, p.end_time) for p in quarters]
#         # time_slices = [
#         #     (p.start_time.tz_localize("UTC"), p.end_time.tz_localize("UTC"))
#         #     for p in quarters
#         # ]
        
        
#     elif granularity == "Annuel":
#         step_year = 1
#         time_slices = [(y, min(y + step_year - 1, end_year))
#                        for y in range(start_year, end_year + 1, step_year)]

#     elif granularity == "Tous les 3 ans":
#         step_year = 3
#         time_slices = [(y, min(y + step_year - 1, end_year))
#                        for y in range(start_year, end_year + 1, step_year)]

#     elif granularity == "Tous les 5 ans":
#         step_year = 5
#         time_slices = [(y, min(y + step_year - 1, end_year))
#                        for y in range(start_year, end_year + 1, step_year)]
#     else:
#         time_slices=None

#     # else:  # 默认年度
#     #     time_slices = [(y, y) for y in range(start_year, end_year + 1)]
#     # st.info(f"Granularité {granularity}:{time_slices}")    
    
#     return time_slices

import pandas as pd

def create_time_slices(df, granularity, date_field_col, force_utc=False):
    """
    根据颗粒度生成时间切片，并保证 df 和 time_slices 时区一致

    参数：
    - df: DataFrame
    - granularity: "Mensuel" | "Trimestriel" | "Annuel" | "Tous les 3 ans" | "Tous les 5 ans"
    - date_field_col: 日期列名
    - force_utc: 是否强制转换为 UTC（推荐 True）

    返回：
    - time_slices: list of (start, end)
    """

    df = df.copy()

    # ---------- 1. 统一 datetime ----------
    df[date_field_col] = pd.to_datetime(df[date_field_col], errors="coerce")

    # ---------- 2. 处理时区 ----------
    tz = df[date_field_col].dt.tz

    if tz is None:
        # 没有时区 → 加 UTC
        df[date_field_col] = df[date_field_col].dt.tz_localize("UTC")
        tz = "UTC"
    else:
        if force_utc:
            # 已有时区 → 转 UTC
            df[date_field_col] = df[date_field_col].dt.tz_convert("UTC")
            tz = "UTC"

    # ---------- 3. 提取时间字段 ----------
    df["year"] = df[date_field_col].dt.year
    df["month"] = df[date_field_col].dt.month

    start_year = int(df["year"].min())
    end_year = int(df["year"].max())

    # ---------- 4. 构建 time_slices ----------
    if granularity == "Mensuel":
        periods = pd.period_range(
            df[date_field_col].min().to_period("M"),
            df[date_field_col].max().to_period("M"),
            freq="M"
        )
        time_slices = [
            (
                p.start_time.tz_localize(tz),
                p.end_time.tz_localize(tz)
            )
            for p in periods
        ]

    elif granularity == "Trimestriel":
        periods = pd.period_range(
            df[date_field_col].min().to_period("Q"),
            df[date_field_col].max().to_period("Q"),
            freq="Q"
        )
        time_slices = [
            (
                p.start_time.tz_localize(tz),
                p.end_time.tz_localize(tz)
            )
            for p in periods
        ]

    elif granularity == "Annuel":
        step = 1
        time_slices = [
            (y, min(y + step - 1, end_year))
            for y in range(start_year, end_year + 1, step)
        ]

    elif granularity == "Tous les 3 ans":
        step = 3
        time_slices = [
            (y, min(y + step - 1, end_year))
            for y in range(start_year, end_year + 1, step)
        ]

    elif granularity == "Tous les 5 ans":
        step = 5
        time_slices = [
            (y, min(y + step - 1, end_year))
            for y in range(start_year, end_year + 1, step)
        ]

    else:
        return None

    return time_slices





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





def generate_keyness_wc(df, options, exclude_nan, group_by, 
                        time_slices, col_val=None, 
                        max_words=100, stopwords=None, method="llr", 
                        date_field_col="publicationDate_tdate"):
    """
    根据时间片生成 keyness 演变词云+小图
    stopwords==user_stopwords
    """
    # 规范日期格式
    df = df.copy()
    # encore
    # df[date_field_col] = pd.to_datetime(df[date_field_col], utc=True errors="coerce")
    df["year"] = df[date_field_col].dt.year #筛选用
       
    
    #-----------time_slices-------------:
    # time_slices=create_time_slices(df, granularity=granularity)

    # ------------- 绘图布局 -------------
    
    if group_by=="Global":    
        n_cols = 4 if len(time_slices) >=  4 else len(time_slices) #按季度可以一年为一行
    else: # 输入已经筛选过的df!
        n_cols=len(time_slices)
    n_rows = math.ceil(len(time_slices) / n_cols)# 计算所需行数
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 5))# 按照行数列数计算图的大小
    axes = np.array(axes).reshape(n_rows, n_cols)  # 保证二维结构
    

    # --- 全局词频 ---
    text_groups = collect_clean_texts_by_col(df, options, stopwords, exclude_nan, col=group_by)    
    # text_groups={
    #   "Global": {"en": "clean text", "fr": "..."},
    # }
    # 或
    # text_groups={
    #     # "1": {"en": "clean text", "fr": "..."}
    # }
    
    for cat, langs in text_groups.items(): 
        texts_all = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
    global_freq = pd.Series(texts_all.split()).value_counts()
    

    for idx, t in enumerate(time_slices):#不变
        # 时间切片可为 (start_date, end_date) 或 (start_year, end_year)
        if isinstance(t[0], pd.Timestamp):  # 月/季度模式
            mask = (df[date_field_col] >= t[0]) & (df[date_field_col] <= t[1])
            label = t[0].strftime("%Y-%m")
        else:
            y_start, y_end = t
            mask = (df["year"] >= y_start) & (df["year"] <= y_end)
            label = f"{y_start}-{y_end}" if y_start != y_end else str(y_start)
        
        #串联这个时间片中所有clean_text。若是df_by_axe，则只有一个cat
        df_slice = df[mask]
        sliced_text_groups= collect_clean_texts_by_col(df_slice, options, stopwords, exclude_nan=exclude_nan, col=group_by, lang_col="language_s")
        text=" "
        for cat, langs in sliced_text_groups.items(): 
            text +=(langs.get("en", "") + " " + langs.get("fr", "")).strip()

        # 选择当前子图的位置：在cols数固定的情况下，按照idx自动排列到某一行
        row, col = divmod(idx, n_cols)#已知idx即可计算小图的位置
        ax = axes[row, col]
        ax.axis("off")



        # --- 局部词频 ---
        # stopwords_nltk=load_external_json("external_data/stopwords_nltk.json")
        stopwords_nltk=read_json("external_data/stopwords_nltk.json")
        
        if text:
            freq_slice = pd.Series(text.split()).value_counts()
            keyness = compute_keyness(freq_slice, global_freq, method=method)

            wc = WordCloud(
                width=400, height=400, background_color="white",
                max_words=max_words, stopwords=set(w.lower() for w in (stopwords_nltk + stopwords))
            ).generate_from_frequencies(keyness)

            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(label, fontsize=12)
        else:
            ax.text(0.5, 0.5, f"Aucune donnée\n{label}",
                    ha="center", va="center", fontsize=10, color="gray")
            continue

    # 清理多余空白子图
    for j in range(len(time_slices), n_rows * n_cols):
        row, col = divmod(j, n_cols)
        axes[row, col].axis("off")
    

    #--------------标题----------------------------
    
    if group_by=="Global":
        # --- 添加全局标题 ---
        if isinstance(time_slices[0][0], pd.Timestamp):
            start_label = time_slices[0][0].strftime("%Y-%m")
            end_label = time_slices[-1][1].strftime("%Y-%m")
        else:
            start_label = str(time_slices[0][0])
            end_label = str(time_slices[-1][1])

        fig.suptitle(f"Évolution du nuage de mots ({start_label} ~ {end_label})", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])

    # elif group_by=="Axe" and col_val!=None :
    elif col_val!=None:
        if group_by=="axe":
            axe_map = {
                    "1": "Performances et responsabilités",
                    "2": "Société de services et services à la société",
                    "3": "Innovations, transformations et résistances organisationnelles et sociétales",
                    "4": "Ouvrages pédagogiques",
                    "nan":'nan'
                }
            title_raw=f"{group_by} {col_val}-{axe_map.get(col_val,'?')}"            
            title = wrap_text(title_raw, max_len=50, html=False)
            fig.suptitle(title, fontsize=16)
            plt.tight_layout(rect=[0, 0, 1, 0.96])

        # elif group_by=="Cl. FNEGE":
        #     fig.suptitle(f"{group_by} {col_val}", fontsize=16)
        #     plt.tight_layout(rect=[0, 0, 1, 0.96])

    return fig













