import streamlit as st
import calendar
import pandas as pd
import re
from datetime import datetime
import calendar

#my utils :
from utils.upload import missing_data_warning


def fetch_hal_articles(start_year=None, start_month=None, end_year=None, end_month=None,
                       doc_types=None, domains=None,keywords=None, languages=None,labs=None,
                       collcode=None, collname=None, authors=None, text=None,
                       fields:list=None, rows=100, max_records=5000):
    """
    grammaire basique de requête:

    q=query, q=col:contenu
    q=*:*    # consulter tout
    q=labStructName_s:"Institut de Recherche en Gestion" # une seule condition
    q=docType_s:"ART" OR docType_s:"COMM" #multi condition
    rows=k #k résultats

    #   opérateur:
    & == AND
    | == OR

    # consulter toutes les conditions (facettes) possibles:
    rows=0
    """
        
    """
    fetch articles via HAL API:
    start_year, end_year: int
    start_month, end_month: int or None
    labs: list of str
    doc_types: list of str
    fields: list of str
    rows: int


    web HAL :
    https://hal.science/search/index/?q=*&rows=30&labStructName_s=Institut+de+Recherche+en+Gestion

    
    exemple d'url (11/10/2025):
    http://api.archives-ouvertes.fr/search/?q=*:*&wt=xml&fq=submittedDate_tdate:[NOW-1MONTHS/DAY TO NOW/HOUR]&fq=submitType_s:(-notice)&fl=label_s,submittedDate_tdate,submitType_s&sort=submittedDate_tdate asc
    
    https://api.archives-ouvertes.fr/search/?q=*:*&wt=xml&fq=submittedDate_tdate:[2025-11-01T00:00:00Z-1YEARS/DAY%20TO%20NOW/DAY]&fl=label_s,submittedDate_tdate,submitType_s&sort=submittedDate_tdate%20asc
    
    """


    import requests
    import pandas as pd
    import calendar
    import urllib.parse

    
    BASE_URL = "https://api.archives-ouvertes.fr/search/"
    
    # 默认输出列：
    if fields is None:
        fields = ['halId_s', "title_s", "authFullName_s", "publicationDate_s",
                  "labStructName_s", "keyword_s", "abstract_s", "urlFulltextEsr_s"]
    

    # # 构建过滤条件[无法继续使用]
    # fq = []
    # if doc_types:
    #     fq.append("(" + " OR ".join([f'docType_s:"{t}"' for t in doc_types]) + ")") 
    #     #formule：(docType_s:"ART" OR docType_s:"COMM")
    # if domains:
    #     fq.append("(" + " OR ".join([f'domain_s:"{t}"' for t in domains]) + ")") 

    # if keywords:
    #     fq.append("(" + " OR ".join([f'keyword_s:"{t}"' for t in keywords]) + ")") 

    # if languages:
    #     fq.append("(" + " OR ".join([f'language_s:"{t}"' for t in languages]) + ")") 

    # if labs:
    #     fq.append("(" + " OR ".join([f'labStructName_s:"{lab}"' for lab in labs]) + ")")

    # 日期1:
    # #HAL（以及 Solr/Elasticsearch）检索时，如果字段是字符串 (_s 后缀通常是 string 类型)，直接用 [start TO end] 比较的是字典序，而不是时间

    # # if start_year is not None and start_month is not None:
    # #     start_date = f"{start_year}-{start_month:02d}"

    # #     # start_date = f"{start_year}-{start_month:02d}-01 00:00:00"
    # #     # start_date = f"{start_year}-{start_month:02d}-01T00:00:00Z"
    # #     # 你生成的是 ISO 8601 带 T 和 Z，而你存储的 modifiedDate_s 是空格分隔且没有 Z
    # # else:
    # #     start_date = None
    
    # # # end_day = calendar.monthrange(end_year, end_month)[1]#按月份决定最后一天是29/30/31
    # # end_date = f"{end_year}-{end_month:02d}"

    # # # f"{end_year}-{end_month:02d}-{end_day:02d} 23:59:59"
    # # # end_date = f"{end_year}-{end_month:02d}-{end_day:02d}T23:59:59Z"
    
    # # if start_date:
    # #     fq.append(f'submittedDate_s:[{start_date} TO {end_date}]')#publicationDate_s,modifiedDate_s
    # #     # print(f"PERIODE : {start_date} TO {end_date}")
    # # else:
    # #     fq.append(f'submittedDate_s:[* TO {end_date}]')  # * 表示不限下限


    # -------------构建搜索条件v2 11/10/25--------------------
    fq = []
    if doc_types:
        input = [f'"{t}"' for t in doc_types]
        fq.append(f'docType_s:({" OR ".join(input)})')

    if labs:
        input = [f'"{t}"' for t in labs]
        fq.append(f'labStructName_s:({" OR ".join(input)})')
    
    if collcode:
        input = [f'"{t}"' for t in labs]
        fq.append(f'collCode_s:({" OR ".join(input)})')
    
    if collname:
        input = [f'"{t}"' for t in labs]
        fq.append(f'collName_s:({" OR ".join(input)})')

    if domains:
        input = [f'"{t}"' for t in domains]
        fq.append(f'domain_s:({" OR ".join(input)})')

    if keywords:
        input = [f'"{t}"' for t in keywords]
        fq.append(f'keyword_s:({" OR ".join(input)})')

    if languages:
        input = [f'"{t}"' for t in languages]
        fq.append(f'language_s:({" OR ".join(input)})')
    if authors:
        input = [f'"{t}"' for t in authors]
        fq.append(f'authFullName_s:({" OR ".join(input)})')



    # ----------------#⭐ 日期范围：submittedDate_s不能继续使用！--------------------
    # #如果有起始年月则加入，如果None，不指定
    # if start_year and start_month:
    #     start_date = f"{start_year}-{start_month:02d}-01T00:00:00Z"
    # else:
    #     start_date = None

    # #如果有起结束月则加入，如果无，
    # if end_year and end_month:
    #     end_day = calendar.monthrange(end_year, end_month)[1]  # 当月最后一天
    #     end_date = f"{end_year:04d}-{end_month:02d}-{end_day:02d}T23:59:59Z"
    # else:
    #     raise ValueError("Préciser l'année de fin ou/et le mois de fin!")
    
    # ##按日期范围查询：
    # if start_date:
    #     fq.append(f'submittedDate_tdate:[{start_date} TO {end_date}]')#publicationDate_s,modifiedDate_s
    #     # print(f"PERIODE : {start_date} TO {end_date}")
    # else:
    #     fq.append(f'submittedDate_tdate:[* TO {end_date}]')  # * 表示不限下限

    #-------------------------------------------------------------------------------
    

    def build_submitted_date_filter(fq, start_year=None, start_month=None,
                                    end_year=None, end_month=None):

        # --- 强化逻辑：如果 start_year 或 start_month 为 "*"，则都视为无限制 ---
        if start_year == "*" or start_month == "*":
            start_year = start_month = "*"

        # --- 强化逻辑：如果 end_year 或 end_month 为 aujourd'hui，则都视为今天 ---
        if end_year == "aujourd'hui" or end_month == "aujourd'hui":
            end_year = end_month = "aujourd'hui"

        # --- 日期合法性检查 ---
        if isinstance(start_year, int) and isinstance(start_month, int) and \
        isinstance(end_year, int) and isinstance(end_month, int):

            # 比较年月元组（保证稳定）
            if (end_year, end_month) < (start_year, start_month):
                st.error("⚠️ Période invalide : la fin est antérieure au début!")
                return []  # 返回空过滤，避免继续运行
            
        # fq = []#不能清空啊！！！！！！

        # --- 构建开始日期 ---
        if isinstance(start_year, int) and isinstance(start_month, int):
            start_date = f"{start_year}-{start_month:02d}-01T00:00:00Z"
        else:
            start_date = "*"

        # --- 构建结束日期 ---
        if isinstance(end_year, int) and isinstance(end_month, int):
            last_day = calendar.monthrange(end_year, end_month)[1]
            end_date = f"{end_year}-{end_month:02d}-{last_day:02d}T23:59:59Z"
        elif end_year == "aujourd'hui":
            today = datetime.utcnow()
            end_date = today.strftime("%Y-%m-%dT23:59:59Z")
        else:
            # 理论上不会进入这里，但作为安全兜底
            today = datetime.utcnow()
            end_date = today.strftime("%Y-%m-%dT23:59:59Z")

        # --- 添加 fq 参数（提交日期区间） ---
        st.write(f"[INFO] Chercher selon submittedDate_s: {start_date} ~ {end_date}")
        fq.append(f"submittedDate_tdate:[{start_date} TO {end_date}]")

        return fq

    fq=build_submitted_date_filter(fq, start_year, start_month,end_year, end_month)




    # 8. 自由文本（全文搜索）
    q = " AND ".join(text) if text else "*:*"

    #==================URL check==================
    # response = requests.get(url, params=params).json()

    # if "response" in response:
    #     docs = response["response"].get("docs", [])
    #     if docs:
    #         print(f"查询到 {len(docs)} 条结果")
    #         for d in docs:
    #             print(d)
    #     else:
    #         print("没有查询到结果")
    # else:
    #     print("查询返回异常")


    # CHECK: 
    #输入筛选条件
    # params = {
    #     "q": q,
    #     "fq": fq,
    #     "fl": ",".join(fields),
    #     "rows": rows,
    #     "wt": "json",
    #     "sort": "submittedDate_t"
    # }   

    # # 构建 URL 用于打印检查
    # query_string = urllib.parse.urlencode(params, doseq=True)
    # full_url = BASE_URL + "?" + query_string
    # print(f'QUERY URL : {full_url} \n')



    # ========= 请求循环 =========
    all_docs = []#储存所有结果

    start = 0#从第几条开始抓取，一次抓取rows条，忽略抓取过的
    total_found = None

    while True:
        #[无法使用]
        # params = {
        #     "q": q,
        #     "fq": fq,
        #     "fl": ",".join(fields),
        #     "rows":  rows,
        #     "start": start,
        #     "wt": "json",
        #     "sort":"submittedDate_t"
        # }

        # # 固定条件测试：
        # params = [
        #     ("q", "*:*"),
        #     ("fq", 'docType_s:("ART" OR "OUV")'),
        #     ("fl", ','.join(fields)),
        #     ("rows", rows),
        #     ("wt", "json"), 
        # ]



        # 10/2025 updates:fq=单独条件
        params = [
        ("q", q),
        ("fl", ",".join(fields)),
        ("rows", rows),
        ("wt", "json"),
        ("start", start),
        ("sort", "submittedDate_tdate desc")#"submittedDate_tdate desc"
    ]
        for f in fq:
            params.append(("fq", f))
        

        
        # 构建 URL 用于打印检查
        query_string = urllib.parse.urlencode(params, doseq=True)
        full_url = BASE_URL + "?" + query_string
        # st.info(f'QUERY URL : {full_url} \n')
        
        resp = requests.get(BASE_URL, params=params, timeout=15)
        # print(resp.json())

        # resp = requests.get(BASE_URL, params=params, timeout=15)
        # st.info(f"[DEBUG] Response status: {resp.status_code} | start={start}")
        

        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            st.error(f"HAL API error: {data['error']}")
            raise ValueError(f"HAL API error: {data['error']}")

        if "response" not in data:
            print("[ERROR] JSON 中没有 'response' 字段！返回内容预览：", data)
            raise KeyError("'response'")
        

        if total_found is None:
            total_found = data["response"]["numFound"]
            # print(f"[INFO] 找到 {total_found} 篇文章，开始抓取...")

        docs = data["response"]["docs"]
        if not docs:
            break

        all_docs.extend(docs)

        start += rows
        if start >= total_found or start >= max_records:
            break
    
    # ========= 整理到 DataFrame =========
    info = []
    for doc in all_docs:
        doc_info = {}
        for col in fields:
            value = doc.get(col, None)
            if isinstance(value, list):
                value = "; ".join(value)
            doc_info[col] = value
        info.append(doc_info)

    # if not data.get('response', {}).get('docs'):
    df = pd.DataFrame(info)
    df=df.drop_duplicates(subset='halId_s')

    if 'submittedDate_s' in df.columns:
        df['submittedDate_s'] = pd.to_datetime(df['submittedDate_s'], errors='coerce')
        df = df.sort_values(by='submittedDate_s', ascending=False)
        
    return df
















#=======================================DOMAINE=======================================================#

def map_domains(codes_str:str=None, map:dict=None):
    """
    搜索结果是代码，对代码进行映射和清洗
    """
    if not isinstance(codes_str,str): 
        return None

    codes = codes_str.split(";")
    mapped = []

    for code in codes:
        code_clean = re.sub(r"^\d+\.", "", code.strip())
        mapped.append(map.get(code_clean, code_clean))
    
    return "; ".join(mapped)








#========================================AXE===========================================================#
def extract_irg_axes(text):
    """
    把 classification_s 字段中的值:
        IRG_AXE1
        IRG_axe1
        IRG_AXE 3
        IRG_AXE1IRG_AXE3
        IRG_AXE2 – Sociétés de services et services à la société (A society of services and services to society)
        Axe_1            

    re.findall(pattern, text)
    \s* 允许space, *表示0或多个！

    (\d+):
        \d是数字，+表示模式重复多次，()为捕获组单位，只取出()内的内容

    """
    if pd.isna(text):
        return None
    text=text.strip().lower()
        
    # 找出所有 irg_axe后面的数字
    matches = re.findall(r"axe\s*(\d+)", text)
    if matches:
        # 用分号拼接
        return "; ".join(matches)
    return None


def clean_axe_from_classification(df,axe_name='axe'):
    """   
    整理成字符串数字，列名改为axe
    """
    df["classification_s"] = df["classification_s"].apply(extract_irg_axes)
    df=df.rename(columns={"classification_s":axe_name})
    return df








#===========================================FNEGE===========================================================#
from typing import Dict, Any #Python 类型注解模块 typing 里的类型提示
from rapidfuzz import process
import unicodedata
import re
from typing import Dict, Any


# def clean_ponc(s):  
#     s=s.strip().lower()
#     clean_s=re.sub(r"[^\w\s]","", s)
#     # \w\s → 匹配所有字母、数字、下划线、空白的字符（即标点符号）。
#     # ^ 表示取反
#     return clean_s


# --------------------------
# 字符串归一化
# --------------------------
def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", "", text)  # 去掉标点

    return text


def normalize_journal(name: str) -> str:
    """清洗 journal 名称，方便 fuzzy 匹配"""
    if not name:
        return ""
    name = str(name).lower().strip()
    name = re.sub(r"[^\w\s]", "", name)  # 去掉标点
    name = re.sub(r"\s+", " ", name)     # 合并多余空格
    return name



# --------------------------
# 模糊匹配期刊名
# --------------------------
def fuzzy_lookup(journal_name: str, mapping: dict, cutoff: int = 70) -> str:
    """
    清洗检索结果csv中的journal_name("journalTitle_s")
    返回最匹配的期刊排名，如果匹配不到则返回 None
    """
    if not journal_name or not mapping:
        return None

    normalized_mapping_keys = {normalize(k): k for k in mapping.keys()}
    norm_name = normalize(journal_name)

    # 找最接近的 key
    best_match = process.extractOne(norm_name, list(normalized_mapping_keys.keys()))
    if best_match and best_match[1] >= cutoff:
        original_key = normalized_mapping_keys[best_match[0]]
        return mapping[original_key]
    return None



# def nearest_fnege_year(pub_year_str):
#     if pd.isna(pub_year_str):
#         return None
#     # 找小于等于 pub_year 的最近年份
    
#     fnege_years = [2011, 2013, 2016, 2019, 2022]
#     pub_year=int(pub_year_str[:4])
#     candidates = [y for y in fnege_years if y <= pub_year]
#     if not candidates:
#         return fnege_years[0]  # 如果年份早于最早的 FNEGE，则用最早年份
#     return max(candidates)



def nearest_fnege_year(pub_year_raw):
    FNEGE_YEARS = [2011, 2013, 2016, 2019, 2022]

    # 处理缺失
    if pd.isna(pub_year_raw):
        return None

    # 处理 datetime / Timestamp
    if isinstance(pub_year_raw, (pd.Timestamp, datetime)):
        pub_year = getattr(pub_year_raw, "year", None)
    else:
        s = str(pub_year_raw).strip()
        # 从字符串中提取第一个四位年份
        m = re.search(r'(\d{4})', s)
        if not m:
            return None
        pub_year = int(m.group(1))

    # 找最近且小于等于 pub_year 的 fnege 年份
    candidates = [y for y in FNEGE_YEARS if y <= pub_year]
    return max(candidates) if candidates else FNEGE_YEARS[0]


def add_classement_fnege(
    df: pd.DataFrame,
    fnege_df: pd.DataFrame,
    journal_col: str = "journalTitle_s",
    year_col: str = "publicationDate_s",
    cl_name: str = 'cl_fnege',
    cutoff: int = 80
) -> pd.DataFrame:
    """
    给搜索结果 DataFrame 增加 FNEGE 排名列
    
    - df: 搜索结果 DataFrame
    - fnege_df: 清洗后的 FNEGE 数据，列名如 rang_2011, rang_2013 ...
    - journal_col: 搜索结果中的期刊名称列
    - year_col: 搜索结果中的发表日期列
    - cl_name: 新增列名
    - cutoff: fuzzy 匹配阈值
    """

    # 构建 fuzzy lookup mapping: key = 再次清洗后的 journal, value = 原始整行字典
    fnege_mapping = {normalize_journal(r['journal']): r.to_dict() for _, r in fnege_df.iterrows()}

    #pub_yer:
    df['fnege_year'] = df[year_col].apply(nearest_fnege_year)

    #cl_fnege
    classement_list = []
    for _, row in df.iterrows():
        #不为nan且strip后不为空：
        if pd.notna(row[journal_col] and str(row[journal_col]).strip()):
            fnege_year=row['fnege_year']

            # fuzzy lookup寻找对应的 journal名
            journal_name = row.get(journal_col, "")
            matched_row = fuzzy_lookup(journal_name, fnege_mapping, cutoff=cutoff)

            # 再在这一行上寻找 对应年份的排名
            rang_value = None
            if matched_row and fnege_year:
                rang_col = f"rang_{fnege_year}"
                rang_value = matched_row.get(rang_col, None)
        else:
            # print('no journal title')
            rang_value=None

        classement_list.append(rang_value)

    # 插入新列
    idx = df.columns.get_loc(journal_col)
    df.insert(loc=idx + 1, column=cl_name, value=classement_list)

    return df



# def add_classement_fnege(
#     df: pd.DataFrame,
#     fnege_df: pd.DataFrame,
#     journal_col: str = "journalTitle_s",
#     year_col: str = "publicationDate_s",
#     cl_name: str = 'cl_fnege',
#     cutoff: int = 85
#     ) -> pd.DataFrame:

#     # 先把 fnege_df 的 journal 做 normalize，用于 fuzzy 匹配
#     fnege_mapping = {}
#     for _, row in fnege_df.iterrows():
#         fnege_mapping[row['journal']] = row.to_dict()  # key: 原始 journal 名, value: 整行字典
    
#     classement_list = []
#     for _, row in df.iterrows():
#         pub_year = str(row[year_col])[:4]  # 取年份
#         journal_name = row[journal_col]
        
#         # fuzzy lookup 找最接近的 fnege journal
#         matched_row = fuzzy_lookup(journal_name, fnege_mapping, cutoff=cutoff)
        
#         if matched_row:
#             # matched_row 是 fnege_mapping 中的字典
#             # 动态取年份对应的排名
#             rang_col = f"rang_{pub_year}"
#             rang_value = matched_row.get(rang_col, None)
#             classement_list.append(rang_value)
#         else:
#             classement_list.append(None)
    
#     # 插入新列到 journal_col 后
#     idx = df.columns.get_loc(journal_col)
#     df.insert(loc=idx+1, column=cl_name, value=classement_list)
    
#     return df


# def add_classement_fnege(
#     df: pd.DataFrame,
#     journal_col: str = "journalTitle_s",
#     fnege_df: Dict[str, Any] = None, ## 表示 mapping 是一个字典，key 是字符串，value 可以是任意类型  
#     cl_name: str = 'cl_fnege',
#     cutoff: int = 85
# ) -> pd.DataFrame:
    
#     col_cl = df[journal_col].apply(lambda x: fuzzy_lookup(x, fnege_df, cutoff=cutoff))
    
#     # 找到 journalTitle_s 的列索引
#     idx = df.columns.get_loc(journal_col)

#     # 插入列到 journalTitle_s 后面
#     df.insert(loc=idx+1, column=cl_name, value=col_cl)
#     return df





#===========================================PRIMARYSTRUCTURE===========================================================#

import urllib.parse
import requests
import time
import numpy as np
from tqdm import tqdm
import os
import json

# def check_primarystructure_map()
def save_as_json(data, file_path="../external_data/author_primarystructure_s_map.json"):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open (file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # st.markdown(f'[SAVE] Les données sauvegardées / mises à jour :\n{file_path}!')
    # &nbsp; == a no breaking space
    return 



def read_json(file_path='../external_data/author_primarystructure_s_map.json'):
    with open (file_path, 'r', encoding="utf-8") as f:
        data=json.load(f)
    return data



def get_author_primarystructure(names: list, author_primarystructure_s_map:dict=None):
    """
    查询作者主要所属机构（Primary Structure），返回一个 dict 映射。
    使用 tqdm 显示查询进度。
    可能有作者在HAL没有HalId，所以通过fullname查询更加保险？

    """
    if author_primarystructure_s_map == None:
        author_primarystructure_s_map={}

    BASE_URL = "https://api.archives-ouvertes.fr/search/"
    # for name in tqdm(names, desc="🔍 chercher la structure primaire de l'auteurs:", ncols=100):
    for i, name in enumerate (names):#如果改变value，应该删除json，不然查询到已经存在的名字，不会再重新搜索!
        if name not in author_primarystructure_s_map.keys():
            try:
                params = [
                    ("fq", f'authFullName_s:"{name}"'),
                    ("fl", "authIdHasPrimaryStructure_fs"),
                    ("rows", 1),
                    ("wt", "json")
                ]
                # #检查生成的url：
                # query_string = urllib.parse.urlencode(params, doseq=True)
                # full_url = BASE_URL + "?" + query_string
                # # print(f'QUERY URL : {full_url} \n')

                resp = requests.get(BASE_URL, params=params, timeout=15)
                resp.raise_for_status()  # 检查HTTP状态码
                data = resp.json()
                # print(data)
                
                
                #提取：
                #ex.{'response': {'numFound': 79, 'start': 0, 'maxScore': 1.0, 'numFoundExact': True, 'docs': [{'authIdHasPrimaryStructure_fs': ['1271130-1099011_FacetSep_Ziad Malas_JoinSep_1151738_FacetSep_Laboratoire de Gestion et des Transitions Organisationnelles', '1271130-1099011_FacetSep_Ziad Malas_JoinSep_301366_FacetSep_Institut Universitaire de Technologie - Paul Sabatier', "12474-177028_FacetSep_Samuel Guillemot_JoinSep_489734_FacetSep_Laboratoire d'Economie et de Gestion de l'Ouest", '21015-5244_FacetSep_Andréa Gourmelen_JoinSep_117385_FacetSep_Montpellier Research in Management']}]}}

                # Identifiant interne + _FacetSep_ + Nom complet + _JoinSep_ + Identifiant HAL de structure primaire + _FacetSep_ + Nom de la structure primaire
                #ex. ['3657528-1564101_FacetSep_Adel Horrig_JoinSep_1004418_FacetSep_Institut de Recherche en Gestion']
                
                docs = data.get("response", {}).get("docs", [])
                if not docs:
                    continue

                records = docs[0]["authIdHasPrimaryStructure_fs"]
                # print(records)# liste de structure >=1
               
                target_records = [r for r in records if f"_FacetSep_{name}_" in r][0]#理论上<=0

                if target_records:
                    parts = target_records.split("_")
                    structure_id= parts[-3] if parts else None #1004418 ou 57129 
                    structure_s = parts[-1] if parts else None
                    id_structure=str(structure_id)+"_"+str(structure_s)
                # else :
                # 会转到except中

                #记录：
                author_primarystructure_s_map[name] = id_structure


            except Exception as e:
                # st.warning (f"ERROR in get_author_primarystructure: \n {e}")
                author_primarystructure_s_map[name] = "no primary structure found"
                continue


    return author_primarystructure_s_map



def update_author_primarystructure_s(names:list, file_path='../external_data/author_primarystructure_s_map.json'):
    #读取已存在的author_primarystructure_s_map，如果authFullName_s不存在则搜索，然后更新至map
    try :
        if os.path.exists(file_path):
            author_primarystructure_s_map=read_json(file_path)
        else :
            author_primarystructure_s_map={}
        updated_author_primarystructure_s_map=get_author_primarystructure(names, author_primarystructure_s_map)
        save_as_json(updated_author_primarystructure_s_map, file_path)
    except Exception as e:
        st.warning (f"ERROR in update_author_primarystructure_s: \n {e}")
    
    return updated_author_primarystructure_s_map



def add_primarystructure(df, author_primarystructure_s_map):
    #读取map中author对应的id_structure str
    # 把author_primarystructure添加到lab后的一列，命名为author_primarystructure_s

    # primarystructures=df['authFullName_s'].apply(lambda x: ";".join([author_primarystructure_s_map.get(a, np.nan) 
    #                                                     for a in x.split(";")]) if isinstance(x, str) else np.nan)
    primarystructures=df['authFullName_s'].apply(lambda x: ";".join([str(author_primarystructure_s_map.get(a.strip(), "mapping_error"))
                                                    for a in x.split(";") if a.strip()]
                                                ) if isinstance(x, str) else "fullname_not_strs")
        
    idx = df.columns.get_loc('labStructName_s')
    df.insert(loc=idx+1, column='author_primarystructure_s', value=primarystructures)
    return df



##集合处理：
def process_df(df, DOMAIN_MAP, FNEGE_MAP, cutoff):
    """
    todo：增加methodologie！

    """
    # -----------处理 domain----------------
    if "domain_s" in df.columns:   
        df["domain_s"] = df["domain_s"].apply(lambda x : map_domains(x, map=DOMAIN_MAP))
    st.write(f"✔ Domaines mappés!")

    #----------处理axe----------------------
    if "classification_s" in df.columns:
        df=clean_axe_from_classification(df)
    st.write(f"✔ Axes nettoyés!")
    missing_data_warning(df, col='axe', show_distribution=True)


    #--------- 处理fnege----------------
    # if "journalTitle_s" in df.columns:
    #     df= add_classement_fnege(df, journal_col='journalTitle_s', fnege_df=FNEGE_MAP, cl_name='Cl.FNEGE')
    # st.write(f"✔ Classements FNEGE mappés!")


    if "journalTitle_s" in df.columns and "publicationDate_s" in df.columns :
        # df=add_classement_fnege(
        #     df=df,
        #     fnege_df=FNEGE_MAP,
        #     journal_col= "journalTitle_s",
        #     year_col = "publicationDate_s",
        #     cl_name = 'cl_fnege',
        #     cutoff = 85
        # )
        
        df=add_classement_fnege(
            df,fnege_df=FNEGE_MAP,
            journal_col = "journalTitle_s",
            year_col= "publicationDate_s",
            cl_name = 'cl_fnege',
            cutoff = cutoff
        ) 
        # missing_data_warning(df, col='fnege_year')
        st.write(f"✔ Classements FNEGE de la date de publication mappés!")
        missing_data_warning(df, col="journalTitle_s", show_distribution=False)
        missing_data_warning(df, col='cl_fnege', show_distribution=True)


    #----------处理author_primarystructure-----------
    # st.write(os.getcwd())
    with st.spinner("Chercher la structure primaire de l'auteur selon le nom complet de l'auteur..."):
        author_col='authFullName_s'
        names = set([
            n.strip()
            for _, r in df.iterrows()
            if isinstance(r[author_col], str)
            for n in r[author_col].split(';')
            if n.strip()
        ])
        author_primarystructure_s_map=update_author_primarystructure_s(names, file_path='external_data/author_primarystructure_s_map.json')
            
        df= add_primarystructure(df, author_primarystructure_s_map)#map
        st.write(f"✔ Structures primaires mappées!")
        missing_data_warning(df, col="author_primarystructure_s", show_distribution=False)#check



    return df






#===========================================DATE DEBUT/FIN DE DEPO？=======================================================#



#===========================================SAVE=======================================================#


def save_file_csv_xlsx(df,start_year, start_month, end_year, end_month):
    import io
    from datetime import datetime   
    if end_year=="aujourd'hui" or end_month=="aujourd'hui":
        now = datetime.now()
        current_year, current_month = now.year, now.month
        end_year, end_month=current_year, current_month

    # df = st.session_state.get(session_key, None)

    if df is not None and not df.empty:
    #  ----------------SAVE TO LOCAL----------------- 
        cols=st.columns(3)
        #---------------file name------------------- 
        with cols[0]:
            today_str = datetime.now().strftime("%Y%m%d")
            default_file_name=f"{today_str}-ProductionScientifiqueIRG-{start_year}{start_month}-{end_year}{end_month}_{len(df)}art"

            # 用户输入框
            #\n format par défaut: today--ProductionScientifiqueIRG-start_date-end_date-nb_articles:
            file_name = st.text_input(
                f"Nom du fichier :",  # 提示文字
                value=default_file_name,            # 默认值
            )

        #---------------as CSV------------------- 
        with cols[1]:
            csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="Télécharger CSV",
                data=csv_data,
                file_name = file_name+".csv",
                mime="text/csv"
            )
            
        #---------------as XLSX------------------- 
        with cols[2]:
            # XLSX → 需要用 io.BytesIO() 来缓存二进制数据，再传给 download_button。
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Articles")
            xlsx_data = xlsx_buffer.getvalue()

            st.download_button(
                label="Télécharger XLSX",
                data=xlsx_data,
                file_name=file_name+".xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 这是 XLSX 文件的 MIME 类型，告诉浏览器这是一个 Excel 文件，否则st button可能无法识别文件类型 
    else : 
        st.warning(f"df.empty!")
    return




def save_file_csv_xlsx_by_filename(df, filename):
    import io
    from datetime import datetime   
    import streamlit as st
    
    if df is not None and not df.empty:
    #  ----------------SAVE TO LOCAL----------------- 
        cols=st.columns(4)
        #---------------file name------------------- 
        with cols[0]:
            file_name = st.text_input(
                f"Nom du fichier :",  # 提示文字
                value=filename,            # 默认值
            )
        #---------------as CSV------------------- 
        with cols[2]:
            csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="Télécharger CSV",
                data=csv_data,
                file_name = file_name+".csv",
                mime="text/csv"
            )

        #---------------as XLSX------------------- 
        with cols[3]:
            # XLSX → 需要用 io.BytesIO() 来缓存二进制数据，再传给 download_button。
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Articles")
            xlsx_data = xlsx_buffer.getvalue()

            st.download_button(
                label="Télécharger XLSX",
                data=xlsx_data,
                file_name=file_name+".xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 这是 XLSX 文件的 MIME 类型，告诉浏览器这是一个 Excel 文件，否则st button可能无法识别文件类型 
    else : 
        st.warning(f"df.empty!")
    return

