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
from collections import defaultdict

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
        # st.info(f"⚠️ Les {WC_MAP.get(col,'...')} sont manquants dans {df[col].isna().sum()}"
        #         f" ({df[col].isna().sum()*100/len(df):.2f}%) articles!")
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
        st.warning("Texte sous forme de liste!!!")
    elif not isinstance(text, str):  # 如果是其他类型，转成字符串
        text = str(text)


    # 去除标点和非字母+lower()
    text = text.lower().strip()
    text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)

    # 去除多余的空格：
    text = re.sub(r"\s+", " ", text).strip()

    # lemmatisation + enlever les stopwords
    clean_tokens=[simplemma.lemmatize(word, lang=lang) for word in text.split()]
    clean_text=" ".join([w for w in clean_tokens if w.isalpha() and w not in stopwords])

    return clean_text



def collect_clean_texts_by_col(df, options, stopwords, exclude_nan=False, col="Global", lang_col="language_s"):
    """
    收集文本，支持：
    - col=None: 全局（只分语言）
    - col="axe" 或 "cl.fnege": 先分分类，再分语言
    
    返回 dict 格式:
    {
      "cat1": {"en": "clean text", "fr": "..."},
      "cat2": {"en": "...", "fr": "..."}
    }
    """
    dict_texts = defaultdict(lambda: defaultdict(str))
    if exclude_nan and col!='Global':#如需dropna且是按照axe/CL分类生成wc
        # exclude_nan==t-> dropna()，若global，不需要筛选

        df=df.dropna(subset=[col])
        df=df[df[col]!="nan"]#有时候可能已经填充了！
        st.write(f'Après dropnan : {len(df)} lignes !')

    if col and col in df.columns:#和exploded都行
        # 处理多分类列:若全部dropna，填充也不会有“nan”
        df["_col_list"] = df[col].fillna("nan").apply(
            lambda x: [v.strip() for v in str(x).split(";") if v.strip()]
        )        
    elif col=="Global":
        # 全局只有一个虚拟类别
        df["_col_list"] = [["Global"]] * len(df)

    # 遍历每个 option 列
    for option_col in options:
        if option_col not in df.columns:
            continue
        for _, row in df.iterrows():
            lang = str(row.get(lang_col, "fr")).lower()  #没有则默认法语
            text = str(row[option_col])#是否忽略无文本的值？
            text = preprocess_text(text, stopwords, lang=lang)
            
            for cat in row["_col_list"]:
                dict_texts[cat][lang] += " " + text

    df.drop(columns=["_col_list"], inplace=True, errors="ignore")
    
    return dict(dict_texts)


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



def generate_wc_param(df, options, group_by, wc_par_lang, exclude_nan, max_words, stopwords):
    #1. collect:
    text_groups=collect_clean_texts_by_col(df, options, stopwords, exclude_nan, col=group_by, lang_col="language_s")
    # text_groups={
    #   "cat1": {"en": "clean text", "fr": "..."},
    #   "cat2": {"en": "...", "fr": "..."}
    # }

    #2.a title
    COL_MAP = {
        "Global": "global",
        "Axe": "par axe",
        "Cl. FNEGE": "par classe FNEGE"
    }    
    group_by_readable=COL_MAP.get(group_by, group_by)
    # 2.b date
    if "submittedDate_s" in df.columns:
        df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
        latest_date = df["submittedDate_s"].max()
        latest_y = latest_date.strftime("%Y") if pd.notnull(latest_date) else "Aucune date valide"

        earliest_date=df["submittedDate_s"].min()
        earliest_y = earliest_date.strftime("%Y") if pd.notnull(latest_date) else "Aucune date valide"
        period_y=f"{earliest_y}~{latest_y}"#图标题


    # wc
    if not wc_par_lang:  # 不分语言 → 合并 EN + FR
        suptitle=f"Nuage de mots {group_by_readable} entre {period_y}"
        st.markdown(
            f"<h3 style='text-align: center;'> {suptitle} </h3>",
            unsafe_allow_html=True
        )

        for cat, langs in text_groups.items(): 
            combined_text = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
            
            if group_by=="Global":
                title=" "
            else:
                title=f"{group_by} {cat}"

            if combined_text:
                fig = generate_wc(
                    langs.get("en", "") + " " + langs.get("fr", ""),  # lang 随便传一个
                    max_words,
                    stopwords,
                    title=title
                )
            # fig.tight_layout(rect=[0, 0, 1, 0.95])  # 顶部留 5% 给 suptitle
            # fig.suptitle(suptitle, fontsize=10, ha="center")
            st.pyplot(fig)


    else:
        # 分语言 → EN/FR 左右列显示，每个类别单独一行
        suptitle=f"Nuage de mots {group_by_readable} par langue entre {period_y}"
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
                        st.pyplot(fig)

                    else :
                        st.warning(f"texte invalie dans la catégorie {cat}-{lang}!")
    return 






#==========================================================================================#
#==========================================================================================#
#==========================================================================================#

def create_time_slices(df, granularity):
    """
    根据颗粒度生成时间切片
    granularity: "month" | "quarter" | "year" | "3year" | "5year"
    """
    df = df.copy()
    df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")

    # 提取年月
    df["year"] = df["submittedDate_s"].dt.year
    df["month"] = df["submittedDate_s"].dt.month

    start_year, end_year = df["year"].min(), df["year"].max()

    if granularity == "Mensuel":
        # 逐月
        months = pd.period_range(df["submittedDate_s"].min().to_period("M"),
                                 df["submittedDate_s"].max().to_period("M"), freq="M")
        time_slices = [(p.start_time, p.end_time) for p in months]

    elif granularity == "Trimestriel":
        # 逐季度
        quarters = pd.period_range(df["submittedDate_s"].min().to_period("Q"),
                                   df["submittedDate_s"].max().to_period("Q"), freq="Q")
        time_slices = [(p.start_time, p.end_time) for p in quarters]

    elif granularity == "Annuel":
        step_year = 1
        time_slices = [(y, min(y + step_year - 1, end_year))
                       for y in range(start_year, end_year + 1, step_year)]

    elif granularity == "Tous les 3 ans":
        step_year = 3
        time_slices = [(y, min(y + step_year - 1, end_year))
                       for y in range(start_year, end_year + 1, step_year)]

    elif granularity == "Tous les 5 ans":
        step_year = 5
        time_slices = [(y, min(y + step_year - 1, end_year))
                       for y in range(start_year, end_year + 1, step_year)]

    # else:  # 默认年度
    #     time_slices = [(y, y) for y in range(start_year, end_year + 1)]
    # st.info(f"Granularité {granularity}:{time_slices}")

    
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




def explode_by_col(df, col="Axe"):
    """"
    空值填nan，
    多值按照，/；分割成list
    =>在某一col上explode；
    检查notna

    """
    df = df.copy()
    df[col] = df[col].fillna('nan').astype(str).str.split("[,;]") # axe中有nan所以type:objet，先变成str
    df = df.explode(col)
    df[col] = df[col].str.strip()
    return df[df[col].notna() & (df[col] != "")]



def generate_keyness_wc(df, options, exclude_nan, group_by, time_slices, max_words=100, stopwords=None, method="llr"):
    """
    根据时间片生成 keyness 演变词云+小图
    """
    #
    df = df.copy()
    df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
    df["year"] = df["submittedDate_s"].dt.year #筛选用


    # --- 绘图布局 ---
    
    if group_by=="Global":    
        n_cols = 4 if len(time_slices) >=  4 else len(time_slices) #按季度可以一年为一行
    else:#输入已经筛选过的df!
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
    #     #   "1": {"en": "clean text", "fr": "..."}
    # }

    for cat, langs in text_groups.items(): 
        texts_all = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
    global_freq = pd.Series(texts_all.split()).value_counts()
    

    for idx, t in enumerate(time_slices):#不变
        # 时间切片可为 (start_date, end_date) 或 (start_year, end_year)
        if isinstance(t[0], pd.Timestamp):  # 月/季度模式
            mask = (df["submittedDate_s"] >= t[0]) & (df["submittedDate_s"] <= t[1])
            label = t[0].strftime("%Y-%m")
        else:
            y_start, y_end = t
            mask = (df["year"] >= y_start) & (df["year"] <= y_end)
            label = f"{y_start}-{y_end}" if y_start != y_end else str(y_start)
        
        #串联这个时间片中所有clean_text
        df_slice = df[mask]
        sliced_text_groups= collect_clean_texts_by_col(df_slice, options, stopwords, exclude_nan=exclude_nan, col=group_by, lang_col="language_s")
        # 若是df_by_axe，则只有一个cat
        for cat, langs in sliced_text_groups.items(): 
            text = (langs.get("en", "") + " " + langs.get("fr", "")).strip()

        # 选择当前子图的位置：在cols数固定的情况下，按照idx自动排列到某一行
        row, col = divmod(idx, n_cols)#已知idx即可计算小图的位置
        ax = axes[row, col]
        ax.axis("off")


        if text:
            freq_slice = pd.Series(text.split()).value_counts() # 局部词频
            keyness = compute_keyness(freq_slice, global_freq, method=method)

            wc = WordCloud(
                width=400, height=400, background_color="white",
                max_words=max_words, stopwords=stopwords
            ).generate_from_frequencies(keyness)

            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(label, fontsize=12)
        else:
            ax.text(0.5, 0.5, f"Aucune donnée\n{label}",
                    ha="center", va="center", fontsize=10, color="gray")

    # 清理多余空白子图
    for j in range(len(time_slices), n_rows * n_cols):
        row, col = divmod(j, n_cols)
        axes[row, col].axis("off")
    
    
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

    elif group_by=="Axe" :
        axe_map = {
                "1": "Performances et responsabilités",
                "2": "Société de services et services à la société",
                "3": "Innovations, transformations et résistances organisationnelles et sociétales",
                "4": "Ouvrages pédagogiques",
                "nan":'nan'
            }
            
        fig.suptitle(f"Axe {axe_map.get(text_groups.keys(),"XXX")}", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])

    return fig


# collect设置是否按语言分？更快？




# def generate_keyness_wc(df, options, exclude_nan, group_by, time_slices, max_words=100, stopwords=None, method="llr"):
#     """
#     根据时间片生成 keyness 演变词云+小图
#     """
#     #
#     df = df.copy()
#     df["submittedDate_s"] = pd.to_datetime(df["submittedDate_s"], errors="coerce")
#     df["year"] = df["submittedDate_s"].dt.year #筛选用


#     # --- 绘图布局 ---
#     n_cols = 4 if len(time_slices) >=  4 else len(time_slices) #按季度可以一年为一行
#     n_rows = math.ceil(len(time_slices) / n_cols)# 计算所需行数
#     fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 5))# 按照行数列数计算图的大小
#     axes = np.array(axes).reshape(n_rows, n_cols)  # 保证二维结构


#     # --- 全局词频 ---
#     if group_by=="Global":
#         text_groups = collect_clean_texts_by_col(df, options, stopwords, exclude_nan, col=group_by)    
#         # text_groups={
#         #   "Global": {"en": "clean text", "fr": "..."},
#         # }
#         for cat, langs in text_groups.items(): 
#             texts_all = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
#         global_freq = pd.Series(texts_all.split()).value_counts()
    


   
#     df_exploded = explode_axes(df, "Axe")
#     if group_by=="Axe":
#         # text_groups={
#         #   "1": {"en": "clean text", "fr": "..."},
#         #   "2": {"en": "...", "fr": "..."}
#         # }
#         for axe, langs in text_groups.items(): 
#             texts_axe = (langs.get("en", "") + " " + langs.get("fr", "")).strip()
#             axe_freq = pd.Series(texts_all.split()).value_counts()




#     for idx, t in enumerate(time_slices):#不变
#         # 时间切片可为 (start_date, end_date) 或 (start_year, end_year)
#         if isinstance(t[0], pd.Timestamp):  # 月/季度模式
#             mask = (df["submittedDate_s"] >= t[0]) & (df["submittedDate_s"] <= t[1])
#             label = t[0].strftime("%Y-%m")
#         else:
#             y_start, y_end = t
#             mask = (df["year"] >= y_start) & (df["year"] <= y_end)
#             label = f"{y_start}-{y_end}" if y_start != y_end else str(y_start)
        
#         # 时间段内clean_text
#         df_slice = df[mask]
#         sliced_text_groups = collect_clean_texts_by_col(df_slice, options, stopwords, col="Global")
#         for cat, langs in sliced_text_groups.items(): 
#             text = (langs.get("en", "") + " " + langs.get("fr", "")).strip()

#         # 选择当前子图的位置：在cols数固定的情况下，按照idx自动排列到某一行
#         row, col = divmod(idx, n_cols)#已知idx即可计算小图的位置
#         ax = axes[row, col]
#         ax.axis("off")


#         if text:
#             freq_slice = pd.Series(text.split()).value_counts() # 局部词频
#             keyness = compute_keyness(freq_slice, global_freq, method=method)

#             wc = WordCloud(
#                 width=400, height=400, background_color="white",
#                 max_words=max_words, stopwords=stopwords
#             ).generate_from_frequencies(keyness)

#             ax.imshow(wc, interpolation="bilinear")
#             ax.set_title(label, fontsize=12)
#         else:
#             ax.text(0.5, 0.5, f"Aucune donnée\n{label}",
#                     ha="center", va="center", fontsize=10, color="gray")

#     # 清理多余空白子图
#     for j in range(len(time_slices), n_rows * n_cols):
#         row, col = divmod(j, n_cols)
#         axes[row, col].axis("off")

#     # --- 添加全局标题 ---
#     if isinstance(time_slices[0][0], pd.Timestamp):
#         start_label = time_slices[0][0].strftime("%Y-%m")
#         end_label = time_slices[-1][1].strftime("%Y-%m")
#     else:
#         start_label = str(time_slices[0][0])
#         end_label = str(time_slices[-1][1])

#     fig.suptitle(f"Évolution du nuage de mots ({start_label} ~ {end_label})", fontsize=16)
#     plt.tight_layout(rect=[0, 0, 1, 0.96])



#     return fig


# # collect设置是否按语言分？更快？
