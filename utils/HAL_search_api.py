import streamlit as st
import calendar
import pandas as pd
import re
from datetime import datetime
import calendar

#my utils :
from utils.upload import missing_data_warning


"""
[2026-01-01 TO 2026-01-27]
[2026-01-01 TO NOW]
[* TO NOW]

"""
##===========================================PERIODE=====================================================
from datetime import datetime, timezone, date

utc_today = datetime.now(timezone.utc).date()

def build_period(start_year=None, start_month=None,
                    end_year=None, end_month=None):
        
        """
        根据输入生成合法的起止时间
        如果开始年月任一为*，则不指定开始时间，
        如果结束年任一以为“aujourd'hui”，自动替换成当下年月
        
        检查结束年月不早于开始年月
        
        输出start_date, end_date(带时间戳)
        """
        

        # --- 强化逻辑：如果 start_year 或 start_month 任一s为 "*"，则都视为无限制 ---
        if start_year == "" or start_month == "*":
            start_year = start_month = "*"

        # --- 强化逻辑：如果 end_year 或 end_month 任一为 aujourd'hui，则都视为今天 ---
        if end_year == "aujourd'hui" or end_month == "aujourd'hui":
            end_year = end_month = "aujourd'hui"


        # --- 日期合法性检查 ---
        if isinstance(start_year, int) and isinstance(start_month, int) and \
        isinstance(end_year, int) and isinstance(end_month, int):

            # 比较年月元组（保证稳定）
            if (end_year, end_month) < (start_year, start_month):
                st.error("Période invalide : la fin est antérieure au début!")
                return []  # 返回空过滤，避免继续运行
            

        # --- 构建开始日期 --如果非数值，则表示无限制
        if isinstance(start_year, int) and isinstance(start_month, int):
            start_date = f"{start_year}-{start_month:02d}-01T00:00:00Z"
        else:
            start_date = "*"
            
        # NB. HAL 的 _tdate 字段是 Solr Date 类型:它 不接受纯 YYYY-MM-DD,必须加上时间区域T23:59:59Z
        # --- 构建结束日期 ---如果非数值，则表示截止至今天
        if isinstance(end_year, int) and isinstance(end_month, int):
            last_day = calendar.monthrange(end_year, end_month)[1]
            end_date = f"{end_year}-{end_month:02d}-{last_day:02d}T23:59:59Z"
            
        elif end_year == "aujourd'hui":# 不要用NOW，其他筛选的时候需要具体日期？
            today = datetime.utcnow()
            end_date = today.strftime("%Y-%m-%dT23:59:59Z")
            
        # --- # 理论上不会进入这里，但作为安全兜底
        else:
            today = datetime.utcnow()
            end_date = today.strftime("%Y-%m-%dT23:59:59Z")
            
        return start_date, end_date


def get_start_end_field(key_prefix):

    """
    streamlit 输入模块：获得起、止，年、月，和筛选的日期列
    
    """

    st.markdown(f"**📆 Période**.  \n")
    
    # ---start~end---
    st.markdown(f"- si vous ne voulez pas définir la date de début, choisisssez '*' dans l'année de début' *ou/et* 'mois de début';  \n"
                f"- si vous ne voulez pas définir la date de fin, choisisssez 'aujourd'hui' dans 'années de fin' *ou/et* 'mois de fin'.")
    now = datetime.now()
    current_year, current_month = now.year, now.month

    start_years = ["*"] + list(range(current_year, 1901, -1))
    start_months= ["*"] + list(range(1, 13)) 
    end_years = ["aujourd'hui"] + list(range(current_year, 1901, -1))
    end_months = ["aujourd'hui"] + list(range(1, 13))

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox("Année de début", start_years, index=start_years.index(current_year),key=f"{key_prefix}_start_year")
    with col2:
        start_month = st.selectbox("Mois de début", start_months, index=start_months.index(current_month), key=f"{key_prefix}_start_month")#JAN!
        
    col3, col4 = st.columns(2)
    with col3:
        end_year = st.selectbox("Année de fin", end_years, index=end_years.index(current_year),key=f"{key_prefix}_end_year")
    with col4:
        end_month = st.selectbox("Mois de fin", end_months, index=end_months.index("aujourd'hui"), key=f"{key_prefix}_end_month")
        
    start_date, end_date=build_period(start_year=start_year, start_month=start_month,
                        end_year=end_year, end_month=end_month)

    # ---date field---
    date_field = st.radio(
        "**Chercher les résultats selon la date de :**",
        ['soumission','modification','publication'],
        horizontal=True, 
        index=2,# default value!
        key=f"{key_prefix}_date_field",
        help="HAL cherche les articles par l'année de la publication (publicationDateY_i)."
    )
        
    # ---check---
    st.markdown(f"[check] chercher les articles pendant **{start_date} ~ {end_date}** par la date de **{date_field}**!")
    # st.markdown("<br>", unsafe_allow_html=True)

    return start_year, start_month, end_year, end_month, date_field




def complete_pub_date(df):
    """
    补全publicationDate_s为YYYY/MM/DD 格式
    
    """
    if "publicationDate_s" not in df.columns:
        # st.write("[warning] 'publicationDate_s' not in df!!!")
        return df
    else :
        df["publicationDate_s"] = df["publicationDate_s"].astype(str)

        # 年 → 补成 01-01
        df["publicationDate_s"] = df["publicationDate_s"].str.replace(
            r"^\d{4}$",
            lambda x: x.group(0) + "-01-01",
            regex=True
        )
        # 年月 → 补成 -01
        df["publicationDate_s"] = df["publicationDate_s"].str.replace(
            r"^\d{4}-\d{2}$",
            lambda x: x.group(0) + "-01",
            regex=True
        )
        # ## 统一变成时间戳格式
        # df["publicationDate_s"]=pd.to_datetime(df["publicationDate_s"], errors="coerce")
        
    return df


def filter_par_date(df, 
                    start_year, start_month, 
                    end_year, end_month, 
                    date_field_col="submittedDate_s"):
    """
    输入：起、止，年、月，筛选列
    生成带时间戳的start_date, end_date
    如果按照pub date筛选，则先清洗格式为YY/MM/DD
    
    """
    
    # --- complete---
    df=complete_pub_date(df)
    df_filtered=df.copy()
    
    # ---satrt-end---        
    start_date, end_date=build_period(start_year=start_year, start_month=start_month,
                                      end_year=end_year,end_month=end_month)
    
    # correct for pub date
    if date_field_col =="publicationDate_s":
        start_date=start_date.split('T')[0]
        end_date=end_date.split('T')[0]
    # print(f"START :{start_date}; END: {end_date}\n")
    
    
    # ---filter---
    if start_date !="*" and start_date is not None :
        df_filtered=df_filtered[df_filtered[date_field_col] >= start_date]
    if end_date is not None:
        df_filtered=df_filtered[df_filtered[date_field_col] < end_date]

    return df_filtered





##=====================================recherche des articles================================================
def fetch_hal_articles(
            # start_date=None, end_date=None,
            start_year=None, start_month=None, end_year=None, end_month=None, 
            date_field_col="publicationDate_tdate", # 默认值
            doc_types=None, auth_names_valid=None,
            
            domains=None,keywords=None, languages=None, labs=None, 
                       
            collcode=None, collname=None, authors=None, 
            
            text=None,
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
    
    fl:field list
    fq:field query
    
    wt:writer type
    
    
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
        fields=[
            'halId_s','uri_s', "docType_s", "title_s", "subTitle_s", "authFullName_s","authIdHal_s","labStructName_s",
            "domain_s","openAccess_bool",'volume_s',"page_s","classification_s",
            "submittedDate_s","modifiedDate_s", "publicationDate_s","journalTitle_s","conferenceTitle_s","conferenceOrganizer_s","conferenceStartDate_s",
            "country_s", "language_s",
            "keyword_s", "abstract_s","files_s","urlFulltextEsr_s","label_s"
        ]
        # fields = ['halId_s', "title_s", "authFullName_s", "publicationDate_s",
        #           "labStructName_s", "keyword_s", "abstract_s", "urlFulltextEsr_s"]
    


    # -------------构建搜索条件v2 11/10/25--------------------
    fq = []
    if doc_types:
        input = [f'"{t}"' for t in doc_types]
        fq.append(f'docType_s:({" OR ".join(input)})')

    if labs:
        input = [f'"{t}"' for t in labs]
        fq.append(f'labStructName_s:({" OR ".join(input)})')
    
    
    if auth_names_valid:
        input = [f'"{t}"' for t in auth_names_valid]
        fq.append(f'authFullName_s:({" OR ".join(input)})')
    
    if collcode:
        input = [f'"{t}"' for t in collcode]
        fq.append(f'collCode_s:({" OR ".join(input)})')
    
    if collname:
        input = [f'"{t}"' for t in collname]
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

    #-------------------------------------period------------------------------------------    
    if start_year and start_month and end_year and end_month:
        start_date, end_date=build_period(start_year, start_month,end_year, end_month)
        fq.append(f"{date_field_col}:[{start_date} TO {end_date}]")
        start_date_s=start_date if start_date!="*" else 'BEFORE'
        st.write(f"[INFO] Période de recherche selon '{date_field_col}' : \n {start_date_s} ~ {end_date}  \n")


    # 8. 自由文本（全文搜索）
    # q = " AND ".join(text) if text else "*:*"
    q="*:*"
    
    """
    start-end:2026-01-01-NOW
    QUERY URL : https://api.archives-ouvertes.fr/search/?q=%2A%3A%2A&
    fl=halId_s%2Curi_s%2CdocType_s%2Ctitle_s%2CsubTitle_s%2CauthFullName_s%2CauthIdHal_s%2ClabStructName_s%2Cdomain_s%2CopenAccess_bool%2Cvolume_s%2Cpage_s%2Cclassification_s%2CsubmittedDate_s%2CmodifiedDate_s%2CpublicationDate_s%2CjournalTitle_s%2CconferenceTitle_s%2CconferenceOrganizer_s%2CconferenceStartDate_s%2Ccountry_s%2Clanguage_s%2Ckeyword_s%2Cabstract_s%2Cfiles_s%2CurlFulltextEsr_s&rows=100&wt=json&start=0&sort=submittedDate_tdate+desc&
    fq=docType=submittedDate_tdate%3A%5B2026-01-01+TO+NOW%5D

    """


    # ========= 请求循环 =========
    all_docs = []#储存所有结果

    start = 0#从第几条开始抓取，一次抓取rows条，忽略抓取过的
    total_found = None

    while True:
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
        print(f'QUERY URL : {full_url} \n')
        
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
    idx=df.columns.get_loc("classification_s")
    axe_values=[extract_irg_axes(axe) for axe in df['classification_s']]
    df.insert(loc=idx+1, column=axe_name, value=axe_values)

    # df[axe_name]=df["classification_s"].apply(extract_irg_axes)
    
    # df["classification_s"] = df["classification_s"].apply(extract_irg_axes)
    # df=df.rename(columns={"classification_s":axe_name})

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
# 字符串归一化?
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
def fuzzy_lookup(journal_name: str, mapping: dict, cutoff: int = 90) -> str:
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





def nearest_fnege_year(pub_year_raw):
    # FNEGE_YEARS = [2011, 2013, 2016, 2019, 2022, 2025]
    
    FNEGE_YEARS = [2011] + list(range(2013, 3000, 3))#range(start, stop, step)
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


def fuzzy_lookup_with_name(query, mapping, cutoff=80):
    from fuzzywuzzy import process
    choices = list(mapping.keys())
    best_match, score = process.extractOne(query, choices)
    if score >= cutoff:
        return mapping[best_match], best_match
    return None, None




def add_classement_fnege(
    df: pd.DataFrame,
    fnege_map: pd.DataFrame,
    journal_col: str = "journalTitle_s",
    year_col: str = "publicationDate_s",
    fnege_col_name: str = 'cl_fnege',
    cutoff: int = 90, 
    active_fuzzylookup=False
) -> pd.DataFrame:

    # 构建 lookup mapping
    fnege_mapping = {r['journal_hal']: r.to_dict() for _, r in fnege_map.iterrows()}

    # 获取年份
    df["fnege_year"]= df[year_col].apply(nearest_fnege_year)
    
    classement_list = []
    for _, row in df.iterrows():
        journal_val = row.get(journal_col, "")
        fnege_year = row['fnege_year']
        rang_value = None #init
        
        # 若有期刊
        if pd.notna(journal_val) and str(journal_val).strip():

            # 总是先精确匹配
            matched_row = fnege_mapping.get(journal_val, None)
            if matched_row and fnege_year:
                rang_col = f"rang_{fnege_year}"
                rang_value = matched_row.get(rang_col, None)#int
            
            # 没有正确，有fnege year（pubdate），且开启模糊搜索
            if not matched_row and fnege_year and active_fuzzylookup:
                fuzzy_row, fuzzy_name = fuzzy_lookup_with_name(journal_val, fnege_mapping, cutoff=cutoff)
                
                if fuzzy_row: # 模糊搜索有匹配的journal_hal,通过其同上获得fnege
                    rang_col = f"rang_{fnege_year}"
                    rang_val = fuzzy_row.get(rang_col, None) # np.nan是float类型!=None
                    
                    if pd.notna(rang_val): # 
                        rang_value = f"{rang_val}_nom-journal-uncertain_{fuzzy_name}"
                    else :# 模糊搜索有名字匹配，但还是没有对应的rang
                        rang_value=None
                        
        classement_list.append(rang_value)
    
    # ADD
    idx = df.columns.get_loc(journal_col)
    df.insert(loc=idx + 1, column=fnege_col_name, value=classement_list)

    return df



##==========================================authPrimaryStructureIdName_s==================================================
##==========================================   ==================================================
import urllib.parse
import requests


def search_authIdHasPrimaryStructure_fs_by_authFullName_s(list_fullnames):
        
    BASE_URL = "https://api.archives-ouvertes.fr/search/"
    params = [
            ('q', "*:*"),           
            ("rows", 0),
            ("wt", "json"),
            ("facet","True"),
            ('facet.mincount',1),
        ]
    
    if list_fullnames:
        input = [f'"{t}"' for t in list_fullnames]
        # print(f'authFullName_s:({" OR ".join(input)})')
        params.append(('fq',f'authFullName_s:({" OR ".join(input)})'))
    

    # ---facet---
    facet_list=['authIdHasPrimaryStructure_fs']

    for f in facet_list:
        facet_query=('facet.field', f)
        params.append(facet_query)
        
    # check url：
    query_string = urllib.parse.urlencode(params, doseq=True)
    full_url = BASE_URL + "?" + query_string
    # print(f'[authFullName_s] QUERY URL : {full_url} \n')

    # parse
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()  # 检查HTTP状态码
    data = resp.json()
    # print(data)
    return data



def trim_authIdHasPrimaryStructure_data(data):
    data_auth_struct=data["facet_counts"]['facet_fields']['authIdHasPrimaryStructure_fs']
    
    map_auth_struct={}
    i= 0
    for auth_struct in data_auth_struct:
        if type(auth_struct)!=int:
            els=auth_struct.split("_")
            
            # ---extract info---
            authFullname_s=els[2]
            authIdHal_s=authFullname_s.lower().replace(" ", "-")
            authIdHal_i=els[0].split('-')[1]        
            labStructName_s=els[-1]
            labStructId_i=els[4]
            
            # ---organise info---
            info = {
                # "authFullname_s": authFullname_s,
                "authIdHal_s": authIdHal_s,
                "authIdHal_i": authIdHal_i,
                "labStructName_s": labStructName_s,
                "labStructId_i": labStructId_i
            }
            if authFullname_s not in map_auth_struct:
                map_auth_struct[authFullname_s] = []
            map_auth_struct[authFullname_s].append(info)
            i+=1
    # print(f"[DONE] {i} new info mapped!")
    return map_auth_struct



import json
import pandas as pd

def update_map_auth_struct(map_auth_struct, list_new_fullnames,
                           path_map_auth_struct='../external_data/auth_struct_map.json'
    ):
    if list_new_fullnames==[]:
        st.write(' No updates in map_auth_struct!')
        return map_auth_struct
    
    new_map_auth_struct=map_auth_struct.copy()
    # search
    data=search_authIdHasPrimaryStructure_fs_by_authFullName_s(list_fullnames=list_new_fullnames)

    # trim
    updates_auth_struct=trim_authIdHasPrimaryStructure_data(data)

    # update
    map_auth_struct.update(updates_auth_struct)

    # save
    with open(path_map_auth_struct, 'w', encoding='utf-8')as f:
        json.dump(map_auth_struct, f, indent=2, ensure_ascii=False)
        st.write(f'map_auth_struct updated and saved in {path_map_auth_struct}!')

    # stat
    print(f"old map_auth_struct: {len(map_auth_struct)}; new:{len(new_map_auth_struct)}")
    
    return new_map_auth_struct


#------------------------------------------------------------------------------------------------------------------------


def map_auth_struct_per_row(authFullName_s, map_auth_struct):
    list_authFullName_s=authFullName_s.split(';')
    
    list_authPrimaryStructureIdName=[]    
    
    for name in list_authFullName_s:#不止一个名字
        info_auth=map_auth_struct.get(name.strip(),[]) 
          
        if info_auth:#一个名字不止一个主要机构
            for dict_info in info_auth:                 
                list_authPrimaryStructureIdName.append(f"{name}_{dict_info.get('labStructId_i','xxx')}_{dict_info.get('labStructName_s','xxx')}")

    authPrimaryStructureIdName_s="; ".join(list_authPrimaryStructureIdName)
    # print(authPrimaryStructureIdName_s)
    
    return authPrimaryStructureIdName_s


def add_authPrimaryStructureIdName_s(df_input, map_auth_struct):
    df=df_input.copy()
    
    # ---list_new_fullnames---
    list_fullnames = []
    for name_str in df['authFullName_s']:
        list_fullnames.extend(name.strip() for name in name_str.split(';'))
        list_new_fullnames=[n for n in list_fullnames if n not in list(map_auth_struct.keys())]
    
    # ---update map_auth_struct---
    new_map_auth_struct=update_map_auth_struct(map_auth_struct, list_new_fullnames=list_new_fullnames,
                        path_map_auth_struct='../external_data/auth_struct_map.json'
    )
    
    # ---map ---   
    values=df['authFullName_s'].apply(lambda x : map_auth_struct_per_row(x, new_map_auth_struct))
    if "authPrimaryStructureIdName_s" in df.columns:
        df["authPrimaryStructureIdName_s"]=values
    else :
        idx_authFullName=df.columns.get_loc("authFullName_s")
        df.insert(loc=idx_authFullName+1, column="authPrimaryStructureIdName_s", value=values)
    
    return df


def check_irgStructureID(df, list_structureid=["1004418","57129"]):
    values=df['authPrimaryStructureIdName_s'].apply(lambda x : any(id_ in x for id_ in list_structureid))
   
    
    if "authPrimaryStructure_hasIRG_bool" in df.columns:
        df["authPrimaryStructure_hasIRG_bool"]=values
    else :
        idx_authprimarystructure=df.columns.get_loc("authPrimaryStructureIdName_s")
        df.insert(loc=idx_authprimarystructure+1, column="authPrimaryStructure_hasIRG_bool", value=values)

    return df




# #===========================================PRIMARYSTRUCTURE===========================================================#

# import urllib.parse
# import requests
# import time
# import numpy as np
# from tqdm import tqdm
# import os
# import json

# # def check_primarystructure_map()
# def save_as_json(data, file_path="../external_data/author_primarystructure_s_map.json"):
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#     with open (file_path, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)
#     # st.markdown(f'[SAVE] Les données sauvegardées / mises à jour :\n{file_path}!')
#     # &nbsp; == a no breaking space
#     return 

# def read_json(file_path='../external_data/author_primarystructure_s_map.json'):
#     with open (file_path, 'r', encoding="utf-8") as f:
#         data=json.load(f)
#     return data

# def get_author_primarystructure(names: list, author_primarystructure_s_map:dict=None):
#     """
#     查询作者主要所属机构（Primary Structure），返回一个 dict 映射。
#     使用 tqdm 显示查询进度。
#     可能有作者在HAL没有HalId，所以通过fullname查询更加保险？
#     """
    
#     if author_primarystructure_s_map == None:
#         author_primarystructure_s_map={}

#     BASE_URL = "https://api.archives-ouvertes.fr/search/"
#     # for name in tqdm(names, desc="🔍 chercher la structure primaire de l'auteurs:", ncols=100):
#     for i, name in enumerate (names):#如果改变value，应该删除json，不然查询到已经存在的名字，不会再重新搜索!
#         if name not in author_primarystructure_s_map.keys():
#             try:
#                 params = [
#                     ("fq", f'authFullName_s:"{name}"'),
#                     ("fl", "authIdHasPrimaryStructure_fs"),
#                     ("rows", 1),
#                     ("wt", "json")
#                 ]
#                 # #检查生成的url：
#                 query_string = urllib.parse.urlencode(params, doseq=True)
#                 full_url = BASE_URL + "?" + query_string
#                 # st.write(f'QUERY URL : {full_url} \n')

#                 resp = requests.get(BASE_URL, params=params, timeout=15)
#                 resp.raise_for_status()  # 检查HTTP状态码
#                 data = resp.json()
#                 # print(data)
                
#                 #提取：
#                 #ex.{'response': {'numFound': 79, 'start': 0, 'maxScore': 1.0, 'numFoundExact': True, 'docs': [{'authIdHasPrimaryStructure_fs': ['1271130-1099011_FacetSep_Ziad Malas_JoinSep_1151738_FacetSep_Laboratoire de Gestion et des Transitions Organisationnelles', '1271130-1099011_FacetSep_Ziad Malas_JoinSep_301366_FacetSep_Institut Universitaire de Technologie - Paul Sabatier', "12474-177028_FacetSep_Samuel Guillemot_JoinSep_489734_FacetSep_Laboratoire d'Economie et de Gestion de l'Ouest", '21015-5244_FacetSep_Andréa Gourmelen_JoinSep_117385_FacetSep_Montpellier Research in Management']}]}}

#                 # Identifiant interne + _FacetSep_ + Nom complet + _JoinSep_ + Identifiant HAL de structure primaire + _FacetSep_ + Nom de la structure primaire
#                 #ex. ['3657528-1564101_FacetSep_Adel Horrig_JoinSep_1004418_FacetSep_Institut de Recherche en Gestion']
                
#                 docs = data.get("response", {}).get("docs", [])
#                 if not docs:
#                     continue

#                 records = docs[0]["authIdHasPrimaryStructure_fs"]
#                 # print(records)# liste de structure >=1
               
#                 target_records = [r for r in records if f"_FacetSep_{name}_" in r][0]#理论上<=0

#                 if target_records:
#                     parts = target_records.split("_")
#                     structure_id= parts[-3] if parts else None #1004418 ou 57129 
#                     structure_s = parts[-1] if parts else None
#                     id_structure=str(structure_id)+"_"+str(structure_s)
#                 # else :
#                 # 会转到except中

#                 #记录：
#                 author_primarystructure_s_map[name] = id_structure


#             except Exception as e:
#                 # st.warning (f"ERROR in get_author_primarystructure: \n {e}")
#                 author_primarystructure_s_map[name] = "no primary structure found"
#                 continue

#     return author_primarystructure_s_map



# def update_author_primarystructure_s(names:list, file_path='../external_data/author_primarystructure_s_map.json'):
#     #读取已存在的author_primarystructure_s_map，如果authFullName_s不存在则搜索，然后更新至map
#     try :
#         if os.path.exists(file_path):
#             author_primarystructure_s_map=read_json(file_path)
#         else :
#             author_primarystructure_s_map={}
#         updated_author_primarystructure_s_map=get_author_primarystructure(names, author_primarystructure_s_map)
#         save_as_json(updated_author_primarystructure_s_map, file_path)
#     except Exception as e:
#         st.warning (f"ERROR in update_author_primarystructure_s: \n {e}")
    
#     return updated_author_primarystructure_s_map



# def add_primarystructure(df, author_primarystructure_s_map):
#     #读取map中author对应的id_structure str
#     # 把author_primarystructure添加到lab后的一列，命名为author_primarystructure_s
#     # primarystructures=df['authFullName_s'].apply(lambda x: ";".join([author_primarystructure_s_map.get(a, np.nan) 
#     #                                                     for a in x.split(";")]) if isinstance(x, str) else np.nan)
    
#     primarystructures=df['authFullName_s'].apply(lambda x: ";".join([str(author_primarystructure_s_map.get(a.strip(), "mapping_error"))
#                                                     for a in x.split(";") if a.strip()]
#                                                 ) if isinstance(x, str) else "fullname_not_strs")
        
#     idx = df.columns.get_loc('labStructName_s')
#     df.insert(loc=idx+1, column='author_primarystructure_s', value=primarystructures)
#     return df






#===========================================FILTRAGE BY PUBLICATION DATE=======================================================#

# def filter_by_publicationdate(df_input, start_year, start_month, end_year, end_month,
#                                date_col="publicationDate_s", filter_pubdate_by="année"):
#     if filter_pubdate_by==None:
#         return df_input
    
#     df=df_input.copy()# df==df_filtered
#     #确保df中的日期列+输入的起止年份为日期格式：
#     df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
#     print(f'df BEFORE filtrage selon date de publication:{len(df)}')
    
#     if filter_pubdate_by=="année et mois":
#         start_date, end_date=build_period(start_year, start_month,end_year, end_month)
        
#         # utc=True!! 会把时间转换为 UTC 时区, 返回的是 带 tzinfo 的 datetime
#         if start_date!="*" and start_date is not None:
#             start_date = pd.to_datetime(start_date, utc=True) if start_date else None
#             df = df[df[date_col] >= start_date]

#         end_date = pd.to_datetime(end_date, utc=True) if end_date else None
#         if end_date is not None:
#             df = df[df[date_col] <= end_date]
    
    
    
#     elif filter_pubdate_by == "année":
#         # 将列转换为 datetime
#         data_col_t=date_col.replace("_s",'_t')# add "publicationDate_t"
#         df[data_col_t] = pd.to_datetime(df[date_col], errors="coerce")

#         # 提取年份
#         df["pub_year"] = df[date_col].dt.year
#         df['pub_year']=pd.to_numeric(df['pub_year'], errors='coerce').astype('Int64')
        
#         # 根据年份筛选
#         if start_year is not None and start_year!="*":# 避免不指定start_yr的情况
#             df = df[df["pub_year"] >= int(start_year)]
#         if end_year is not None:
#             df = df[df["pub_year"] <= int(end_year)]
       
#     print(f'AFTER:{len(df)}')

#     return df
 

## =================================filtrer par date =====================================


##集合处理：
def process_df(df, DOMAIN_MAP, 
               FNEGE_MAP, cutoff, active_fuzzylookup,
            #  start_year, start_month, end_year, end_month, filter_pubdate_by
               AUTH_STRUCT_MAP
               ):
    
    """
    todo：增加methodologie！

    """
    # -----------处理 domain----------------
    if "domain_s" in df.columns:   
        df["domain_s"] = df["domain_s"].apply(lambda x : map_domains(x, map=DOMAIN_MAP))
    st.write(f"✔ Domaines mappés!")
    # st.markdown("<br>", unsafe_allow_html=True)

    #----------处理axe----------------------
    if "classification_s" in df.columns:
        df=clean_axe_from_classification(df)
    st.write(f"✔ Axes nettoyés!")
    missing_data_warning(df, col='axe', show_distribution=True)
    st.markdown("<br>", unsafe_allow_html=True)


    #--------- 处理fnege----------------
    if "journalTitle_s" in df.columns and "publicationDate_s" in df.columns :       
        #先精确，再模糊
        df=add_classement_fnege(
            df=df,
            fnege_map=FNEGE_MAP,
            journal_col = "journalTitle_s",
            year_col = "publicationDate_s",
            fnege_col_name='cl_fnege',
            cutoff= cutoff, 
            active_fuzzylookup=active_fuzzylookup
        )
        st.write(f"✔ Classements FNEGE selon la date de publication mappés dans la colonne 'cl_fnege'!")
        missing_data_warning(df, col="journalTitle_s", show_distribution=False)
        missing_data_warning(df, col='cl_fnege', show_distribution=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------authPrimaryStructureIdName_s+authPrimaryStructure_IRG_bool----------------------
    if "authFullName_s" in df.columns and AUTH_STRUCT_MAP :  
        st.write(f"✔ Structures primaires des auteurs mappées!")
        
        df=add_authPrimaryStructureIdName_s(df, map_auth_struct=AUTH_STRUCT_MAP)
        df=check_irgStructureID(df,list_structureid=["1004418","57129"])


    
    # #----------处理author_primarystructure-----------
    # # st.write(os.getcwd())
    # with st.spinner("Chercher la structure primaire de l'auteur selon le nom complet de l'auteur..."):
    #     author_col='authFullName_s'
    #     names = set([
    #         n.strip()
    #         for _, r in df.iterrows()
    #         if isinstance(r[author_col], str)
    #         for n in r[author_col].split(';')
    #         if n.strip()
    #     ])
    #     author_primarystructure_s_map=update_author_primarystructure_s(names, file_path='external_data/author_primarystructure_s_map.json')
    #     df= add_primarystructure(df, author_primarystructure_s_map)#map
    #     st.write(f"✔ Structures primaires mappées!")
    #     missing_data_warning(df, col="author_primarystructure_s", show_distribution=False)#check   
    # st.markdown("<br>", unsafe_allow_html=True)


    # st.write("DF avant filtrage!")
    # st.dataframe(df)

    # #----------按照publicationDate_s筛选-----------------
    # # # keys 与radio输入保持一致！
    # df_filtered=filter_by_publicationdate(df_input=df, start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month,
    #                                     filter_pubdate_by=filter_pubdate_by)
    
    # if filter_pubdate_by=="année":
    #     period_str=f"{start_year}~{end_year}" 
    #     st.markdown(f"✔ Résultat filtré selon **{filter_pubdate_by}** de la data de publication : **{period_str}**")

    # elif filter_pubdate_by=="année et mois":
    #     if end_year !="aujourd'hui" and end_month!="aujourd'hui":#有一个是ajd就会被同化          
    #        period_str= f"{start_year}/{start_month}~{end_year}/{end_month}"           
    #     else:
    #         today=datetime.today().strftime("%Y/%m")
    #         period_str= f"{start_year}/{start_month}~{today}"
    
    #     st.markdown(f"✔ Résultat filtré selon **{filter_pubdate_by}** de la data de publication : **{period_str}**")
    # # else: filter_pubdate_by==None=> no filter
    # st.markdown("<br>", unsafe_allow_html=True)
    
    #----------references from 'label_s'-----------------
    df.rename(columns={"label_s":"ref_hal"},inplace=True)   
    df=generate_ref_apa(df)
    
    st.markdown(f"✔ Bibliographie disponible dans les colonnes 'ref_hal' et 'ref_apa'! Decendez pour la télécharger!")
     
    return df






#======================================references===================================================#
def generate_ref_apa(df):
    import re
    apa_list = []
    for entry in df["ref_hal"].dropna():
        parts = entry.split(". ")
        authors = parts[0]
        title = parts[1]
        conference_info = parts[2] if len(parts) > 2 else ""

        # 作者格式化
        author_list = authors.split(", ")
        apa_authors = []
        for author in author_list:
            names = author.split(" ")
            last = names[-1]
            initials = " ".join([n[0] + "." for n in names[:-1]])
            apa_authors.append(f"{last}, {initials}")
        apa_authors_str = ", ".join(apa_authors)

        # 提取年份
        year_match = re.search(r"\b(20\d{2})\b", conference_info)
        year = year_match.group(1) if year_match else "n.d."

        # APA 文献
        apa_entry = f"{apa_authors_str} ({year}). {title}. In {conference_info}."
        apa_list.append(apa_entry)
        
    idx=df.columns.get_loc("ref_hal")
    df.insert(loc=idx+1, column="ref_apa", value=apa_list)
     
    # df["APA"] = apa_list
    return df


def preview_and_download_references(df):
    """
    在 Streamlit 中预览和下载参考文献。
    支持选择 HAL 原始格式或 APA 格式。
    自动编号和按字母排序。
    """
    if df is None or df.empty:
        st.warning("df vide !")
        return
    
    if "ref_hal" not in df.columns:
        st.warning("Colonne 'ref_hal' introuvable")
        return
    
    st.markdown("### 📚Bibliographie ###") 

    # ------- 用户选择 APA 格式 -------
    use_apa = st.selectbox(
        "Format de citation :",
        options=["HAL original", "APA format"]
    )

    # ------- 选择显示的列 -------
    if use_apa == "APA format":
        if "ref_apa" not in df.columns:
            df = generate_ref_apa(df) # just check
        refs_list = df["ref_apa"].dropna().astype(str).tolist()
    else:
        refs_list = df["ref_hal"].dropna().astype(str).tolist()

    # ------- 按第一个作者字母排序 -------
    refs_list = sorted(refs_list, key=lambda x: x.split(",")[0].strip())
    
   
    # ------- 自动编号 -------
    # txt_string = "\n\n".join([f"{ref}" for i, ref in enumerate(refs_list)])
    txt_string = "\n\n".join([f"[{i+1}] {ref}" for i, ref in enumerate(refs_list)])

    #--------rtf format------
    # {\rtf1 → RTF 文件头
    # \par → 换行
    # \b → 加粗
    
    rtf_string = r"{\rtf1\ansi\deff0" + "\n"
    for i, ref in enumerate(refs_list):
        rtf_string += f"{ref}\\par"
    rtf_string += "}"


    # ------- 预览区域 -------
    # st.markdown("### 📚 Preview References")
    st.text_area("Aperçu (format TXT)", value=txt_string, height=300)
    st.markdown(f"ps. La bibliographie est numérotée et triée par ordre alphabétique!  \n")
    
    # ------- 下载区域 -------
    col1, col2, col3 = st.columns([3,1,1])

    with col1:
        file_name = st.text_input(
            f"📥 Télécharger la bibliographie :",
            value=f"references_{use_apa.split()[0]}",
            key="ref"# ref_filename
        )

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="as TXT",
            data=txt_string.encode("utf-8-sig"),
            file_name=file_name + ".txt",
            mime="text/plain",
            key='download_ref_txt'
        )
        
        
        
