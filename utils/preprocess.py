import pandas as pd
import numpy as np
import json
import matplotlib

import textwrap
import simplemma
import re    
import math
from collections import defaultdict


#my utils:
from utils.upload import load_external_json

def safe_count(df, col, split=False, unique=True):
    if col not in df.columns:
        return None
    series = df[col].dropna()
    if split:
        series = series.str.split(";").explode()
    return series.nunique() if unique else len(series)


def wrap_text(text, max_len=30, html=True):
    """
    在 空格 处换行，而不会拆开单词；

    把太长的文字（超过 max_len）自动插入 <br>；

    返回一个 HTML 字符串，适合用于 Streamlit 或 Plotly 的可视化标签。

    可选使用\n（适用于str）或者 <br>（适用于网页）   
    默认是在网页中显示   
    replace_whitespace=True（默认）
        会把文本中所有的空白字符（\n, \t, \r, 等）都替换成普通的 " "（空格）。
        这样可以避免出现“奇怪的换行”或“制表符错位”等问题。

    replace_whitespace=False
        则会保留原文中的这些空白字符，不会替换。
        例如：原来有换行符 \n，它就会被保留下来


    """
    lines = textwrap.wrap(text, width=max_len, break_long_words=False)
    return ("<br>" if html else "\n").join(lines)


# def explode_by_col(df, col):
#     """"
#     空值填nan，
#     多值按照，/；分割成list
#     =>在某一col上explode；
#     检查notna
#     """
#     df = df.copy()
#     df[col] = df[col].fillna('nan').astype(str).str.split("[,;]") # axe中有nan所以type:objet，先变成str
#     df = df.explode(col)
#     df[col] = df[col].str.strip()
#     return df[df[col].notna() & (df[col] != "")]




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



def assign_time_unit(df, date_col="submittedDate_s"):
    """
    给 DataFrame 增加一个 'time_unit' 列，根据整个 df 的时间范围自动选择粒度：
    - <=12个月：按月
    - 12~36个月：按季度
    - >36个月：按年

    参数：
        df : pd.DataFrame
        date_col : str，日期列名，默认 "submittedDate_s"

    返回：
        df : 增加 'time_unit' 列的 DataFrame
        period_m : 总月份数
        x_label_format : 可用于 matplotlib 的时间格式化字符串
    """
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        earliest_date = df[date_col].min()
        latest_date = df[date_col].max()

        if pd.notnull(earliest_date) and pd.notnull(latest_date):
            period_m = (latest_date.year - earliest_date.year) * 12 + \
                       (latest_date.month - earliest_date.month) + 1

            # 自动选择时间粒度
            if period_m <= 12:
                df['time_unit'] = df[date_col].dt.to_period('M')
                x_label_format = "%Y-%m"
            elif period_m <= 36:
                df['time_unit'] = df[date_col].dt.to_period('Q')
                x_label_format = "Q%q-%Y"
            else:
                df['time_unit'] = df[date_col].dt.to_period('Y')
                x_label_format = "%Y"
        else:
            period_m = 0
            df['time_unit'] = pd.NaT
            x_label_format = "%Y-%m"
    else:
        period_m = 0
        df['time_unit'] = pd.NaT
        x_label_format = "%Y-%m"

    return df



def preprocess_text(text, user_stopwords=None, lang='fr'):
    stopwords_nltk=load_external_json("json_data/stopwords_nltk.json")
    #=>list

    # stopwords==user_stopwords 
    if user_stopwords==None:
        user_stopwords=[]


    # --- 🔧关键修复：确保拼接时都是 list ---
    stopwords = list(stopwords_nltk) + list(user_stopwords)
    stopwords = set(w.lower() for w in stopwords)

    # 转小写+去重
    # stopwords = set(w.lower() for w in (stopwords_nltk + user_stopwords))

    # 处理 None / NaN
    if text is None or str(text).lower().strip() in ['nan', 'none'," "]:
        return " "
    
    # list -> str
    if isinstance(text, list):
        text = " ".join(map(str, text))
        # st.warning("Texte sous forme de liste!!!") 
    elif not isinstance(text, str):  # 如果是其他类型，转成字符串
        text = str(text)

    text = str(text).lower().strip()
    
    # 去标点 &非字母 & 多余空格
    text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    
    # lemmatize + 去停用词
    clean_tokens = [simplemma.lemmatize(word, lang=lang) for word in text.split()]
    clean_text = " ".join([w for w in clean_tokens if w.isalpha() and w not in stopwords])
    
    return clean_text



def collect_clean_texts_by_col(df_input, options, stopwords, exclude_nan=False, col="Global", lang_col="language_s"):
    """
    收集文本，支持：
    - col=None: 全局（只分语言）
    - col="axe" 或 "cl.fnege": 先分分类，再分语言
    
    返回 dict 格式:
    {
      "1": {"en": "clean text", "fr": "..."},
      "2": {"en": "...", "fr": "..."}
    }
    """
    df=df_input.copy()

    dict_texts = defaultdict(lambda: defaultdict(str))
    if exclude_nan==True and col!='Global':#如需dropna且是按照axe/CL分类生成wc
        # exclude_nan==t-> dropna()，若global，不需要筛选
        df=df.dropna(subset=[col])
        df=df[df[col]!="nan"]#有时候NAN可能已经填充了！
        
    if col and col in df.columns:#和exploded都行
        # 处理多分类列:若全部dropna，填充也不会有“nan”
        df["_col_list"] = df[col].fillna("nan").apply(
            lambda x: [v.strip() for v in str(x).split(";") if v.strip()]
        )        
        #==explode
        
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

    return {k : dict_texts[k] for k in sorted(dict_texts.keys())}#按照顺序重新排序

