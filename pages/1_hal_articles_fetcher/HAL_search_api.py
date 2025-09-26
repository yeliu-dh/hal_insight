# hal_fetch.py


def fetch_hal_articles(start_year=None, start_month=None, end_year=None, end_month=None,
                       doc_types=None, domains=None,keywords=None, languages=None,labs=None, authors=None, text=None,
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
    

    # 构建过滤条件
    fq = []
    if doc_types:
        fq.append("(" + " OR ".join([f'docType_s:"{t}"' for t in doc_types]) + ")") 
        #formule：(docType_s:"ART" OR docType_s:"COMM")
    if domains:
        fq.append("(" + " OR ".join([f'domain_s:"{t}"' for t in domains]) + ")") 

    if keywords:
        fq.append("(" + " OR ".join([f'keyword_s:"{t}"' for t in keywords]) + ")") 
    

    if languages:
        fq.append("(" + " OR ".join([f'language_s:"{t}"' for t in languages]) + ")") 

    if labs:
        fq.append("(" + " OR ".join([f'labStructName_s:"{lab}"' for lab in labs]) + ")")

    if start_year is not None and start_month is not None:
        start_date = f"{start_year}-{start_month:02d}-01T00:00:00Z"
    else:
        start_date = None
    
    end_day = calendar.monthrange(end_year, end_month)[1]#按月份决定最后一天是29/30/31
    end_date = f"{end_year}-{end_month:02d}-{end_day:02d}T23:59:59Z"
    
    if start_date:
        fq.append(f'publicationDate_s:[{start_date} TO {end_date}]')
        # print(f"PERIODE : {start_date} TO {end_date}")

    else:
        fq.append(f'publicationDate_s:[* TO {end_date}]')  # * 表示不限下限

    if text:
        q = " AND ".join(text)  # 所有关键词都必须出现
    else:
    
        q="*:*"


    # CHECK: 
    #输入筛选条件
    params = {
        "q": q,
        "fq": fq,
        "fl": ",".join(fields),
        "rows": rows,
        "wt": "json"
    }   

    # 构建 URL 用于打印检查
    query_string = urllib.parse.urlencode(params, doseq=True)
    full_url = BASE_URL + "?" + query_string
    print(f'QUERY URL : {full_url} \n')


    # ========= 请求循环 =========
    all_docs = []#储存所有结果

    start = 0#从第几条开始抓取，一次抓取rows条，忽略抓取过的
    total_found = None

    while True:
        params = {
            "q": q,
            "fq": fq,
            "fl": ",".join(fields),
            "rows": rows,
            "start": start,
            "wt": "json"
        }

        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

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

    df = pd.DataFrame(info)
    df=df.drop_duplicates(subset='halId_s')


    if 'publicationDate_s' in df.columns:
        df['publicationDate_s'] = pd.to_datetime(df['publicationDate_s'], errors='coerce')
        df = df.sort_values(by='publicationDate_s', ascending=False)
    
    return df







